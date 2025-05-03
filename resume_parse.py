from dotenv import load_dotenv
import google.generativeai as genai
import os
import json
import re
import PyPDF2
import time
import google.api_core.exceptions

# Load environment variables
load_dotenv()

# Configure the generative AI model
genai.configure(api_key=os.getenv("GEMINI_API"))

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


def extract_text_from_pdf(pdf_path):
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    text += page_text
        return text
# Resume parsing class
class ResumeParse:
    def __init__(self, resume_text,job_description):
        self.resume_text = resume_text
        self.job_description = job_description
    def clean_response(self, response_text):
        """
        Clean the response text to remove unwanted JSON formatting artifacts
        like backticks, code blocks, or extra text, and handle Unicode characters.
        """
        # Remove markdown-like code blocks (```json ... ```)
        cleaned_response = re.sub(r'```json\n|```', '', response_text)

        # Replace problematic characters like dashes and special quotes
        cleaned_response = cleaned_response.replace("â", "-").replace("\u2019", "'")

        # Replace specific characters and encoded newlines
        cleaned_response = re.sub(r'\\n', ' ', cleaned_response)
        cleaned_response = re.sub(r'\\u2013', '-', cleaned_response)

        # Remove any non-ASCII characters
        cleaned_response = re.sub(r'[^\x00-\x7F]+', ' ', cleaned_response)

        # Remove excessive spaces and ensure valid JSON brackets
        cleaned_response = re.sub(r'\s+', ' ', cleaned_response).strip()

        if not cleaned_response.startswith("["):
            cleaned_response = "[" + cleaned_response
        if not cleaned_response.endswith("]"):
            cleaned_response = cleaned_response + "]"

        return cleaned_response
    

    def parse_work_experience(self, prompt):
        # Generate the response from generative AI model
        model = genai.GenerativeModel("gemini-1.5-flash")
        inputs = [self.resume_text, self.job_description, prompt]
        return generate_with_retry(model, inputs)
    def extract_json_string(self,cleaned_output):
        # Use a regular expression to extract all valid JSON parts between curly braces
        json_match = re.findall(r'(\{.*?\})', cleaned_output, re.DOTALL)
        
        if json_match:
            # Since you may have multiple JSON objects (one per work experience), create a list of them
            json_list = []

            for match in json_match:
                json_string = match

                # Clean the string: replace single quotes with double quotes
                json_string = json_string.replace("'", '"')

                # Replace "null" strings with actual null
                json_string = json_string.replace('"null"', 'null')

                # Replace Python booleans (True/False) with JSON-compliant booleans (true/false)
                json_string = json_string.replace("True", "true").replace("False", "false")
                
                # Remove markdown-like syntax like '**' or any other extra characters
                json_string = json_string.replace("**", "")
                
                # Clean up whitespace or newlines
                json_string = re.sub(r'\s+', ' ', json_string).strip()

                try:
                    # Try to load each JSON object
                    json_obj = json.loads(json_string)
                    json_list.append(json_obj)
                except json.JSONDecodeError as e:
                    print(f"Failed to parse part of the string: {json_string}")
                    print(f"Error: {e}")
                    continue
            
            return json_list

        else:
            print("No valid JSON structure found in the string.")
            return None