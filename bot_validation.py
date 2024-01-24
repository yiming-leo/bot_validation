import re
import time

from PIL import Image
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import main
from SqlParse import SqlParse
from TelMsgRcv import TelMsgRcv


# ----------3.去haodf用户注册网站注册---------------
class CrackGeetest:

    def __init__(self, fake_phone, fake_password, register_url, temp_token):
        self.browser = webdriver.Chrome()
        self.url = register_url
        self.fake_password = fake_password
        self.fake_phone = fake_phone
        self.temp_token = temp_token
        self.tel_msg_rcv = TelMsgRcv()

        self.sql_parse_instance = main.sql_parse_instance

    def crack(self):
        self.browser.get(self.url)  # 访问网址
        time.sleep(2)
        print(f"url访问成功")
        tel_input = self.browser.find_element(By.XPATH, '//input[@class="input"]')
        tel_input.send_keys(self.fake_phone)
        send_code = self.browser.find_element(By.XPATH, '//button[@class="sendCode"]')
        send_code.click()
        print(f"请求验证成功")
        element = WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='geetest_panel geetest_wind']"))
        )
        time.sleep(3)
        print(f"element: {element}")
        style_attribute = element.get_attribute("style")
        print(f"style_attribute: {style_attribute}")
        if "display: block; opacity: 1;" in style_attribute:
            print("Style attribute matches the expected value!")
            self.login()
        else:
            print(f"element错误")
            self.crack()

    def login(self):
        print(f"getting in login")
        # ---------------------------4.获取图片（层级：滑块>缺口背景>满背景）-------------------------------
        # 删除滑块图片
        slider_element = self.browser.find_element(By.XPATH, '//canvas[@class="geetest_canvas_slice geetest_absolute"]')
        slider_element.screenshot('slider.png')
        gap_img_element = self.browser.find_element(By.XPATH, '//canvas[@class="geetest_canvas_bg geetest_absolute"]')
        gap_img_element.screenshot('gap.png')
        self.set_slider_opacity_0(slider_element)
        # 删除缺口图片
        self.set_gapbg_opacity_0(gap_img_element)
        # 修改 canvas 元素的 style 属性
        self.set_fullbg_opacity_1()
        # 拍张full bg照片
        (self.browser.find_element(By.XPATH, '//*[@class="geetest_canvas_fullbg geetest_fade geetest_absolute"]')
         .screenshot('full.png'))
        # 修改 canvas 元素的 style 属性
        self.set_fullbg_display_none()
        # 把他们删除的的都加回来
        self.add_slide_png(slider_element)
        self.add_gap_png(gap_img_element)
        # 执行滑块操作
        print(f"slider_element: {slider_element}")
        # 传统像素检测
        gap_pos = self.detect_diff_img()
        gap_pos -= 5
        # ----------------------------------拖动按钮拼合验证---------------------------------
        slider_btn = self.browser.find_element(By.XPATH, '//*[@class="geetest_slider_button"]')
        self.perform_move(slider_btn, gap_pos)
        # 检测是否通过验证，如果没通过，那就使用验证码刷新按钮，重新获取图片重新点按钮
        self.validate_failed_try_again()
        # ----------------------------------5.先等待短信发送25s-----------------------------
        time.sleep(25)
        # 点击提取与输入短信
        self.inject_input_val_msg()
        # 保存手机号和手机状态到mysql
        self.save_phone()
        # 点击设置密码
        self.input_password(self.fake_password)
        self.click_submit()  # 没被注册，继续点击其他按钮，完成剩余注册
        time.sleep(10000)
        print(f"结束")

    # -------------------------------------------组件-----------------------------------
    # 保存手机号、密码、手机状态码到mysql
    def save_phone(self):
        # 调用main程序
        self.init_processor.save_fake_phone_to_mysql(self.fake_phone, self.fake_password, 0)

    # 剩余操作, 点击输入短信
    def inject_input_val_msg(self):
        # 去接码平台调用收取验证码API，得到验证消息内容
        msg_ver_code_text = self.tel_msg_rcv.get_msg(self.temp_token, self.fake_phone)
        # 提取验证消息内容，拿到验证码
        match = re.search(r'\b\d{6}\b', msg_ver_code_text)
        verification_code = ""
        if match:
            verification_code = match.group()
            print("提取到的验证码:", verification_code)
        else:
            print("未找到6位数字验证码")
        # 将验证码输入到输入框内
        val_msg_input = self.browser.find_element(By.XPATH, '//input[@type="text"]')
        val_msg_input.send_keys(verification_code)
        print(f"password inputted...")
        time.sleep(0.2)

    # 点击注册
    def click_submit(self):
        self.browser.find_element(By.XPATH, '//button[@class="submit"]')
        print(f"submit btn clicked...")

    # 仅输入密码
    def input_password(self, password):
        password_input = self.browser.find_element(By.XPATH, '//input[@type="password"]')
        password_input.send_keys(password)
        print(f"password inputted...")
        time.sleep(0.2)

    def set_slider_opacity_0(self, slider_element):
        self.browser.execute_script("""
                    var element = arguments[0];
                    element.style.opacity = '0';
                """, slider_element)
        print("==>1: remove slider_element")
        time.sleep(0.5)

    def set_gapbg_opacity_0(self, gap_img_element):
        self.browser.execute_script("""
                    var element = arguments[0];
                    element.style.opacity = '0';
                """, gap_img_element)
        print("==>2: remove gap_img_element")
        time.sleep(0.5)

    def set_fullbg_opacity_1(self):
        self.browser.execute_script("""
                var canvasElement = document.querySelector('.geetest_canvas_fullbg.geetest_fade.geetest_absolute');
                if (canvasElement) {
                    canvasElement.setAttribute('style', 'opacity: 1;');
                    return 'set success';
                }else {
                    return 'style element_not_found';
                }
                """)
        print("==>3: modify style: display->X")
        time.sleep(0.5)

    def set_fullbg_display_none(self):
        self.browser.execute_script("""
                        var canvasElement = document.querySelector('.geetest_canvas_fullbg.geetest_fade.geetest_absolute');
                        if (canvasElement) {
                            canvasElement.setAttribute('style', 'display: none; opacity: 1;');
                            return 'set success';
                        }else {
                            return 'style element_not_found';
                        }
                        """)
        print("==>3: add style: display->none")
        time.sleep(0.5)

    # 传统图片像素检测
    def detect_diff_img(self):
        image_a = Image.open('full.png').convert('RGB')  # 打开原始图片
        image_b = Image.open('gap.png').convert('RGB')  # 打开有缺口的图片
        gap_pos = self.get_gap(image_a, image_b, 60)
        print(f"gap_pos: {gap_pos}")
        return gap_pos

    # 将缺口图片的透明度设置为不透明（1）
    def add_gap_png(self, gap_img_element):
        self.browser.execute_script("""
                            var element = arguments[0];
                            element.style.opacity = '1';
                        """, gap_img_element)
        print("==>1: create element: gap_png")
        time.sleep(0.5)

    # 将滑块图片的透明度设置为不透明（1）
    def add_slide_png(self, slider_element):
        self.browser.execute_script("""
                    var element = arguments[0];
                    element.style.opacity = '1';
                """, slider_element)
        print("==>2: create element: slide_png")
        time.sleep(0.5)

    def perform_move(self, slider_btn, gap_pos):
        time.sleep(3)
        action = webdriver.ActionChains(self.browser)  # 启动Selenium的动作链
        action.move_to_element(slider_btn)  # 将鼠标移动到元素上
        action.click_and_hold(slider_btn)  # 按住滑动按钮不松开
        action.pause(0.2)
        action.move_by_offset(gap_pos - 10, 0)
        action.pause(0.6)
        action.move_by_offset(10, 0)
        action.pause(0.6)
        action.release().perform()  # 释放滑块

    def validate_failed_try_again(self):
        time.sleep(2)
        val_element = self.browser.find_element(By.XPATH, '//*[@class="geetest_panel geetest_wind"]')
        style_value = val_element.get_attribute("style")  # 获取元素的 style 属性值
        if "display: block; opacity: 1;" in style_value:
            val_refresh_btn = self.browser.find_element(By.XPATH, "//a[@class='geetest_refresh_1']")
            val_refresh_btn.click()
            self.login()

    def is_pixel_equal(self, image1, image2, x, y, threshold):
        # 取两个图片的像素点
        pixel1 = image1.load()[x, y]
        pixel2 = image2.load()[x, y]
        threshold = threshold
        if abs(pixel1[0] - pixel2[0]) < threshold and abs(pixel1[1] - pixel2[1]) < threshold and abs(
                pixel1[2] - pixel2[2]) < threshold:
            return True
        else:
            return False

    def get_gap(self, image1, image2, threshold):
        left = 60
        for i in range(left, image1.size[0]):
            for j in range(image1.size[1]):
                if not self.is_pixel_equal(image1, image2, i, j, threshold):
                    left = i
                    return left
        return left
