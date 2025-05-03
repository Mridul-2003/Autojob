import streamlit as st
from bs4 import BeautifulSoup
import requests
import uuid
from urllib.parse import urljoin

# Define Job class
class Job:
    def __init__(self, title, description, apply_link):
        self.title = title
        self.description = description
        self.apply_link = apply_link
        self.id = str(uuid.uuid4())

    def __repr__(self):
        return f"Job(title={self.title!r}, description={self.description[:50]!r}..., apply_link={self.apply_link!r})"

# Define JobScraper class
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

            job_elements = soup.find_all('a', {'class': 'WpHeLc VfPpkd-mRLv6 VfPpkd-RLmnJb'})
            titles = soup.find_all('h3', {'class': 'QJPWVe'})

            if len(job_elements) == 0:
                break

            for job_element, title_element in zip(job_elements, titles):
                job_href = job_element.get('href')
                if job_href:
                    job_link = urljoin("https://careers.google.com", job_href)
                    job_title = title_element.text.strip()

                    # Fetch job description and apply link
                    job_description, apply_link = self.fetch_job_details(job_link)
                    
                    job = Job(title=job_title, description=job_description, apply_link=apply_link)
                    all_jobs.append(job)

                    if len(all_jobs) >= 10:  # Stop after 10 jobs
                        return all_jobs

            page += 1

        return all_jobs

    def fetch_job_details(self, job_url):
        response = requests.get(job_url)
        if response.status_code != 200:
            return "", ""

        soup = BeautifulSoup(response.text, 'html.parser')

        try:
            qualification = soup.find("div", class_="KwJkGe")
            about_job = soup.find("div", class_="aG5W3")
            responsibilities = soup.find("div", class_="BDNOWe")
            sections = [section.get_text(strip=True) for section in [qualification, about_job, responsibilities] if section]
            job_description = "\n".join(sections)
        except:
            job_description = ""

        try:
            apply_button = soup.find("a", {"aria-label": "Apply"})
            if apply_button:
                apply_href = apply_button.get('href')
                apply_link = urljoin("https://careers.google.com", apply_href)
            else:
                apply_link = ""
        except:
            apply_link = ""

        return job_description, apply_link

# Streamlit UI
st.set_page_config(page_title="Google Careers Scraper", layout="wide")

st.title("Google Careers - Top 10 Jobs")

# Input Base URL
base_url = st.text_input(
    "Enter Google Careers URL:",
    value="https://careers.google.com/jobs/results/?company=Google&distance=50&employment_type=FULL_TIME&hl=en_US&jlo=en_US&q=&sort_by=relevance"
)

if st.button("Fetch Jobs"):
    with st.spinner('Fetching jobs... Please wait.'):
        scraper = JobScraper(base_url)
        jobs = scraper.fetch_job_data()

        if jobs:
            for idx, job in enumerate(jobs, start=1):
                st.subheader(f"{idx}. {job.title}")
                st.markdown(f"**Description:** {job.description[:500]}...")  # Limit description preview
                st.markdown(f"[Apply Here]({job.apply_link})")
                st.markdown("---")
        else:
            st.error("No jobs found!")

