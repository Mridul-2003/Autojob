import streamlit as st
from azure.data.tables import TableServiceClient
from azure.core.exceptions import HttpResponseError
import logging
from ats_score import UpdateResume
from resume_parse import extract_text_from_pdf
from dotenv import load_dotenv
import os
import google.generativeai as genai
from apply_jobs import ApplyJobs
import tempfile
from fpdf import FPDF
from coverletter import GenerateCoverLetter
import google.api_core.exceptions
from update_resume import EnhanceResume
import time
from src.resume_generate import ResumeGenerator
# -------------------------
# Azure Class
# -------------------------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
def generate_with_retry(model, inputs, max_retries=5, initial_delay=1, backoff_factor=2):
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            response = model.generate_content(inputs)
            return response.text
        except google.api_core.exceptions.ResourceExhausted as e:  # 429 error
            print(f"Rate limit hit (attempt {attempt + 1}), retrying in {delay}s...")
            time.sleep(delay)
            delay *= backoff_factor
        except Exception as e:
            print(f"Error: {e}")
            break
    return "❌ Failed to generate content after retries."
class FilterData:
    def __init__(self, connection_string, table_name):
        self.connection_string = connection_string
        self.table_name = table_name
        self.table_client = None
        self.initialize_table()

    def initialize_table(self):
        try:
            table_service_client = TableServiceClient.from_connection_string(self.connection_string)
            self.table_client = table_service_client.get_table_client(self.table_name)
            logging.info(f"Successfully connected to Table: {self.table_name}")
        except Exception as e:
            logging.error(f"Failed to initialize Azure Table service: {e}")
            raise

    def fetch_job_data(self, top_n):
        """Fetch top N job data from Azure Table Storage."""
        job_data = []
        try:
            entities = self.table_client.list_entities(results_per_page=top_n)
            page = next(entities.by_page())

            for i, entity in enumerate(page):
                if i >= top_n:  # Extra check
                    break
                job_data.append({
                    'job_title': entity.get('JobName'),
                    'job_description': entity.get('JobDescription'),
                    'job_apply_link': entity.get('URL'),
                    'partition_key': entity.get('PartitionKey'),
                    'row_key': entity.get('RowKey')
                })
            logging.info(f"Fetched {len(job_data)} jobs (limited to top {top_n}).")
        except HttpResponseError as e:
            logging.error(f"HTTP error fetching job data: {e}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
        return job_data

    def filter_jobs(self, job_data, search_term,resume_path):
        filtered_jobs = []
        non_filtered_jobs=[]
        search_term_lower = search_term.lower()
        for job in job_data:
            job_title = job.get('job_title', '').lower()
            job_description = job.get('job_description', '').lower()
            resume_text = extract_text_from_pdf(resume_path)
            updateresume=UpdateResume(job_description,resume_text)
            ats_score = updateresume.calculate_ats()
            query = f"""your task is to check wether the seacrh keyword match the job.
            The given search keyword is {search_term_lower} and job is {job}.If job matches send output Yes else No.
            Dont give anything else in result instead of yes or no."""
            gemini_response = generate_with_retry(model, [query])
            print("Gemini Response:",gemini_response)
            print(ats_score)
            if ats_score[0]['ats_score']>60:
                if gemini_response.strip().lower() == "yes":
                    filtered_jobs.append(job)
                    print(ats_score)
            else:
                non_filtered_jobs.append(job)
        logging.info(f"Found {len(filtered_jobs)} jobs matching '{search_term}'.")
        return filtered_jobs,non_filtered_jobs

# ---------------------------
# Streamlit App
# ---------------------------
# Azure credentials
connection_string = "DefaultEndpointsProtocol=https;AccountName=jobsdetails;AccountKey=hyv15hGwCxlf8e2NcI3YJ9FtD+EtCAp9W0pdtPBh3HhKICYemrgrZwRSbhXEkthCHj57rddFLkPs+ASt+Cf+Mw==;EndpointSuffix=core.windows.net"
table_name = "CorazorJobDetails"

# Initialize Azure connection
filter_data = FilterData(connection_string, table_name)
sign_in = st.sidebar.button("Sign In", key="signin_button")
sign_up = st.sidebar.button("Sign Up", key="signup_button")
log_out = st.sidebar.button("Log Out",key="log_out")
signin = False
if not st.session_state.get("signin_done", False):
    if sign_in or signin == False and not sign_up:
        st.title("Sign In")
        email = st.text_input("Email","gauravsaini905888@gmail.com",key="email")
        password = st.text_input("Password","Gaurav$05",type="password",key="password")
        sign_in_button = st.button("Sign In")
        if sign_in_button:
            # Here you would typically check the credentials against a database
            signin = True
            st.session_state["credentials_ready"]=True
            st.session_state["signin_done"] = True
            Email = st.session_state["email"]
            Password = st.session_state["password"]
            email+=Email
            password+=Password
            st.success("Sign In successful!")
            time.sleep(5)
            st.rerun()
elif log_out:
    st.session_state["signin_done"] = False
    st.session_state["credentials_ready"] = False
    st.success("Logged out successfully!")
    time.sleep(5)
    st.rerun()
else:   
    if sign_up and sign_in:
        st.success("Already signed in. Please sign out to create a new account.")        
    # Sidebar Navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Go to", ["Job Search", "Create Resume"])

    if page == "Create Resume":
        # Resume Creation Page
        st.title("📄 Create Your Resume")

        # Input for Basics Section
        st.subheader("Basics Section")
        firstname = st.text_input("First Name", "Mridul")
        lastname = st.text_input("Last Name", "Mittal")
        email = st.text_input("Email", "mridulmittal2003@gmail.com")
        phone = st.text_input("Phone", "+91-9667677092")
        website = st.text_input("Website", "")
        address = st.text_input("Address", "")

        basics_section = {
            "basics": [
                {
                    "firstname": firstname,
                    "lastname": lastname,
                    "email": email,
                    "phone": phone,
                    "website": website if website.strip() else None,
                    "address": address if address.strip() else None,
                }
            ]
        }

        # Input for Education Section
        st.subheader("Education Section")
        degree = st.text_input("Degree", "Bachelor of Technology")
        major = st.text_input("Major", "Artificial Intelligence and Machine Learning")
        institution = st.text_input("Institution", "Guru Gobind Singh Indraprastha University")
        city = st.text_input("City", "Delhi")
        start_date = st.text_input("Start Date", "July 2021")
        end_date = st.text_input("End Date", "July 2025")
        gpa = st.text_input("GPA", "8.493")

        education_section = {
            "education": [
                {
                    "degree": degree,
                    "major": major,
                    "institution": institution,
                    "city": city,
                    "start_date": start_date,
                    "end_date": end_date,
                    "gpa": gpa,
                }
            ]
        }

        # Input for Awards Section
        st.subheader("Awards Section")
        awards = []
        for i in range(1):  # Allow up to 1 award
            award_title = st.text_input(f"Award Title {i + 1}", "Open Source Coordinator, Google Developer Students Club USAR")
            award_date = st.text_input(f"Award Date {i + 1}", "August 2023 – September 2024")
            award_description = st.text_area(f"Award Description {i + 1}", "")
            awards.append(
                {
                    "title": award_title,
                    "date": award_date,
                    "description": award_description,
                }
            )

        awards_section = {"awards": awards}

        # Input for Projects Section
        st.subheader("Projects Section")
        projects = []
        for i in range(3):  # Allow up to 3 projects
            st.text(f"Project {i + 1}")
            project_title = st.text_input(f"Title {i + 1}", key=f"project_title_{i}")
            project_description = st.text_area(f"Description {i + 1}", key=f"project_description_{i}")
            project_tools = st.text_input(f"Tools {i + 1} (comma-separated)", key=f"project_tools_{i}")
            projects.append(
                {
                    "title": project_title,
                    "description": project_description,
                    "tools": [tool.strip() for tool in project_tools.split(",") if tool.strip()],
                    "impact": "",
                }
            )

        projects_section = {"projects": projects}

        # Input for Skills Section
        st.subheader("Skills Section")
        skills = []
        for i in range(3):  # Allow up to 3 skill categories
            st.text(f"Skill Category {i + 1}")
            skill_name = st.text_input(f"Category Name {i + 1}", key=f"skill_name_{i}")
            skill_keywords = st.text_input(f"Keywords {i + 1} (comma-separated)", key=f"skill_keywords_{i}")
            skills.append(
                {
                    "name": skill_name,
                    "keywords": [keyword.strip() for keyword in skill_keywords.split(",") if keyword.strip()],
                }
            )

        skills_section = {"skills": skills}

        # Input for Work Experience Section
        st.subheader("Work Experience Section")
        work_experience = []
        for i in range(2):  # Allow up to 2 work experiences
            st.text(f"Work Experience {i + 1}")
            job_title = st.text_input(f"Job Title {i + 1}", key=f"job_title_{i}")
            company_name = st.text_input(f"Company Name {i + 1}", key=f"company_name_{i}")
            location = st.text_input(f"Location {i + 1}", key=f"location_{i}")
            start_date = st.text_input(f"Start Date {i + 1}", key=f"work_start_date_{i}")
            end_date = st.text_input(f"End Date {i + 1}", key=f"work_end_date_{i}")
            responsibilities = st.text_area(f"Responsibilities {i + 1} (comma-separated)", key=f"responsibilities_{i}")
            work_experience.append(
                {
                    "job_title": job_title,
                    "company_name": company_name,
                    "location": location,
                    "start_date": start_date,
                    "end_date": end_date,
                    "responsibilities": [resp.strip() for resp in responsibilities.split(",") if resp.strip()],
                }
            )

        work_section = {"work_experience": work_experience}

        # Combine all sections into a JSON resume
        json_resume = {
            **basics_section,
            **education_section,
            **awards_section,
            **projects_section,
            **skills_section,
            **work_section,
        }

        # Display JSON Resume
        st.subheader("Generated JSON Resume")
        st.json(json_resume)

        # Generate Resume Button
        if st.button("✨ Generate Resume"):
            generator = ResumeGenerator()
            resume_bytes = generator.generate_resume_from_json(json_resume, "Awesome", ["education", "work", "skills", "projects", "awards"], improve_check=True)

            if resume_bytes:
                st.success("✅ Resume generated successfully!")

                # Provide a download button for the generated resume
                with open("Generated_Resume.pdf", "wb") as f:
                    f.write(resume_bytes)
                with open("Generated_Resume.pdf", "rb") as f:
                    st.download_button(
                        label="⬇️ Download Resume as PDF",
                        data=f.read(),
                        file_name="Generated_Resume.pdf",
                        mime="application/pdf"
                    )
            else:
                st.error("❌ Failed to generate resume. Please check your input.")
    else:

        # Upload Resume
        uploaded_resume = st.sidebar.file_uploader("📄 Upload your Resume (PDF)", type=["pdf"])
        resume_path = None
        cover_letter_path = None
        ai_generated_cover_letter = None

        # Cover Letter Option
        cover_letter_option = st.sidebar.radio("📝 Cover Letter:", ("Upload", "Generate using AI","Generate for specific job or project"))
        uploaded_cover_letter = None

        st.sidebar.write("Important Extra Details")
        work_mode = st.sidebar.radio("Preferef Work Mode:",("Remote","On-site","Hybrid"))
        join_immediately = st.sidebar.radio("Are you ready to join immedately?",("Yes","No"))
        current_location = st.sidebar.text_input("Current Location", "")
        email = st.sidebar.text_input("Enter Your Email","")
        password = st.sidebar.text_input("Enter your Password","",type="password")
        if uploaded_resume:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(uploaded_resume.read())
                resume_path = temp_file.name
            st.sidebar.success("✅ Resume uploaded successfully!")

            # Handle cover letter based on selected option
            if cover_letter_option == "Upload":
                uploaded_cover_letter = st.sidebar.file_uploader("Upload Cover Letter (PDF)", type=["pdf"])
                if uploaded_cover_letter:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_cl:
                        temp_cl.write(uploaded_cover_letter.read())
                        cover_letter_path = temp_cl.name
                    st.sidebar.success("✅ Cover Letter uploaded successfully!")

            # elif cover_letter_option == "Generate using AI":
            #     job_description = st.sidebar.text_area("Paste Job Description to generate Cover Letter", "")
            #     generate_btn = st.sidebar.button("✨ Generate Cover Letter")

            #     if generate_btn:
            #         if job_description.strip() == "":
            #             st.sidebar.warning("Please paste the job description.")
            #         else:
            #             resume_text = extract_text_from_pdf(resume_path)

            #             # Generate Cover Letter using AI
            #             generator = GenerateCoverLetter(resume_text, job_description)
            #             result = generator.generate_cover_letter()
            #             ai_generated_cover_letter = result["Cover_Letter"]

            #             st.subheader("📄 AI-Generated Cover Letter")
            #             st.write(ai_generated_cover_letter)

            #             # Generate PDF from text
            #             pdf = FPDF()
            #             pdf.add_page()
            #             pdf.set_auto_page_break(auto=True, margin=15)
            #             pdf.set_font("Arial", size=12)
            #             for line in ai_generated_cover_letter.split('\n'):
            #                 pdf.multi_cell(0, 10, line)

            #             pdf_path = os.path.join(tempfile.gettempdir(), "ai_cover_letter.pdf")
            #             pdf.output(pdf_path)

            #             with open(pdf_path, "rb") as f:
            #                 st.download_button(
            #                     label="⬇️ Download Cover Letter as PDF",
            #                     data=f.read(),  # ✅ FIX: pass bytes instead of file object
            #                     file_name="AI_Cover_Letter.pdf",
            #                     mime="application/pdf"
            #                 )

        else:
            st.sidebar.warning("⚠️ Please upload your resume to proceed.")

        # Search Section
        search_term = st.sidebar.text_input("Enter Job Title", "")
        search_button = st.sidebar.button("Search")

        # Main Area
        st.title("💼 Job Search and Apply")
        def sanitize_text(text):
            return text.encode('latin-1', 'replace').decode('latin-1')

        job_urls = []
        if cover_letter_option == "Generate for specific job or project":
            st.write("### Generate Cover Letter for a Specific Job or Project")
            job_description = st.text_area("Paste Job Description or Project to generate Cover Letter", "")
            generate_btn = st.button("✨ Generate Cover Letter")

            if generate_btn:
                if job_description.strip() == "":
                    st.warning("Please paste the job description or project details.")
                else:
                    resume_text = extract_text_from_pdf(resume_path)

                    # Generate Cover Letter using AI
                    generator = GenerateCoverLetter(resume_text, job_description)
                    result = generator.generate_cover_letter()
                    ai_generated_cover_letter = result["Cover_Letter"]

                    st.subheader("📄 AI-Generated Cover Letter")
                    st.write(ai_generated_cover_letter)

                    # Generate PDF from text
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_auto_page_break(auto=True, margin=15)
                    pdf.set_font("Arial", size=12)
                    for line in ai_generated_cover_letter.split('\n'):
                        pdf.multi_cell(0, 10, sanitize_text(line))

                    pdf_path = os.path.join(tempfile.gettempdir(), "ai_cover_letter.pdf")
                    pdf.output(pdf_path)

                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="⬇️ Download Cover Letter as PDF",
                            data=f.read(),
                            file_name="AI_Cover_Letter.pdf",
                            mime="application/pdf"
                        )
        non_ats_jobs = []
        if search_button or cover_letter_option == "Generate using AI" :
            if not resume_path:
                st.warning("⚠️ Upload your resume before searching.")
            elif search_term:
                with st.spinner(""):
                    job_data = filter_data.fetch_job_data(top_n=15)
                    print(f"[DEBUG] Total Top Jobs Fetched: {len(job_data)}")

                    if job_data:
                        filtered_jobs,non_ats_jobs= filter_data.filter_jobs(job_data, search_term, resume_path)
                        non_ats_jobs = [job for job in non_ats_jobs if job not in filtered_jobs]
                        print(f"[DEBUG] Jobs matching '{search_term}': {len(filtered_jobs)}")
                        print(f"[DEBUG] Non-ATS Jobs: {len(non_ats_jobs)}")
                        st.write(f"### Jobs matching **'{search_term}'** (Top 5 Search):")

                        if filtered_jobs:
                            for idx, job in enumerate(filtered_jobs, start=1):
                                st.subheader(f"{idx}. {job['job_title']}")
                                st.write(job['job_description'])
                                st.write(f"**Apply Here:** [Link]({job['job_apply_link']})")
                                job_urls.append(job['job_apply_link'])
                            

                                # Optional: Generate Cover Letter
                                if cover_letter_option == "Generate using AI":
                                    if st.button(f"✨ Generate Cover Letter for Job {idx}"):
                                        resume_text = extract_text_from_pdf(resume_path)
                                        generator = GenerateCoverLetter(resume_text, job["job_description"])
                                        result = generator.generate_cover_letter()
                                        ai_generated_cover_letter = result["Cover_Letter"]

                                        # Clean special characters
                                        def clean_cover_letter(text):
                                            replacements = {
                                                '–': '-', '—': '-',  # dashes
                                                '“': '"', '”': '"',  # double quotes
                                                '‘': "'", '’': "'",  # single quotes
                                                '…': '...',          # ellipsis
                                            }
                                            for key, val in replacements.items():
                                                text = text.replace(key, val)
                                            return text

                                        ai_generated_cover_letter = clean_cover_letter(ai_generated_cover_letter)

                                        # Display cover letter
                                        st.write("📄 **Generated Cover Letter:**")
                                        st.code(ai_generated_cover_letter)

                                        # Convert to PDF
                                        pdf = FPDF()
                                        pdf.add_page()
                                        pdf.set_auto_page_break(auto=True, margin=15)
                                        pdf.set_font("Arial", size=12)
                                        for line in ai_generated_cover_letter.split('\n'):
                                            pdf.multi_cell(0, 10, line)

                                        cover_letterpdf_path = os.path.join(tempfile.gettempdir(), f"ai_cover_letter_{idx}.pdf")
                                        pdf.output(cover_letterpdf_path)

                                        # Store in session state
                                        st.session_state[f"cover_letter_path_{idx}"] = cover_letterpdf_path
                                        st.session_state[f"ai_cover_letter_text_{idx}"] = ai_generated_cover_letter

                                        # Download button
                                        with open(cover_letterpdf_path, "rb") as f:
                                            st.download_button(
                                                label="⬇️ Download This Cover Letter as PDF",
                                                data=f.read(),
                                                file_name=f"AI_Cover_Letter_Job_{idx}.pdf",
                                                mime="application/pdf"
                                            )

                                
                                        cover_letter_path_key = f"cover_letter_path_{idx}"
                                        ai_text_key = f"ai_cover_letter_text_{idx}"

                                        if cover_letter_path_key not in st.session_state:
                                            st.warning("⚠️ No cover letter provided. Please upload or generate one first.")
                                        else:
                                            cover_letter_path = st.session_state[cover_letter_path_key]
                                            ai_generated_cover_letter = st.session_state[ai_text_key]
                                            st.write(f"Applying for job: {job['job_apply_link']}")
                                            applyjobs = ApplyJobs(job['job_apply_link'],resume_path)
                                            applyjobs.signin(cover_letter_path, ai_generated_cover_letter,work_mode,join_immediately,current_location)
                                            st.success(f"✅ Successfully applied for: {job['job_title']}")
                                
                                else:
                                    
                                    st.write(f"Applying for job: {job['job_apply_link']}")
                                    applyjobs = ApplyJobs(job['job_apply_link'],resume_path)
                                    applyjobs.signin(email,password,cover_letter_path, ai_generated_cover_letter,work_mode,join_immediately,current_location)
                                    st.success(f"✅ Successfully applied for: {job['job_title']}")

                                st.markdown("---")
                        else:
                            st.warning("No jobs matched your search term.")
                    else:
                        st.error("No job data found. Please check Azure connection.")
            else:
                st.warning("Please enter a job title to search for jobs.")           
        # if non_ats_jobs or st.download_button:
        #     st.write(f"### Non-ATS Jobs (Not Matching Criteria):")
        #     for idx, job in enumerate(non_ats_jobs, start=1):
        #         st.subheader(f"{idx}. {job['job_title']}")
        #         st.write(job['job_description'])
        #         st.write(f"**Apply Here:** [Link]({job['job_apply_link']})")
        #         job_description = job['job_description']
        #         resume_text = extract_text_from_pdf(resume_path)

        #         # Enhance the resume using UpdateResume
        #         enhancedresume = EnhanceResume(job_description, resume_text)
        #         enhanced_resume_text = enhancedresume.update_resume()

        #             # Display the enhanced resume
        #         st.write("📄 **Enhanced Resume:**")
        #         st.code(enhanced_resume_text)

        #         enhanced_resume_pdf_path = "/Volumes/PortableSSD/Jobscraper/src/resume.pdf"

        #             # Provide a download button for the enhanced resume
        #         with open(enhanced_resume_pdf_path, "rb") as f:
        #             st.download_button(
        #                                     label="⬇️ Download Enhanced Resume as PDF",
        #                                     data=f.read(),
        #                                     file_name=f"Enhanced_Resume_Job_{idx}.pdf",
        #                                     mime="application/pdf"
        #                                 )

                st.markdown("---")
        else:
            st.info("No Non-ATS jobs found.")
                    
            

# # Run the Streamlit app
# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO)
#     st.sidebar.title("Navigation")
#     st.sidebar.write("Welcome to the Job Search and Apply App!")
#     st.sidebar.write("Please sign in to access the features.")
#     st.sidebar.write("Developed by Mridul Mittal")
#     st.sidebar.write("Version 1.0")
