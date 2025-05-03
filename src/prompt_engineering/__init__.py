import google.generativeai as genai
import json
import os
import re

# Configure the Google Generative AI (Gemini) API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def clean_response(response_text):
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

    # Remove any leading or trailing text outside of JSON brackets
    json_start = cleaned_response.find('{')
    json_end = cleaned_response.rfind('}') + 1
    cleaned_response = cleaned_response[json_start:json_end]

    return cleaned_response

def generate_json_resume(cv_text, api_key):
    """Generate a JSON resume from a CV text"""
    final_json = {}
    genai.configure(api_key=api_key)

    # Use the Gemini model
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Define prompts and schemas for each section of the resume
    sections = {
        "basics": {
            "prompt": """
            Extract the candidate's basic information including firstname,lastname, email, phone number, website, and address. 
            Provide the output in JSON format using the following schema:
            
            ```json
            basics:[{
              "firstname": str,
              "lastname::str,
              "email": str,
              "phone": str,
              "website": str,
              "address": str
            }]
            ```
            """,
            "content": ""
        },

        "education": {
            "prompt": "Extract the candidate's education details using the following schema:\n\n```json\n{\n  \"education\": [\n    {\n      \"degree\": str,\n      \"major\": str,\n      \"institution\": str,\n      \"city\": str,\n      \"start_date\": str,\n      \"end_date\": str,\n      \"gpa\": str\n    }\n  ]\n}\n```",
            "content": ""
        },
        "awards": {
            "prompt": "Extract any awards or recognitions the candidate has received using the following schema:\n\n```json\n{\n  \"awards\": [\n    {\n      \"title\": str,\n      \"date\": str,\n      \"description\": str\n    }\n  ]\n}\n```",
            "content": ""
        },
        "projects": {
            "prompt": "Extract the candidate's projects using the following schema:\n\n```json\n{\n  \"projects\": [\n    {\n      \"title\": str,\n      \"description\": str,\n      \"tools\":[str],\n      \"impact\": str\n    }\n  ]\n}\n```",
            "content": ""
        },
        "skills": {
            "prompt": "Extract the candidate's skills using the following schema:\n\n```json\n{\n  \"skills\": [\n    {\n      \"name\": str,\n      \"keywords\": [str]\n    }\n  ]\n}\n```",
            "content": ""
        },
        "work": {
            "prompt": "Extract the candidate's work experience using the following schema:\n\n```json\n{\n  \"work_experience\": [\n    {\n      \"job_title\": str,\n      \"company_name\": str,\n      \"location\": str,\n      \"start_date\": str,\n      \"end_date\": str,\n      \"responsibilities\": [str]\n    }\n  ]\n}\n```",
            "content": ""
        }
    }

    # Iterate over each section and generate content
    for section_name, section_info in sections.items():
        try:
            prompt = f"{section_info['prompt']}\n\nResume Text:\n{cv_text}"
            response = model.generate_content(prompt)
            print(f"{section_name.capitalize()} Section Response:", response.text)  # Log the response

            # Clean and parse the JSON response
            cleaned_response = clean_response(response.text)
            parsed_json = json.loads(cleaned_response)

            # Update the final JSON
            final_json.update(parsed_json)
        except Exception as e:
            print(f"Error processing section '{section_name}': {e}")
            print(f"Response Text:\n{response.text}")
            continue

    return final_json

def tailor_resume(cv_text, api_key):
    """Tailor a resume using the Harvard Extension School Resume guidelines"""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # System prompt to guide the tailoring of the resume
    system_prompt = (
        "You are a smart assistant to career advisors at the Harvard Extension School. "
        "Your task is to rewrite resumes to be more brief and convincing according to the "
        "Resumes and Cover Letters guide."
    )

    try:
        # Generate the tailored resume
        response = model.generate_content(f"{system_prompt} \nConsider the following CV: {cv_text}")
        print("Tailored Resume Response:", response.text)  # Log tailored response
        return response.text
    except Exception as e:
        print(f"Error tailoring resume: {e}")
        return cv_text
