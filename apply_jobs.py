from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait,Select
from selenium.common.exceptions import StaleElementReferenceException
import time
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from resume_parse import extract_text_from_pdf
from answer_questions import AnswerQuestions
import re
import os
# Setup Chrome options
options = ChromeOptions()
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-software-rasterizer")
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("platformName=linux")
options.add_argument("browserName=chrome")
options.add_argument("headless=new")
options.add_experimental_option("excludeSwitches", ["enable-automation"])

# Extract resume text
resume_text = extract_text_from_pdf("/Volumes/PortableSSD/Jobscraper/resume-9.pdf")
selenium_host = os.environ.get("SELENIUM_HOST", "selenium")
selenium_grid_url = f"https://selenium-grid-server.onrender.com/wd/hub" # Use "selenium" as the host in docker network
class ApplyJobs:
    def __init__(self,job_url,resume_path):
        # self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        self.driver = webdriver.Remote(
            command_executor=selenium_grid_url,
            options=options
        )
        self.job_url = job_url
        self.resume_path = resume_path
    def signin(self,cover_letter_path=None,cover_letter_text=None,Prefered_work_type=None,Join_immediately=None,Current_location=None):
        max_retries = 3  # Maximum number of retries
        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt + 1} to sign in...")
                self.driver.get("https://corazor-technology.vercel.app/signin")

                # Login
                email = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder='Enter your email']")
                email.clear()
                email.send_keys("gauravsaini905888@gmail.com")
                password = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder='Enter your password']")
                password.clear()
                password.send_keys("Gaurav$05")
                signin_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                signin_button.click()

                # Wait for login success
                wait = WebDriverWait(self.driver, 180)
                wait.until(EC.presence_of_element_located((By.XPATH, "//button[normalize-space()='Logout']")))
                print("Login successful!")
                break  # Exit the loop if login is successful

            except TimeoutException:
                print(f"Login failed on attempt {attempt + 1}. Retrying...")
                if attempt == max_retries - 1:
                    print("Max retries reached. Exiting.")
                    self.driver.quit()
                    return
                time.sleep(5)  # Wait before retrying
            

        # Click on Careers
        time.sleep(10)
        self.driver.find_element(By.XPATH, "//div[normalize-space()='Careers']").click()
        match = re.search(r'/apply/(\d+)', self.job_url)
        if match:
            number = match.group(1)
        wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, f"(//button[@class='mt-6 bg-black text-white w-full py-2 rounded hover:bg-gray-800 transition self-end'][normalize-space()='Apply'])[{number}]"))
        )
        self.driver.find_element(By.XPATH, f"(//button[normalize-space()='Apply'])[{number}]").click()
        time.sleep(3)

        # Begin answering questions
        questions_answered = set()

        while True:
            try:
                # Get question labels
                WebDriverWait(self.driver, 30).until(
    EC.presence_of_element_located((By.TAG_NAME, "label"))
)

                label_elements = self.driver.find_elements(By.TAG_NAME, "label")
                print(f"Found {len(label_elements)} labels")
                new_question_found = False
                
                for label in label_elements:
                    radio_inputs = label.find_elements(By.XPATH, ".//input[@type='radio']")
                    if not radio_inputs:
                        
                        question_text = label.text.strip()
                        if not question_text or question_text in questions_answered:
                            continue
                        print(f"Question: {question_text}")
                        questions_answered.add(question_text)
                        print(f"Questions answered so far: {questions_answered}")

                        new_question_found = True

                        # Handle resume upload
                        if "resume" in question_text.lower() or "upload" in question_text.lower():
                            print("Resume upload question detected.")
                            resume_input = self.driver.find_element(By.XPATH, "//input[@type='file']")
                            resume_input.send_keys(self.resume_path)
                            time.sleep(5)

                        elif "cover letter" in question_text.lower() and "upload" in question_text.lower():
                            print("Cover letter upload question detected")
                            cover_letter_input = self.driver.find_element(By.XPATH, "//input[@type='file']")
                            cover_letter_input.send_keys(cover_letter_path)
                            time.sleep(5)
                            continue
                        # Handle text-based questions
                        elif self.driver.find_elements(By.XPATH, "//input[@type='text' and @placeholder='Enter your answer']") or \
                            self.driver.find_elements(By.XPATH, "//textarea[@placeholder='Enter your answer']"):

                            # Choose correct input field
                            try:
                                input_box = self.driver.find_element(By.XPATH, "//textarea[@placeholder='Enter your answer']")
                            except NoSuchElementException:
                                input_box = self.driver.find_element(By.XPATH, "//input[@type='text' and @placeholder='Enter your answer']")
                            if "cover letter" in question_text.lower():
                                input_box.send_keys(cover_letter_text)
                            elif "current location" in question_text.lower():
                                input_box.send_keys(Current_location)
                            else:

                            # Generate AI response
                                query = f"""You are an AI assistant that helps users answer job application form questions.
                                Use the resume text below to answer professionally.
                                Answer only the job based questions.
                                Resume Text: {resume_text}
                                Question: {question_text}
                                """
                                answer_questions = AnswerQuestions(resume_text)
                                response = answer_questions.generate_content(query)
                                input_box.send_keys(response)
                                print(f"Answer: {response}")
                            time.sleep(2)
                                
                            # Submit
                            submit_button = self.driver.find_element(By.XPATH, "//button[normalize-space()='Submit']")
                            submit_button.click()
                            time.sleep(3)
                        # Handle Select drop down questions
                        elif self.driver.find_elements(By.XPATH,"(//select[@class='w-full border px-4 py-2 rounded focus:outline-none'])[1]"):
                            dropdown = self.driver.find_element(By.XPATH,"(//select[@class='w-full border px-4 py-2 rounded focus:outline-none'])[1]")
                            select = Select(dropdown)
                            list_of_options = [opt.text.strip().lower() for opt in select.options]
                            print(list_of_options)
                            query = f"""You You are an AI assistant that helps users answer job application form questions of selct the answers from options type.
                            Use the resume text below to answer professionally.
                            Select answer from the options provided below.
                            Resume Text: {resume_text}
                            Question: {question_text} 
                            Options: {list_of_options}
                            Give only the answer from the options provided below.not include anything else
                            Example:
                            Options :[0-1,1]
                            Answer: 0-1
                            Options :[0-1,1,2-3]
                            Answer:1
                            Options :[0-1,1,2-3,4-5]
                            Answer:2-3
                            Options :['select', '0-1', '1-3', '3-5', '5+']
                            Answer: 1-3
                            """
                            answer_questions = AnswerQuestions(resume_text)
                            response = answer_questions.generate_content(query)
                            print(response)
                            for attempt in range(3):  # Retry a few times
                                try:
                                    options = select.options  # refetch options
                                    for opt in options:
                                        opt_text_clean = opt.text.strip().lower()
                                        response_clean = response.strip().lower()
                                        if response_clean == opt_text_clean:
                                            print("Matched:", opt.text.strip())
                                            select.select_by_visible_text(opt.text.strip())
                                            break
                                    break  # success
                                except StaleElementReferenceException:
                                    print("Stale element, retrying...")
                            time.sleep(10)
                        #Handle radio button questions
                        elif "join immediately" in question_text.strip().lower():
                            radio_button = self.driver.find_element(By.CSS_SELECTOR, f"input[value={Join_immediately}]")
                            radio_button.click()
                            print("Clicked 'Yes' for join immediately.")
                            break
                        else:
                            radio_button = self.driver.find_element(By.CSS_SELECTOR, f"input[value={Prefered_work_type}]")
                            radio_button.click()
                            print("Radio button clicked for 'Remote'.")
                            break

                                
                            

                            
                            

                if not new_question_found:
                    print("No new questions found or all answered.")
                    break

            except NoSuchElementException:
                print("No more questions to answer or page error.")
                html = self.driver.page_source
                with open("debug.html", "w", encoding="utf-8") as f:
                    f.write(html)
                if "Preferred Work Mode?" in self.driver.page_source:
                    print("Detected: Preferred Work Mode? manually.")

                break

        # Done
        self.driver.quit()

# # Run the automation
# applyjobs = ApplyJobs("https://corazor-technology.vercel.app/careers/apply/1", "/Volumes/PortableSSD/Jobscraper/resume-9.pdf")
# applyjobs.signin()
# Traceback (most recent call last):
#   File "/Volumes/PortableSSD/Jobscraper/jobscrapper/lib/python3.10/site-packages/streamlit/runtime/scriptrunner/exec_code.py", line 121, in exec_func_with_error_handling
#     result = func()
#   File "/Volumes/PortableSSD/Jobscraper/jobscrapper/lib/python3.10/site-packages/streamlit/runtime/scriptrunner/script_runner.py", line 640, in code_to_exec
#     exec(code, module.__dict__)
#   File "/Volumes/PortableSSD/Jobscraper/filter_jobs.py", line 408, in <module>
#     filtered_jobs,non_ats_jobs= filter_data.filter_jobs(job_data, search_term, resume_path)
#   File "/Volumes/PortableSSD/Jobscraper/filter_jobs.py", line 90, in filter_jobs
#     ats_score = updateresume.calculate_ats()
#   File "/Volumes/PortableSSD/Jobscraper/ats_score.py", line 53, in calculate_ats
#     ats_score = json.loads(cleaned_response)
#   File "/Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/json/__init__.py", line 346, in loads
#     return _default_decoder.decode(s)
#   File "/Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/json/decoder.py", line 337, in decode
#     obj, end = self.raw_decode(s, idx=_w(s, 0).end())
#   File "/Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/json/decoder.py", line 355, in raw_decode
#     raise JSONDecodeError("Expecting value", s, err.value) from None
# json.decoder.JSONDecodeError: Expecting value: line 1 column 2 (char 1)
# [DEBUG] Total Top Jobs Fetched: 15
# Gemini Response: No

# [{'ats_score': 75}]
# Gemini Response: No

# [{'ats_score': 75}]
# Gemini Response: No

# [{'ats_score': 70}]
# Gemini Response: No

# [{'ats_score': 75}]
# Gemini Response: No



