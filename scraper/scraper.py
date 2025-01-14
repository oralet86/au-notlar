from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from typing import Literal
from PIL import Image
import numpy as np
import io
from ocr import solver as s

OBS_LOGIN_URL = "https://obs.ankara.edu.tr/Account/Login"


class ScraperManager:
    instances = []


class OBSScraper:
    browser: webdriver.Firefox = None
    state: Literal["init", "mainmenu", "form", "examresults"] = "init"
    results = None

    def __init__(self, label: str, username: str, password: str):
        self.label = label
        self.username = username
        self.password = password
        self.start()

    def navigateSite(self) -> None:
        while True:
            self.determineState()
            try:
                match self.state:
                    case "init":
                        self.attemptLogin()
                    case "form":
                        self.closeForm()
                    case "mainmenu":
                        self.enterResultsPage()
                    case "examresults":
                        self.extractResults()
                        return self.results
            except Exception as e:
                print(e)
                self.browser.refresh()

    def determineState(
        self,
    ) -> Literal["init", "mainmenu", "form", "examresults"]:
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
        self.wait.until(
            EC.visibility_of_element_located(
                ("xpath", "/html/body/div[16]/div[3]/div/button")
            )
        )

    def getLoginElements(self):
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
        button_1 = self.browser.find_element(
            "xpath", "/html/body/div[8]/div[1]/ul/li[1]/a"
        )
        button_1.click()
        button_2 = self.browser.find_element(
            "xpath", "/html/body/div[8]/div[1]/ul/li[1]/ul/li[2]/a"
        )
        button_2.click()
        button_3 = self.browser.find_element(
            "xpath", "/html/body/div[8]/div[1]/ul/li[1]/ul/li[2]/ul/li[4]/a"
        )
        button_3.click()
        self.wait.until(
            EC.visibility_of_element_located(("xpath", '//*[@id="btnToggle"]'))
        )

    def extractResults(self):
        open_all = self.browser.find_element("xpath", '//*[@id="btnToggle"]')
        open_all.click()

        lessons = self.browser.find_elements(
            "css selector", "table.student-lesson-list"
        )

        for lesson in lessons:
            lesson.find_elements(
                "css selector",
            )

    def quit(self):
        self.browser.quit()
        self.browser = None
        self.state = "init"

    def start(self):
        browser = webdriver.Firefox()
        browser.get(OBS_LOGIN_URL)
        self.browser = browser
        self.wait = WebDriverWait(self.browser, 5)

    def __del__(self):
        self.quit()


class CaptchaScraper(OBSScraper):
    def __init__(self):
        super().__init__()

    def getCaptchas(amount=100): ...


if __name__ == "__main__":
    ...
