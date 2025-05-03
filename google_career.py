from azure.data.tables import TableServiceClient, TableEntity
from bs4 import BeautifulSoup
import requests
import uuid
from urllib.parse import urljoin
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import ssl
import undetected_chromedriver as uc
ssl._create_default_https_context = ssl._create_stdlib_context

options = uc.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
# Step 1: Define JobScraper class
class JobScraper:
    def __init__(self, base_url):
        self.base_url = base_url

    def fetch_job_data(self):
        page = 1
        all_jobs = []

        while True:
            url = f"{self.base_url}&page={page}"
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Failed to retrieve page {page}")
                break

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract job titles and links
            job_elements = soup.find_all('a', {'class': 'WpHeLc VfPpkd-mRLv6 VfPpkd-RLmnJb'})
            titles = soup.find_all('h3', {'class': 'QJPWVe'})

            # If no jobs are found, stop the loop
            if len(job_elements) == 0:
                print(f"No jobs found on page {page}. Stopping.")
                break

            for job_element, title_element in zip(job_elements, titles):
                job_href = job_element.get('href')
                if job_href:
                    job_link = urljoin("https://careers.google.com", job_href)
                    job_title = title_element.text.strip()

                    # Fetch job description and apply link by visiting the job detail page
                    job_description, apply_link = self.fetch_job_details(job_link)
                    
                    # Create a Job object
                    job = Job(title=job_title, description=job_description, apply_link=apply_link)
                    all_jobs.append(job)
                    print(f"Fetched job: {job_title}")
                    print(f"Fetch job link:{apply_link}")

            print(f"Page Number: {page}, Jobs Found: {len(job_elements)}")
            page += 1

        return all_jobs

    def fetch_job_details(self, job_url):
        response = requests.get(job_url)
        if response.status_code != 200:
            print(f"Failed to retrieve job details from {job_url}")
            return "", ""

        soup = BeautifulSoup(response.text, 'html.parser')

        # Fetch job description
        try:
            qualification = soup.find("div", class_="KwJkGe")
            about_job = soup.find("div", class_="aG5W3")
            responsibilities = soup.find("div", class_="BDNOWe")
            sections = [section.get_text(strip=True) for section in [qualification, about_job, responsibilities] if section]
            job_description = "\n".join(sections)
        except Exception as e:
            print(f"Error fetching job description: {e}")
            job_description = ""

        # Fetch apply link by navigating within the job detail page
        try:
            apply_button = soup.find("a", {"aria-label": "Apply"})
            if apply_button:
                apply_href = apply_button.get('href')
                apply_link = urljoin("https://careers.google.com", apply_href)
            else:
                apply_link = ""
        except Exception as e:
            print(f"Error fetching apply link: {e}")
            apply_link = ""

        return job_description, apply_link

# Step 2: Define Job class to hold job data
class Job:
    def __init__(self, title, description, apply_link):
        self.title = title
        self.description = description
        self.apply_link = apply_link
        self.id = str(uuid.uuid4())

    def __repr__(self):
        return f"Job(title={self.title!r}, description={self.description[:50]!r}..., apply_link={self.apply_link!r})"

# Step 3: Define AzureTableStorage class to store job data
class AzureTableStorage:
    def __init__(self, connection_string, table_name):
        self.connection_string = connection_string
        self.table_name = table_name
        self.service_client = TableServiceClient.from_connection_string(conn_str=self.connection_string)
        self.table_client = self.create_table_if_not_exists()

    def create_table_if_not_exists(self):
        try:
            self.service_client.create_table_if_not_exists(table_name=self.table_name)
            return self.service_client.get_table_client(self.table_name)
        except Exception as e:
            print(f"Error creating table: {e}")
            return None
    def delete_entities_in_batches(self, partition_key="GoogleCareersJobs", batch_size=100):
        """
        Deletes all entities with the specified partition key in batches.

        Args:
            partition_key (str, optional): The partition key of the entities to delete. Defaults to "GlassDoorJobs".
            batch_size (int, optional): The number of entities to delete in each batch. Defaults to 100.
        """
        
        # Retrieve all entities with the specified partition key
        entities = list(self.table_client.query_entities(query_filter=f"PartitionKey eq '{partition_key}'"))

        if not entities:
            print(f"No entities found with PartitionKey '{partition_key}'.")
            return

        for i in range(0, len(entities), batch_size):
            chunk = entities[i:i + batch_size]  # Get a batch of entities
            for entity in chunk:
                try:
                    print(f"Adding delete operation for: {entity['PartitionKey']}, {entity['RowKey']}")
                    self.table_client.delete_entity(row_key=entity['RowKey'], partition_key=entity['PartitionKey'])
                            #operations.append(("delete", entity))  # Add delete operation to batch
                except Exception as e:
                            print(f"Error preparing delete operation for entity {entity['PartitionKey']}, {entity['RowKey']}: {e}")
            try:
                print(f"Successfully deleted batch of {len(chunk)} entities.")
            except Exception as e:
                print(f"Error committing batch delete: {e}")
                        # Handle batch failure (e.g., retry, log, etc.)
                        # You might want to consider retrying the batch or logging the error and moving on.
                        # To retry:
                        # time.sleep(5)  # Wait before retrying
                        # self.delete_entities_in_batches(partition_key, batch_size) #recursively call the function

        print(f"Finished deleting entities with PartitionKey '{partition_key}'.")


    def store_job(self, job):
        if self.table_client:
            job_entity = TableEntity()
            job_entity['PartitionKey'] = 'GoogleCareersJob'
            job_entity['RowKey'] = job.id
            job_entity['JobName'] = job.title
            job_entity['JobDescription'] = job.description
            job_entity['URL'] = job.apply_link
            self.table_client.upsert_entity(entity=job_entity)
            print(f"Stored job: {job.title}")

# def main():
#     base_url = 'https://careers.google.com/jobs/results/?company=Fitbit&company=GFiber&company=Google&company=YouTube&company=Verily%20Life%20Sciences&company=Waymo&company=Wing&company=X&distance=50&employment_type=FULL_TIME&employment_type=INTERN&hl=en_US&jlo=en_US&q=&sort_by=relevance'
#     azure_connection_string = 'DefaultEndpointsProtocol=https;AccountName=jobsdetails;AccountKey=hyv15hGwCxlf8e2NcI3YJ9FtD+EtCAp9W0pdtPBh3HhKICYemrgrZwRSbhXEkthCHj57rddFLkPs+ASt+Cf+Mw==;EndpointSuffix=core.windows.net'
#     table_name = 'JobDetails'

#     scraper = JobScraper(base_url)
#     azure_storage = AzureTableStorage(azure_connection_string, table_name)
#     azure_storage.delete_entities_in_batches()
#     job_list = scraper.fetch_job_data()
#     for job in job_list:
#         print(job)
#         azure_storage.store_job(job)
#     # url = "https://www.google.com/about/careers/applications/jobs/results?q=%22Google%20Cloud%22&location=India&src=Online/House%20Ads/BKWS_LOC1&gad_source=1&gclid=CjwKCAiAudG5BhAREiwAWMlSjG7bqf4FB0Exf4RLaYhIl-OmK3vIviJPuKlcYsgRk-OYWlhCkDwpHRoCzRYQAvD_BwE"
#     # googlecareer = GoogleCareer(url)
#     # googlecareer.open_website()
#     # googlecareer.apply_job()

# if __name__ == '__main__':
#     main()

