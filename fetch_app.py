# app.py
import streamlit as st
from corazor_jobs import CorazorJobs, AzureTableStorage

st.set_page_config(page_title="Corazor Job Scraper", layout="wide")
st.title("🧲 Corazor Job Scraper")

BASE_URL = "https://corazor-technology.vercel.app/careers"
base_url = st.text_input("Enter the URL of the job page:", value=BASE_URL, key="url_input")
if st.button("🔍 Fetch Jobs from Website"):
    with st.spinner("Fetching and parsing jobs using Gemini..."):
        scraper = CorazorJobs(base_url)
        jobs = scraper.fetch_jobs()

        if jobs:
            st.success(f"✅ Fetched {len(jobs)} jobs!")
            connection_string = "DefaultEndpointsProtocol=https;AccountName=jobsdetails;AccountKey=hyv15hGwCxlf8e2NcI3YJ9FtD+EtCAp9W0pdtPBh3HhKICYemrgrZwRSbhXEkthCHj57rddFLkPs+ASt+Cf+Mw==;EndpointSuffix=core.windows.net"
            table_name = "CorazorJobDetails"
            storage = AzureTableStorage(connection_string,table_name)
            storage.delete_entities_in_batches(partition_key="CorazorCareer")
            for job in jobs:
                with st.expander(job.title):
                    st.write(f"**Description:** {job.description}")
                    st.write(f"**Place:** {job.place}")
                    st.write(f"**Type:** {job.job_type}")
                    st.write(f"[Apply Here]({job.apply_link})")
                    
                    storage.store_job(job)
        else:
            st.error("❌ No jobs found or error occurred.")

