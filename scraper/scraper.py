from selenium import webdriver

OBS_LOGIN_URL = "https://obs.ankara.edu.tr/Account/Login"

class ScraperManager:
  instances = []

class OBSScraper:
  browser: webdriver.Firefox = None
  state = "init"

  def __init__(self):
    browser = webdriver.Firefox()
    browser.get(OBS_LOGIN_URL)
    self.browser = browser
    
  def getLoginElements(self):
    username_input = self.browser.find_element("css selector", "#OtherUsername")
    password_input = self.browser.find_element("css selector", "#OtherPassword")
    captcha_photo = self.browser.find_element("xpath", "/html/body/div[4]/form/div[4]/img")
    captcha_input = self.browser.find_element("css selector", "#Captcha")
    login_button = self.browser.find_element("css selector", "#btnSend")
    
    return {"username": username_input, "password": password_input, "captcha_photo": captcha_photo, "captcha": captcha_input, "login": login_button}

  browser.quit()
  
if __name__ == "__main__":
  x = OBSScraper()