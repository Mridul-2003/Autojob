import jinja2
import os

# This is a hack to import from doc_utils
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from doc_utils import escape_for_latex

template_commands = {
    "Simple": ["pdflatex", "-interaction=nonstopmode", "resume.tex"],
    "Awesome": ["xelatex", "-interaction=nonstopmode", "resume.tex"],
    "BGJC": ["pdflatex", "-interaction=nonstopmode", "resume.tex"],
    "Deedy": ["xelatex", "-interaction=nonstopmode", "resume.tex"],
    "Modern": ["pdflatex", "-interaction=nonstopmode", "resume.tex"],
    "Plush": ["xelatex", "-interaction=nonstopmode", "resume.tex"],
    "Alta": ["xelatex", "-interaction=nonstopmode", "resume.tex"],
}


def generate_latex(template_name, json_resume, prelim_section_ordering):
    dir_path = os.path.dirname(os.path.realpath(__file__))

    latex_jinja_env = jinja2.Environment(
        block_start_string="\BLOCK{",
        block_end_string="}",
        variable_start_string="\VAR{",
        variable_end_string="}",
        comment_start_string="\#{",
        comment_end_string="}",
        line_statement_prefix="%-",
        line_comment_prefix="%#",
        trim_blocks=True,
        autoescape=False,
        loader=jinja2.FileSystemLoader(dir_path),
    )

    escaped_json_resume = escape_for_latex(json_resume)

    return use_template(
        template_name, latex_jinja_env, escaped_json_resume, prelim_section_ordering
    )


def use_template(template_name, jinja_env, json_resume, prelim_section_ordering):
    PREFIX = f"{template_name}"
    EXTENSION = "tex.jinja"

    resume_template = jinja_env.get_template(f"{PREFIX}/resume.{EXTENSION}")
    basics_template = jinja_env.get_template(f"{PREFIX}/basics.{EXTENSION}")
    education_template = jinja_env.get_template(f"{PREFIX}/education.{EXTENSION}")
    work_template = jinja_env.get_template(f"{PREFIX}/work.{EXTENSION}")
    skills_template = jinja_env.get_template(f"{PREFIX}/skills.{EXTENSION}")
    projects_template = jinja_env.get_template(f"{PREFIX}/projects.{EXTENSION}")
    awards_template = jinja_env.get_template(f"{PREFIX}/awards.{EXTENSION}")

    sections = {}
    section_ordering = get_final_section_ordering(prelim_section_ordering)

    if "basics" in json_resume and len(json_resume["basics"]) > 0:
        basics = json_resume["basics"][0]
        
        # Check for 'first_name' and 'last_name', else split 'name'
        if 'firstname' in basics and 'lastname' in basics:
            firstName = basics.get("firstname", "")
            lastName = basics.get("lastname", "")
        elif 'name' in basics:
            name_parts = basics['name'].strip().split(" ", 1)
            firstName = name_parts[0]
            lastName = name_parts[1] if len(name_parts) > 1 else ""
        else:
            firstName = ""
            lastName = ""
        
        sections["basics"] = basics_template.render(
            firstName=firstName,
            lastName=lastName,
            email=basics.get("email", ""),
            phone=basics.get("phone", ""),
            website=basics.get("website", ""),
            address=basics.get("address", "")
        )

    if "education" in json_resume and len(json_resume["education"]) > 0:
        sections["education"] = education_template.render(
            schools=json_resume["education"], heading="Education"
        )
    if "work_experience" in json_resume and len(json_resume["work_experience"]) > 0:
        sections["work"] = work_template.render(
            works=json_resume["work_experience"], heading="Work Experience"
        )
    if "skills" in json_resume and len(json_resume["skills"]) > 0:
        sections["skills"] = skills_template.render(
            skills=json_resume["skills"], heading="Skills"
        )
    if "projects" in json_resume and len(json_resume["projects"]) > 0:
        sections["projects"] = projects_template.render(
            projects=json_resume["projects"], heading="Projects"
        )

    if "awards" in json_resume:
        valid_awards = [award for award in json_resume["awards"] if award.get("title")]
        if valid_awards:  # Render only if there are awards with valid titles
            sections["awards"] = awards_template.render(
                awards=valid_awards, heading="Awards"
            )
    else:
        sections["awards"] = awards_template.render(
            awards=[], heading="Awards"
        )
        sections["work_experience"] = work_template.render(
            works=[], heading="Work Experience"
        )
        sections["projects"] = projects_template.render(
            projects=[], heading="Projects"
        )
        sections["skills"] = skills_template.render(
            skills=[], heading="Skills"
        )
        sections["education"] = education_template.render(
            schools=[], heading="Education"
        )
        sections["basics"] = basics_template.render(
            firstName="",
            lastName="",
            email="",
            phone="",
            website="",
            address=""
        )

    resume = resume_template.render(
        sections=sections, section_ordering=section_ordering
    )
    return resume



def get_final_section_ordering(section_ordering):
    final_ordering = ["basics"]
    additional_ordering = section_ordering + [
        "education",
        "work",
        "skills",
        "projects",
        "awards",
    ]
    for section in additional_ordering:
        if section not in final_ordering:
            final_ordering.append(section)

    return final_ordering
