from ats_score import UpdateResume
from src.resume_generate import ResumeGenerator
class EnhanceResume:
    def __init__(self,job_description,resume_text):
        self.job_description = job_description
        self.resume_text = resume_text
    def update_resume(self):
        udapted_resume = UpdateResume(self.job_description,self.resume_text)
        updated_resume_text = udapted_resume.resume_update()
        template_name = "Simple"
        section_ordering = ["education", "work", "skills", "projects", "awards"]
        generator = ResumeGenerator()
        resume_bytes = generator.generate_resume(updated_resume_text, template_name, section_ordering, improve_check=True)
        if resume_bytes:
            # Save the generated resume and other files
            generator.save_resume(resume_bytes)
            generator.save_latex("Generated LaTeX content")  # Example usage, replace with actual latex content
            generator.save_json("Generated JSON content")  # Example usage, replace with actual JSON content
        return updated_resume_text