import os
import tempfile
import json
# from doc_utils import extract_text_from_upload
from src.templates import generate_latex, template_commands
from src.prompt_engineering import generate_json_resume, tailor_resume
from src.render import render_latex
import PyPDF2
class ResumeGenerator:
    def __init__(self):
        self.gemini_api_key = "AIzaSyAKjQbErgbnknBRZDrp63vAU93CKtiKNz0"  # Use the API key from environment variable
        self.template_options = list(template_commands.keys())

    def process_uploaded_file(self, pdf_path):
        """ Extracts text from the uploaded file (works for both file-like objects and file paths). """
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    text += page_text
        return text
    def generate_resume(self, text, template_name, section_ordering, improve_check=False):
        try:

            # If improve_check is True, tailor the resume with LLM
            if improve_check and self.gemini_api_key:
                print("Tailoring the resume...")
                text = tailor_resume(text, self.gemini_api_key)

            # Convert the extracted text into a JSON resume format
            json_resume = generate_json_resume(text, self.gemini_api_key)
            print("Generated JSON resume:")
            print(json_resume)
            # Generate the LaTeX content based on selected template and sections
            latex_resume = generate_latex(template_name, json_resume, section_ordering)
            
            # Log LaTeX content for inspection
            print("Generated LaTeX content:")
            print(latex_resume)

            # Render the LaTeX content to PDF
            resume_bytes = render_latex(template_commands[template_name], latex_resume)

            if resume_bytes:
                # Return the PDF as bytes
                return resume_bytes
            else:
                raise Exception("Failed to generate PDF. Please check your LaTeX content.")
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
    def generate_resume_from_json(self,json_resume, template_name, section_ordering, improve_check=False):
        try:
            # Generate the LaTeX content based on selected template and sections
            latex_resume = generate_latex(template_name, json_resume, section_ordering)
            
            # Log LaTeX content for inspection
            print("Generated LaTeX content:")
            print(latex_resume)

            # Render the LaTeX content to PDF
            resume_bytes = render_latex(template_commands[template_name], latex_resume)

            if resume_bytes:
                # Return the PDF as bytes
                return resume_bytes
            else:
                raise Exception("Failed to generate PDF. Please check your LaTeX content.")
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def save_resume(self, resume_bytes, file_name="resume.pdf"):
        """ Save the generated PDF to a file. """
        try:
            with open(file_name, 'wb') as f:
                f.write(resume_bytes)
            print(f"Resume saved as {file_name}")
        except Exception as e:
            print(f"Failed to save resume: {e}")

    def save_latex(self, latex_resume, file_name="resume.tex"):
        """ Save the generated LaTeX source to a file. """
        try:
            with open(file_name, 'w') as f:
                f.write(latex_resume)
            print(f"LaTeX source saved as {file_name}")
        except Exception as e:
            print(f"Failed to save LaTeX source: {e}")

    def save_json(self, json_resume, file_name="resume.json"):
        """ Save the generated JSON resume to a file. """
        try:
            with open(file_name, 'w') as f:
                json.dump(json_resume, f, indent=4)
            print(f"JSON resume saved as {file_name}")
        except Exception as e:
            print(f"Failed to save JSON resume: {e}")


# Example usage:

# if __name__ == '__main__':
#     # Example uploaded file (this could be from Streamlit or a manual file input)
#     pdf_path = "/Volumes/PortableSSD/AutoJobsApply/ResuLLMe/src/resume19.pdf"  # Update this path to a valid PDF file
#     # Choose template and section ordering
#     template_name = "Simple"  # Example template name
#     section_ordering = ["education", "work", "skills", "projects", "awards"]

#     # Create an instance of the ResumeGenerator class
#     generator = ResumeGenerator()
#     text = generator.process_uploaded_file(pdf_path)
#     # Generate the resume
#     resume_bytes = generator.generate_resume(text, template_name, section_ordering, improve_check=True)
#     if resume_bytes:
#         # Save the generated resume and other files
#         generator.save_resume(resume_bytes)
#         generator.save_latex("Generated LaTeX content")  # Example usage, replace with actual latex content
#         generator.save_json("Generated JSON content")  # Example usage, replace with actual JSON content

