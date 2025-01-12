from selenium import webdriver

OBS_LOGIN_URL = "https://obs.ankara.edu.tr/Account/Login"

browser = webdriver.Firefox()

browser.get(OBS_LOGIN_URL)

username_input = browser.find_element("css selector", "#OtherUsername")
password_input = browser.find_element("css selector", "#OtherPassword")
captcha_input = browser.find_element("css selector", "#Captcha")
login_button = browser.find_element("css selector", "#btnSend")

with open('filename.png', 'wb') as file:
  file.write(browser.find_element("xpath", "/html/body/div[4]/form/div[4]/img").screenshot_as_png)

browser.quit()