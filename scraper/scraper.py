from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from typing import Literal
from PIL import Image
import numpy as np
import io
from ocr import solver as s
from global_variables import logger, OBS_LOGIN_URL


class OBSScraper:
    browser: webdriver.Firefox = None
    state: Literal["init", "mainmenu", "form", "examresults", "recaptcha"] = "init"
    results = None

    def __init__(self, label: str, username: str, password: str):
        logger.info(f"{label}: Initializing OBSScraper.")
        self.label = label
        self.username = username
        self.password = password

    def navigateSite(self) -> None:
        while True:
            logger.info(f"{self.label}: Navigating site..")
            self.determineState()
            try:
                match self.state:
                    case "recaptcha":
                        logger.info(
                            "ReCAPTCHA detected. Shutting the browser down and rebooting."
                        )
                        self.stop()
                        self.start()
                        continue
                    case "init":
                        self.attemptLogin()
                    case "form":
                        self.closeForm()
                    case "mainmenu":
                        self.enterResultsPage()
                    case "examresults":
                        return
            except Exception as e:
                logger.info(f"{self.label}: Exception while navigating site! {e}")
                self.browser.refresh()

    def determineState(
        self,
    ) -> Literal["init", "mainmenu", "form", "examresults", "recaptcha"]:
        logger.info(f"{self.label}: Determining state.. ")
        if self.isReCaptcha():
            self.state = "recaptcha"
        if self.isInLogin():
            self.state = "init"
        elif self.isInForm():
            self.state = "form"
        elif self.isInMainmenu():
            self.state = "mainmenu"
        elif self.isInExamResults():
            self.state = "examresults"
        else:
            raise Exception("Unknown state.")
        return self.state

    def isReCaptcha(self):
        try:
            self.browser.find_element("css selector", ".g-recaptcha")
            return True
        except Exception:
            return False

    def isInLogin(self):
        try:
            self.browser.find_element("css selector", "#recover")
            return True
        except Exception:
            return False

    def isInForm(self):
        try:
            form = self.browser.find_element("xpath", "/html/body/div[16]")
            form_bool = form.is_displayed()
            return form_bool
        except Exception:
            return False

    def isInMainmenu(self):
        try:
            self.browser.find_element("css selector", "#column-1")
            return True
        except Exception:
            return False

    def isInExamResults(self):
        try:
            self.browser.find_element("css selector", "#confirmationReport-list")
            return True
        except Exception:
            return False

    def attemptLogin(self):
        logger.info(f"{self.label}: Attempting to log in..")
        elements = self.getLoginElements()
        elements["username"].clear()
        elements["username"].send_keys(self.username)
        elements["password"].clear()
        elements["password"].send_keys(self.password)
        image = np.array(
            Image.open(io.BytesIO(elements["captcha_photo"].screenshot_as_png))
        )
        solver = s.CaptchaSolver(image)
        result = solver.solve_captcha()
        if result is None:
            self.browser.refresh()
            return
        elements["captcha"].clear()
        elements["captcha"].send_keys(str(result))
        elements["login"].click()

    def getLoginElements(self):
        logger.info(f"{self.label}: Getting login elements..")
        self.wait.until(
            EC.presence_of_element_located(("css selector", "#OtherUsername"))
        )
        username_input = self.browser.find_element("css selector", "#OtherUsername")
        password_input = self.browser.find_element("css selector", "#OtherPassword")
        captcha_photo = self.browser.find_element(
            "xpath", "/html/body/div[4]/form/div[4]/img"
        )
        captcha_input = self.browser.find_element("css selector", "#Captcha")
        login_button = self.browser.find_element("css selector", "#btnSend")

        return {
            "username": username_input,
            "password": password_input,
            "captcha_photo": captcha_photo,
            "captcha": captcha_input,
            "login": login_button,
        }

    def closeForm(self):
        logger.info(f"{self.label}: Closing form..")
        self.wait.until(
            EC.presence_of_element_located(
                ("xpath", "/html/body/div[16]/div[3]/div/button")
            )
        )
        form_button = self.browser.find_element(
            "xpath", "/html/body/div[16]/div[3]/div/button"
        )
        self.wait.until(
            EC.element_to_be_clickable(
                ("xpath", "/html/body/div[16]/div[3]/div/button")
            )
        )
        self.wait.until(EC.invisibility_of_element(("xpath", "/html/body/div[1]")))
        form_button.click()
        self.wait.until(
            EC.invisibility_of_element(
                ("xpath", "/html/body/div[16]/div[3]/div/button")
            )
        )

    def enterResultsPage(self):
        logger.info(f"{self.label}: Entering the exam results page..")
        self.wait.until(
            EC.visibility_of_element_located(
                ("xpath", "/html/body/div[8]/div[1]/ul/li[1]/a")
            )
        )
        button_1 = self.browser.find_element(
            "xpath", "/html/body/div[8]/div[1]/ul/li[1]/a"
        )
        button_1.click()
        self.wait.until(
            EC.visibility_of_element_located(
                ("xpath", "/html/body/div[8]/div[1]/ul/li[1]/ul/li[2]/a")
            )
        )
        button_2 = self.browser.find_element(
            "xpath", "/html/body/div[8]/div[1]/ul/li[1]/ul/li[2]/a"
        )
        button_2.click()
        self.wait.until(
            EC.visibility_of_element_located(
                ("xpath", "/html/body/div[8]/div[1]/ul/li[1]/ul/li[2]/ul/li[4]/a")
            )
        )
        button_3 = self.browser.find_element(
            "xpath", "/html/body/div[8]/div[1]/ul/li[1]/ul/li[2]/ul/li[4]/a"
        )
        button_3.click()

    def extractResults(self):
        logger.info(f"{self.label}: Extracting exam results..")
        self.wait.until(
            EC.visibility_of_element_located(("xpath", '//*[@id="btnToggle"]'))
        )
        results = []
        open_all = self.browser.find_element("xpath", '//*[@id="btnToggle"]')
        open_all.click()

        lesson_table = self.browser.find_element(
            "xpath", "/html/body/div[8]/div[4]/div[5]/form/table/tbody"
        )

        # Get the necessary elements from the lesson table
        normal_tr_tags = lesson_table.find_elements(
            "css selector", "#confirmationReport-list > tbody > tr:not(.sub-tr)"
        )
        subtr_tr_tags = lesson_table.find_elements(
            "css selector", "#confirmationReport-list > tbody > tr.sub-tr"
        )
        try:
            surveys = lesson_table.find_elements("css selector", "a.noteview-survey")
        except Exception:
            surveys = []

        logger.info(
            f"{self.label}: Survey amount: {len(surveys)}, <tr> amount: {len(normal_tr_tags)}, <tr.subtr> amount: {len(subtr_tr_tags)}"
        )
        assert len(normal_tr_tags) - len(surveys) == len(subtr_tr_tags)

        # Go through each lecture and extract the available exam data
        survey_count = 0
        for i in range(len(normal_tr_tags)):
            lesson_information = {"name": None, "exams": []}
            lesson_information["name"] = (
                normal_tr_tags[i]
                .find_element(
                    "css selector",
                    "#confirmationReport-list > tbody > tr > td:nth-child(1)",
                )
                .text
            )
            is_surveyed = False
            try:
                surveys = normal_tr_tags[i].find_element(
                    "css selector",
                    "#confirmationReport-list > tbody > tr > td.textC > a.noteview-survey",
                )
                # If an element is found, that means there is a survey.
                # Which means exam data must be extracted a different way.
                is_surveyed = True
                survey_count += 1
            except Exception:
                # If no element is found, we can proceed as normal.
                ...
            # logger.info(f"Lesson Name: {lesson_information['name']}, Survey: {is_surveyed}, Survey Count: {survey_count}, i - survey_count = {i - survey_count}")
            if is_surveyed:
                lesson_information["exams"].append(
                    {
                        "name": "Harf Notu / Letter Grade",
                        "percentage": "%100",
                        "date": normal_tr_tags[i]
                        .find_element(
                            "css selector",
                            "#confirmationReport-list > tbody > tr > td:nth-child(3)",
                        )
                        .text,
                    }
                )
            else:
                try:
                    subtr_info = subtr_tr_tags[i - survey_count].find_elements(
                        "xpath",
                        ".//td[2]/table/tbody/tr[count(*) > 1]",
                    )
                except Exception:
                    logger.info(
                        f"No exam info found for \"{lesson_information['name']}\""
                    )
                    subtr_info = []

                for subtr in subtr_info:
                    lesson_information["exams"].append(
                        {
                            "name": subtr.find_element(
                                "css selector", "td:nth-child(1)"
                            ).text,
                            "percentage": subtr.find_element(
                                "css selector", "td:nth-child(3)"
                            ).text,
                            "date": subtr.find_element(
                                "css selector", "td:nth-child(4)"
                            ).text,
                        }
                    )
            # print(lesson_information)
            results.append(lesson_information)
        self.results = results

    def stop(self):
        logger.info(f"{self.label}: Quitting the scraper..")
        if self.browser is not None:
            self.browser.quit()
            self.browser = None
        self.state = "init"

    def start(self):
        logger.info(f"{self.label}: Starting the scraper..")
        browser = webdriver.Firefox()
        browser.get(OBS_LOGIN_URL)
        self.browser = browser
        self.wait = WebDriverWait(self.browser, 5)

    def refresh(self):
        self.browser.refresh()

    def __del__(self):
        self.stop()


if __name__ == "__main__":
    ...
