from resume_parse import ResumeParse
class GenerateCoverLetter:
    def __init__(self,resume_text,job_description):
        self.resume_text = resume_text
        self.job_description = job_description
    def generate_cover_letter(self):
        parse = ResumeParse(self.resume_text,self.job_description)
        cover_letter_prompt = """
        you are a professional mentor who helps people to generate and create a professional cover letter based on given resume_text and jobs descriptions .

        your task is to create a cover letter mentioning why should the company hire them , why he's a good fit and persuade the company to hire him.

        extract the name , experience , qualities skills and other details from the resume only .

        Example:

        Dear Hiring manager,
        I am really interested in Full-Stack Blockchain Developer role. My academic journey at the University School of Automation and Robotics has equipped me with a robust foundation in Artificial Intelligence and Data Science. Throughout the past two years, I have honed my skills in full-stack web development, Web3, and Machine Learning. Proficient in languages such as Solidity, SCrypt, Python, C, and Java, coupled with a deep understanding of blockchain technologies, I am well-prepared to bring value to your internship program.
        In my recent role as a Blockchain Intern at SimplyFi, I actively contributed to the development of DMCC, a metaverse project integrated with a Hyperledger backend. Additionally, my experience as a Full Stack Blockchain Intern at Prodigal AI involved working on projects like Algosage, where I used Solidity, Typescript, Postgres SQL, and Next.js. My role in managing smart contract functionality and developing Solidity connectors for various protocols in the LayerDapp project showcases my versatility in the blockchain domain.
        Furthermore, my leadership as a Blockchain Developer Lead at SkyHi, where I worked on an NFT-based game using technologies like Flutter, Truffle, Hardhat, Solidity, and others, reflects my ability to lead and contribute to innovative projects.
        What specifically draws me to GGSIPU's Internship Program is its commitment to providing interns with autonomy in choosing projects, refining skills, and collaborating with diverse teams. This aligns seamlessly with my desire to deepen my understanding of Blockchain Core Engineering, Cryptography Research, DevOps, Security, L2 Tooling, and DeFi Research C Development.
        The projects I have undertaken, such as Algosage, SkyHi, SmartDraw, and LayerDapp, showcase my hands-on experience in building practical solutions and underscore my commitment to the field. Additionally, my participation in the Microsoft Learn Student Ambassador program, where I achieved recognition for ambassador projects globally and served as a mentor in cybersecurity and Blockchain, highlights my dedication to continuous learning and knowledge sharing.
        I am enthusiastic about the opportunity to contribute to the organization’s vision and to learn from the talented professionals on your team. I believe that my technical skills, project experience, and enthusiasm for blockchain technology makes me a valuable candidate for this internship.
        Sincerely, Anant Jain 8700943798

        Important things :

        NOTE 1: in case of students and no experience , modify the cover letter accordingly

        NOTE 2: don't mention "Platform where you found the job posting" as we don't know where we find the listing and posting exactly .

        NOTE 3: If user has any experience with company , then mention that specific company name 


        """

        output5 = parse.parse_work_experience(cover_letter_prompt)
        formatted_text = " ".join(line.strip() for line in output5.splitlines())
        
        # Replace multiple spaces with a single space
        formatted_text = " ".join(formatted_text.split())
        result = {"Cover_Letter":formatted_text}
        return result
# resume_text = """

# 1
# Mridul Mittal +91-9667677092
# Bachelor of Technology mridulmittal2003@gmail.com
# Artificial Intelligence and Data Science GitHub
# Guru Gobind Singh Indraprastha University, Delhi Kaggle
# Enrollment No: 08419011921 LinkedIn
# Education
# •Bachelor of Technology in Artificial Intelligence and Machine Learning July 2021 - July 2025
# UNIVERSITY SCHOOL OF AUTOMATION AND ROBOTICS, Surajmal Vihar, New Delhi CGPA: 8.493
# •Intermediate July 2020 - July 2021
# Ramjas School, Pusa Road, Delhi Percentage: 82
# Personal Projects
# •Automatic Text Summarization and Language Translation
# Python, TextRank, Google Translate
# –Implemented a TextRank-based algorithm using the ’gensim’ library, improving keyword extraction efficiency by
# 40% and reducing content processing time by 20 hours monthly.
# •Pizza Messiness Score Calculator
# Python, OpenCV, MediaPipe, CNN, Transfer Learning
# –Developed an innovative ’Pizza Messiness Score Calculator’ using OpenCV and MediaPipe.
# –Deployed a CNN model, achieving 95% accuracy in pizza classification and reducing manual identification time by
# 70%.
# •Machine Translation using Seq2Seq Model
# NLP, Deep Learning, RNN, LSTM, TensorFlow
# –Built a Seq2Seq model for machine translation of resumes between languages, improving accessibility for global
# job markets.
# Experience
# •Corazor Technology Private Limited March 2024 - Present
# AI Intern Remote
# –Gained expertise in Azure ML Studio, data storage, and related tools.
# –Engineered an AI-driven recommendation system leveraging NLP algorithms and Microsoft Azure, leading to a
# notable 40 percent reduction in customer churn through tailored product suggestions based on previous purchasing
# behavior.
# –Developed AI algorithms for a truck tracking system using Python and Google Maps API.
# –Created Flask API for findid Nearby Workers and Navigating Workers.
# –Working on Automated Lead Generations using Selenium.
# •The Moronss June 2024 - September 2024
# ML and AI Intern Hybrid
# –Developing AI/ML solutions for an Applicant Tracking System (ATS).
# –Created an automated question generation system for personalized test preparation.
# –Collaborating on projects to enhance student employability.
# Technical Skills and Interests
# Languages: C/C++, Python, Javascript, HTML+CSS
# Libraries: TensorFlow, Scikit-learn, OpenCV, Keras, pandas, numpy, matplotlib, MediaPipe
# Web Dev Tools: VScode, Git, GitHub
# Frameworks: Flask, Django
# Cloud/Databases: MongoDB, Microsoft Azure, MySQL
# Relevant Coursework: Data Structures, Algorithms, Operating Systems, OOP, DBMS, Software
# Engineering, Machine Learning, Deep Learning, Neural Networks, NLP, Computer Vision, Agile Testing
# Additional Skills: Large Language Models (LLM), Retrieval-Augmented Generation (RAG),
# Hyperparameter Tuning, JIRA, Manual Testing, Automated Testing
# Areas of Interest: Web Development, Artificial Intelligence, Generative AI
# Positions of Responsibility
# •Open Source CoordinatorGoogle Developer Students Club USAR August 2023 - September 2024
# –Contributed to open-source projects within the Google Developer Students Club.

# """
# result = GenerateCoverLetter(resume_text, "Assist marketing team with campaigns and research.").generate_cover_letter()

# print(result)