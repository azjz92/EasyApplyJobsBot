import time
import random
import os
import math
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import config
import utils
import constants


class LinkedinBot:
    def __init__(self):
        utils.prYellow(
            "🤖 Thanks for using Easy Apply Jobs bot, for more information you can visit our site - www.automated-bots.com")
        utils.prYellow("🌐 Bot will run in Chrome browser and log in Linkedin for you.")
        self.driver = self.setup_driver()
        self.wait = WebDriverWait(self.driver, 10)
        self.login()

    def setup_driver(self):
        chrome_options = Options()
        if config.headless:
            chrome_options.add_argument("--headless")

        if config.chromeProfilePath:
            chrome_options.add_argument(f"user-data-dir={config.chromeProfilePath}")

        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)

    def login(self):
        self.driver.get("https://www.linkedin.com/login")
        if not config.chromeProfilePath:
            try:
                self.wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(config.email)
                self.driver.find_element(By.ID, "password").send_keys(config.password)
                self.driver.find_element(By.XPATH, '//button[@type="submit"]').click()
                time.sleep(random.uniform(3, 5))
            except:
                utils.prRed("❌ Couldn't log in Linkedin. Please check your credentials in the config file.")
                self.driver.quit()
                exit()

        self.wait.until(EC.presence_of_element_located((By.XPATH, '//div[@id="global-nav"]')))
        utils.prGreen("✅ Successfully logged in Linkedin!")

    def apply_jobs(self):
        utils.prYellow("🔍 Starting to apply for jobs...")
        self.generate_urls()

        applied_jobs = 0
        total_jobs = 0

        urlData = utils.getUrlDataFile()
        for url in urlData:
            self.driver.get(url)
            time.sleep(random.uniform(1, constants.botSpeed))

            totalJobs = self.driver.find_element(By.XPATH, '//small').text
            totalPages = utils.jobsToPages(totalJobs)

            urlWords = utils.urlToKeywords(url)
            lineToWrite = f"\nCategory: {urlWords[0]}, Location: {urlWords[1]}, Applying {totalJobs} jobs."
            self.displayWriteResults(lineToWrite)

            for page in range(totalPages):
                currentPageJobs = constants.jobsPerPage * page
                url = url + f"&start={currentPageJobs}"
                self.driver.get(url)
                time.sleep(random.uniform(1, constants.botSpeed))

                jobs_on_page = self.wait.until(
                    EC.presence_of_all_elements_located((By.XPATH, '//li[@data-occludable-job-id]')))

                for job in jobs_on_page:
                    total_jobs += 1
                    job_id = job.get_attribute("data-occludable-job-id").split(":")[-1]
                    job_url = f'https://www.linkedin.com/jobs/view/{job_id}'

                    self.driver.execute_script("arguments[0].scrollIntoView();", job)
                    job.click()
                    time.sleep(random.uniform(0.5, 1))

                    job_properties = self.getJobProperties(total_jobs)
                    if "blacklisted" in job_properties:
                        self.displayWriteResults(f"{job_properties} | * 🤬 Blacklisted Job, skipped!: {job_url}")
                        continue

                    if self.is_easy_apply():
                        result = self.apply_to_job(job_url)
                        if "Successfully applied" in result:
                            applied_jobs += 1
                        self.displayWriteResults(f"{job_properties} | {result}")
                    else:
                        self.displayWriteResults(f"{job_properties} | * 🥳 Already applied! Job: {job_url}")

                    time.sleep(random.uniform(0.5, 1))

            utils.prYellow(f"Category: {urlWords[0]}, {urlWords[1]} applied: {applied_jobs} jobs out of {total_jobs}.")

        utils.donate(self)

    def generate_urls(self):
        if not os.path.exists('data'):
            os.makedirs('data')
        try:
            with open('data/urlData.txt', 'w', encoding="utf-8") as file:
                linkedinJobLinks = utils.LinkedinUrlGenerate().generateUrlLinks()
                for url in linkedinJobLinks:
                    file.write(url + "\n")
            utils.prGreen("✅ Apply urls are created successfully, now the bot will visit those urls.")
        except:
            utils.prRed("❌ Couldn't generate urls, make sure you have edited config file line 25-39")

    def is_easy_apply(self):
        try:
            return self.wait.until(EC.presence_of_element_located(
                (By.XPATH, "//button[contains(@class, 'jobs-apply-button')]"))).is_displayed()
        except:
            return False

    def apply_to_job(self, job_url):
        try:
            apply_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'jobs-apply-button')]")))
            apply_button.click()
            time.sleep(random.uniform(0.5, 1))

            try:
                self.chooseResume()
                submit_button = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Submit application']")))
                submit_button.click()
                time.sleep(random.uniform(1, 2))
                return "* 🥳 Successfully applied to this job: " + job_url
            except:
                try:
                    continue_button = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Continue to next step']")))
                    continue_button.click()
                    time.sleep(random.uniform(0.5, 1))
                    self.chooseResume()
                    comPercentage = self.driver.find_element(By.XPATH,
                                                             'html/body/div[3]/div/div/div[2]/div/div/span').text
                    percenNumber = int(comPercentage[0:comPercentage.index("%")])
                    result = self.applyProcess(percenNumber, job_url)
                    return result
                except:
                    self.chooseResume()
                    return "* 🥵 Cannot apply to this Job! " + job_url
        except Exception as e:
            return f"* 🥵 Cannot apply to this Job! {job_url} Error: {str(e)}"

    def chooseResume(self):
        try:
            self.driver.find_element(By.CLASS_NAME, "jobs-document-upload__title--is-required")
            resumes = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'ui-attachment--pdf')]")
            if len(resumes) == 1 and resumes[0].get_attribute("aria-label") == "Select this resume":
                resumes[0].click()
            elif len(resumes) > 1 and resumes[config.preferredCv - 1].get_attribute(
                    "aria-label") == "Select this resume":
                resumes[config.preferredCv - 1].click()
            elif not isinstance(len(resumes), int):
                utils.prRed("❌ No resume has been selected. Please add at least one resume to your Linkedin account.")
        except:
            pass

    def applyProcess(self, percentage, job_url):
        applyPages = math.floor(100 / percentage)
        try:
            for _ in range(applyPages - 2):
                self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Continue to next step']").click()
                time.sleep(random.uniform(0.5, 1))

            self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Review your application']").click()
            time.sleep(random.uniform(0.5, 1))

            if not config.followCompanies:
                try:
                    self.driver.find_element(By.CSS_SELECTOR, "label[for='follow-company-checkbox']").click()
                except:
                    pass

            self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Submit application']").click()
            time.sleep(random.uniform(1, 2))

            return "* 🥳 Successfully applied to this job: " + job_url
        except:
            return "* 🥵 Cannot apply to this Job! " + job_url

    def getJobProperties(self, count):
        textToWrite = str(count) + " | "
        try:
            jobTitle = self.driver.find_element(By.XPATH, "//h1[contains(@class, 'job-title')]").get_attribute(
                "innerHTML").strip()
            textToWrite += jobTitle + " | "
            if any(word.lower() in jobTitle.lower() for word in config.blackListTitles):
                return textToWrite + "(blacklisted title)"
        except:
            textToWrite += "? | "

        try:
            jobDetail = self.driver.find_element(By.XPATH,
                                                 "//div[contains(@class, 'job-details-jobs')]//div").text.replace("·",
                                                                                                                  "|")
            textToWrite += jobDetail + " | "
            if any(word.lower() in jobDetail.lower() for word in config.blacklistCompanies):
                return textToWrite + "(blacklisted company)"
        except:
            pass

        try:
            jobLocation = " | ".join([span.text for span in self.driver.find_elements(By.XPATH,
                                                                                      "//span[contains(@class,'ui-label ui-label--accent-3 text-body-small')]//span[contains(@aria-hidden,'true')]")])
            textToWrite += jobLocation
        except:
            pass

        return textToWrite

    def displayWriteResults(self, lineToWrite: str):
        try:
            print(lineToWrite)
            utils.writeResults(lineToWrite)
        except Exception as e:
            utils.prRed("❌ Error in DisplayWriteResults: " + str(e))


if __name__ == "__main__":
    start = time.time()
    bot = LinkedinBot()
    bot.apply_jobs()
    bot.driver.quit()
    end = time.time()
    utils.prYellow(f"---Took: {round((end - start) / 60)} minute(s).")