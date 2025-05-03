from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ChromeOptions, Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
import time
options = ChromeOptions()
options.add_argument("--disable-gpu")  # Disable GPU acceleration
options.add_argument("--no-sandbox")
options.add_argument("--disable-software-rasterizer")
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("platformName=linux")
options.add_argument("browserName=chrome")
options.add_experimental_option("excludeSwitches", ["enable-automation"])

driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

driver.get("https://corazor-technology.vercel.app/careers/apply/1")  # Replace with actual form URL

seen = set()
questions = []
time.sleep(20)
while True:
    time.sleep(2)  # Give time for next question to appear
    
    # Fetch all visible question blocks
    blocks = driver.find_elements(By.CSS_SELECTOR, ".mb-6")  # Adjust selector
    
    new_blocks = [b for b in blocks if b.text.strip() not in seen]
    if not new_blocks:
        break  # No new question appeared, exit
    
    for block in new_blocks:
        try:
            question_text = block.find_element(By.CSS_SELECTOR, ".mb-2").text.strip()
            input_el = block.find_element(By.CSS_SELECTOR, "input, textarea, select")
            input_type = input_el.get_attribute("type") or input_el.tag_name

            print(f"Found question: {question_text} ({input_type})")
            questions.append((question_text, input_type))
            seen.add(question_text)

            # Trigger next question by simulating input (minimal dummy data)
            if input_type == "text":
                input_el.send_keys("test")
            elif input_type == "radio":
                block.find_element(By.CSS_SELECTOR, "input[type='radio']").click()
            elif input_type == "checkbox":
                block.find_element(By.CSS_SELECTOR, "input[type='checkbox']").click()
            elif input_type == "file":
                input_el.send_keys("/Volumes/PortableSSD/Jobscraper/resume-9.pdf")  # required if it's mandatory
            elif input_type == "select":
                input_el.find_elements(By.TAG_NAME, "option")[1].click()
            else:
                print("Unknown input type, skipping")
        except Exception as e:
            print("Error processing question:", e)

driver.quit()