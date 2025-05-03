import google.generativeai as genai
from dotenv import load_dotenv
import os
from resume_parse import extract_text_from_pdf
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
class AnswerQuestions:
    def __init__(self, resume_text):
        self.resume_text = resume_text
        self.model = genai.GenerativeModel('gemini-2.0-flash')
    def generate_content(self, query):
        response = self.model.generate_content(query)
        return response.text


