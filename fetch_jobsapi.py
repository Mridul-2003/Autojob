from flask import Flask,request,jsonify
from corazor_jobs import CorazorJobs,AzureTableStorage

app=Flask(__name__)

@app.route("/fetch_jobs",methods=['POST'])
def fetch_jobs():
    data = request.get_json()
    base_url = data['base_url']
    corazorjobs = CorazorJobs(base_url)
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
        return jsonify({"msg":"Jobs data succesfully stored","jobs":job_data})
    else:
        return jsonify({"msg":"No jobs extracted"})
