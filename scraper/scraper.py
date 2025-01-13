from selenium import webdriver
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
    state: Literal["init", "mainmenu", "form", "examresults", "other"] = "init"

    def __init__(self):
        self.start()

    def navigateSite(self):
        while True:
            match self.state:
                case "init":
                    self.attemptLogin()
                case "mainmenu":
                    ...
                case "examresults":
                    ...
                case "other":
                    print("Confused state. Quitting and restarting the browser.")
                    self.quit()
                    self.start()

    def determineState(self):
        if self.isInLogin():
            self.state = "init"
        elif self.isInForm():
            self.state = "form"
        elif self.isInMainmenu():
            self.state = "mainmenu"
        elif self.isInExamResults():
            self.state = "examresults"
        else:
            self.state = "other"

    def isInLogin(self):
        try:
            self.browser.find_element("css selector", "#recover")
            return True
        except Exception:
            return False

    def isInForm(self):
        try:
            self.browser.find_element("xpath", "/html/body/div[16]")
            return True
        except Exception:
            return False

    def isInMainmenu(self):
        try:
            self.browser.find_element("css selector", "#column")
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
        elements["username"].send_keys()
        elements["password"].send_keys()
        image = np.array(
            Image.open(io.BytesIO(elements["captcha_photo"].screenshot_as_png))
        )
        solver = s.CaptchaSolver(image)
        result = solver.solve_captcha()
        elements["captcha"].send_keys(str(result))
        elements["login"].click()

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

    def quit(self):
        self.browser.quit()
        self.browser = None
        self.state = "init"

    def start(self):
        browser = webdriver.Firefox()
        browser.get(OBS_LOGIN_URL)
        self.browser = browser

    def __del__(self):
        self.quit()


class CaptchaScraper(OBSScraper):
    def __init__(self):
        super().__init__()

    def getCaptchas(amount=100): ...


if __name__ == "__main__":
    x = OBSScraper()
    x.attemptLogin()
