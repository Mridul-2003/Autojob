from dotenv import load_dotenv
import google.generativeai as genai
import os
import json
import re
import PyPDF2
import time
from resume_parse import ResumeParse
from resume_parse import extract_text_from_pdf
import google.api_core.exceptions
load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API"))
def generate_with_retry(model, inputs, max_retries=10, initial_delay=1, backoff_factor=2):
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
class UpdateResume:
    def __init__(self,job_description_text,resume_text):
        self.job_description_text = job_description_text
        self.resume_text = resume_text

    def calculate_ats(self):
        prompt = """ 
        Calculate the ATS score or the similarity score of the provided resume_text by comparing it with
the provided job_description_text. Do not provide any explanation, only return the result in the following JSON format:
        Schema:
{
    "ats_score":int
}
example:
{
"ats_score":80
}
"""
        model = genai.GenerativeModel("gemini-1.5-flash")
        input = [self.job_description_text,self.resume_text,prompt]
        parse = ResumeParse(self.resume_text,self.job_description_text)
        response = generate_with_retry(model, input)
        cleaned_response = parse.clean_response(response)
        print("Cleaned Response:", cleaned_response)
        cleaned_response = cleaned_response.strip()
        ats_score = json.loads(cleaned_response)
        return ats_score
    def resume_update(self):
        prompt = """ 
        Update the given resume_text on the basis of provided job_description_text
        by highlighting the required keywords correctly in the resume to 
         increase the resume ATS score in comparsion to job description and
        dont add any external keyword or skill that are not present in the 
        provided resume_text .Give only the updated resume_text as output.
        Example Output: 
        Education
Mridul Mittal
Bachelor of Technology
Artificial Intelligence and Data Science
Guru Gobind Singh Indraprastha University, Delhi Enrollment No: 08419011921
+91-9667677092 mridulmittal2003@gmail.com GitHub Kaggle LinkedIn
 •Bachelor of Technology in Artificial Intelligence and Machine Learning UNIVERSITY SCHOOL OF AUTOMATION AND ROBOTICS, Surajmal Vihar, New Delhi
•Intermediate
Ramjas School, Pusa Road, Delhi
Personal Projects
•Automatic Text Summarization and Language Translation Python, TextRank, Google Translate
July 2021 - July 2025
CGPA: 8.493
July 2020 - July 2021
Percentage: 82
 – Implemented a TextRank-based algorithm using the ’gensim’ library, improving keyword extraction efficiency by 40% and reducing content processing time by 20 hours monthly.
•Pizza Messiness Score Calculator
Python, OpenCV, MediaPipe, CNN, Transfer Learning
– Developed an innovative ’Pizza Messiness Score Calculator’ using OpenCV and MediaPipe.
– Deployed a CNN model, achieving 95% accuracy in pizza classification and reducing manual identification time by
70%.
•Machine Translation using Seq2Seq Model NLP, Deep Learning, RNN, LSTM, TensorFlow
– Built a Seq2Seq model for machine translation of resumes between languages, improving accessibility for global job markets.
Experience
•Corazor Technology Private Limited March 2024 - Present
AI Intern Remote
– Gained expertise in Azure ML Studio, data storage, and related tools.
– Engineered an AI-driven recommendation system leveraging NLP algorithms and Microsoft Azure, leading to a
notable 40 percent reduction in customer churn through tailored product suggestions based on previous purchasing
behavior.
– Developed AI algorithms for a truck tracking system using Python and Google Maps API.
– Created Flask API for findid Nearby Workers and Navigating Workers.
– Working on Automated Lead Generations using Selenium.
 •The Moronss ML and AI Intern
– Developing AI/ML solutions for an Applicant Tracking System (ATS).
– Created an automated question generation system for personalized test preparation. – Collaborating on projects to enhance student employability.
Technical Skills and Interests
June 2024 - September 2024
Hybrid
 Languages: C/C++, Python, Javascript, HTML+CSS
Libraries: TensorFlow, Scikit-learn, OpenCV, Keras, pandas, numpy, matplotlib, MediaPipe
Web Dev Tools: VScode, Git, GitHub
Frameworks: Flask, Django
Cloud/Databases: MongoDB, Microsoft Azure, MySQL
Relevant Coursework: Data Structures, Algorithms, Operating Systems, OOP, DBMS, Software Engineering, Machine Learning, Deep Learning, Neural Networks, NLP, Computer Vision, Agile Testing Additional Skills: Large Language Models (LLM), Retrieval-Augmented Generation (RAG), Hyperparameter Tuning, JIRA, Manual Testing, Automated Testing
Areas of Interest: Web Development, Artificial Intelligence, Generative AI
Positions of Responsibility
•Open Source CoordinatorGoogle Developer Students Club USAR August 2023 - September 2024 – Contributed to open-source projects within the Google Developer Students Club.


"""
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content([self.job_description_text,
                                           self.resume_text,
                                           prompt])
        return response.text
    

# pdf_path = "/Users/useradmin/Desktop/AutoJobsApply/resume-9.pdf"
# resume_text = extract_text_from_pdf(pdf_path)
# job_description = "About the internship:As an AI Intern with a focus on Computer Vision and Video Analytics, you will work closely with our AI and engineering teams to develop, implement, and optimize computer vision algorithms for analyzing video data. This internship will provide hands-on experience in a fast-paced and collaborative environment, offering the opportunity to work on real-world projects that drive innovation and efficiency.Selected intern's day-to-day responsibilities include:1. Assist in developing and implementing computer vision algorithms for video analysis.2. Work with large datasets of video footage to extract meaningful insights.3. Collaborate with the team to design, train, and evaluate machine learning models.4. Participate in the integration and testing of computer vision solutions within existing systems.5. Conduct research to stay updated on the latest advancements in computer vision and video analytics.6. Assist in the preparation of technical documentation and reports.Who can applyOnly those candidates can apply who:1. are available for full time (in-office) internship2. can start the internship between 10th Dec'24 and 14th Jan'253. are available for duration of 2 months4. have relevant skills and interestsStipend:INR ₹ 8,000-10,000 /monthDeadline:2025-01-09 23:59:59Other perks:Certificate, Flexible work hoursSkills required:Python, Machine Learning, Computer Vision, Artificial Intelligence and Deep LearningAbout Company:Indika AI is a global data service company working with some of the advanced artificial intelligence (AI) companies across the world to help them train their AI models with exceptional quality training data. We provide data annotation, search relevance, and content moderation services."
# updateresume=UpdateResume(job_description,resume_text)
# ats_score = updateresume.calculate_ats()
# print(ats_score)