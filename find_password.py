import time

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By


class CrackRegistered:

    def __init__(self, fake_phone, reset_password_url):
        self.browser = webdriver.Chrome()
        self.url = reset_password_url
        self.fake_phone = fake_phone

    def detect_is_registered(self):
        self.browser.get(self.url)
        time.sleep(2)
        phone_input = self.browser.find_element(By.XPATH, '//input[@id="contact"]')
        phone_input.send_keys(self.fake_phone)
        next_step_btn = self.browser.find_element(By.XPATH, '//input[@type="button"]')
        next_step_btn.click()
        print(f"探测成功，等待页面执行")
        time.sleep(2)

        try:
            self.browser.find_element(By.XPATH, '//div[@id="js-mask"]')
            print(f"元素已找到，电话未注册过，可用")
            return True
        except NoSuchElementException:
            print("元素已找到，电话注册过，不可用，请重新生成")
            return False
