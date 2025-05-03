import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import uuid
from dotenv import load_dotenv
import os
import json
from azure.data.tables import TableServiceClient, TableEntity

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# ------------------------------
# Job Class
# ------------------------------
class Job:
    def __init__(self, title, description, place, job_type,apply_link):
        self.id = str(uuid.uuid4())
        self.title = title
        self.description = description
        self.place = place
        self.job_type = job_type
        self.apply_link = apply_link

# ------------------------------
# Scraper Class
# ------------------------------
class CorazorJobs:
    def __init__(self, base_url):
        self.base_url = base_url

    def fetch_jobs(self):
        response = requests.get(self.base_url)
        if response.status_code != 200:
            print("❌ Failed to retrieve page.")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        html_content = str(soup)

        query = f"""
        Get all the job details from this HTML content:
        {html_content}

        Extract:
        - Job_Title
        - Job_Description
        - Job_Place
        - Job_Type

        Output strictly in JSON list format like:
        [
            {{
                "Job_Title": "Software Engineer",
                "Job_Description": "We are hiring...",
                "Job_Place": "Remote",
                "Job_Type": "Full-Time",
                "Job_Apply_Link": "https://example.com/apply"
            }}
        ]
        """

        try:
            gemini_response = model.generate_content(query)
            cleaned = gemini_response.text.replace("```json", "").replace("```", "")
            jobs_raw = json.loads(cleaned)

            jobs = []
            for i,item in enumerate(jobs_raw):
                job = Job(
                    title=item.get("Job_Title", ""),
                    description=item.get("Job_Description", ""),
                    place=item.get("Job_Place", ""),
                    job_type=item.get("Job_Type", ""),
                    apply_link= f"https://corazor-technology.vercel.app/careers/apply/{i+1}"
                )
                jobs.append(job)

            return jobs

        except Exception as e:
            print(f"❌ Error parsing Gemini output: {e}")
            return []

# ------------------------------
# Azure Table Storage Handler
# ------------------------------
class AzureTableStorage:
    def __init__(self, connection_string, table_name):
        self.connection_string = connection_string
        self.table_name = table_name
        self.service_client = TableServiceClient.from_connection_string(self.connection_string)
        self.table_client = self.create_table_if_not_exists()

    def create_table_if_not_exists(self):
        try:
            self.service_client.create_table_if_not_exists(self.table_name)
            return self.service_client.get_table_client(self.table_name)
        except Exception as e:
            print(f"❌ Error creating table: {e}")
            return None

    def delete_entities_in_batches(self, partition_key="CorazorCareer", batch_size=100):
        entities = list(self.table_client.query_entities(query_filter=f"PartitionKey eq '{partition_key}'"))

        if not entities:
            print(f"No entities found with PartitionKey '{partition_key}'.")
            return

        for i in range(0, len(entities), batch_size):
            chunk = entities[i:i + batch_size]
            for entity in chunk:
                try:
                    self.table_client.delete_entity(row_key=entity['RowKey'], partition_key=entity['PartitionKey'])
                except Exception as e:
                    print(f"❌ Failed to delete {entity['RowKey']}: {e}")
            print(f"✅ Deleted batch of {len(chunk)} entities.")

        print(f"✅ Finished deleting all entities with PartitionKey '{partition_key}'.")

    def store_job(self, job):
        if not self.table_client:
            print("❌ Table client not initialized.")
            return

        job_entity = TableEntity()
        job_entity['PartitionKey'] = 'CorazorCareer'
        job_entity['RowKey'] = job.id
        job_entity['JobName'] = job.title
        job_entity['JobDescription'] = f"{job.description}\n\nPlace: {job.place}\nType: {job.job_type}"
        job_entity['URL'] = job.apply_link

        try:
            self.table_client.upsert_entity(job_entity)
            print(f"✅ Stored job: {job.title}")
        except Exception as e:
            print(f"❌ Error storing job: {e}")

# ------------------------------
# Usage
# ------------------------------
if __name__ == "__main__":
    # Fetch jobs
    corazorjobs = CorazorJobs("https://corazor-technology.vercel.app/careers")
    job_data = corazorjobs.fetch_jobs()

    if job_data:
        print(f"Fetched {len(job_data)} jobs.")
        print(vars(job_data[0]))  # Print first job for verification

        # Store in Azure
        connection_string = "DefaultEndpointsProtocol=https;AccountName=jobsdetails;AccountKey=hyv15hGwCxlf8e2NcI3YJ9FtD+EtCAp9W0pdtPBh3HhKICYemrgrZwRSbhXEkthCHj57rddFLkPs+ASt+Cf+Mw==;EndpointSuffix=core.windows.net"
        table_name = "CorazorJobDetails"
        azure_storage = AzureTableStorage(connection_string, table_name)

        # Optional: Delete old jobs
        azure_storage.delete_entities_in_batches(partition_key="CorazorCareer")

        for job in job_data:
            azure_storage.store_job(job)
    else:
        print("No job data extracted.")
