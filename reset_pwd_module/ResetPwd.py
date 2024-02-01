import re
import time

from PIL import Image
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from TelMsgRcv import TelMsgRcv


class ResetPassword:
    def __init__(self, fake_phone, fake_password, reset_password_url, temp_token, sql_parse_instance,
                 selenium_remote_driver_url):
        chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument('remote')
        # self.browser = webdriver.Remote(command_executor=selenium_remote_driver_url, options=chrome_options)
        self.browser = webdriver.Chrome()

        self.tel_msg_rcv = TelMsgRcv()

        self.selenium_remote_driver_url = selenium_remote_driver_url
        self.url = reset_password_url
        self.fake_phone = fake_phone
        self.fake_password = fake_password
        self.reset_password_url = reset_password_url
        self.temp_token = temp_token
        self.sql_parse_instance = sql_parse_instance

    def reset_account_password(self):
        self.browser.get(self.url)
        time.sleep(2)
        phone_input = self.browser.find_element(By.XPATH, '//input[@id="contact"]')
        phone_input.send_keys(self.fake_phone)
        next_step_btn = self.browser.find_element(By.XPATH, '//input[@type="button"]')
        next_step_btn.click()
        print(f"探测成功，等待页面执行")
        time.sleep(2)
        # 这里可能会出现图片验证
        element = WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='geetest_panel geetest_wind']"))
        )
        time.sleep(3)
        style_attribute = element.get_attribute("style")
        print(f"style_attribute: {style_attribute}")
        if "display: block; opacity: 1;" in style_attribute:
            print("element正确，需要执行验证拼图操作")
            self.parse_img_val()
        else:
            print(f"element错误，无需执行验证拼图操作")
        # --------------------这里通过了拼图验证操作，到了需要氪金提取验证码输入验证码的截断--------------------------
        rcv_msg = self.inject_val_msg(1)  # 提取短信
        if not rcv_msg:
            return False  # ------------->>执行结果<<-------------
        self.input_val_msg(rcv_msg)  # 输入短信验证码
        # ------------------点击下一步，看看验证码是否正确-------------------------
        time.sleep(2)
        # next_step_btn = self.browser.find_element('//div[@class="content js-send-ver-code"]/div[@class="button"]')
        button_selector = ".button"  # 请根据实际情况提供正确的选择器
        script = f'document.querySelector("{button_selector}").click();'
        self.browser.execute_script(script)
        # next_step_btn.click()
        time.sleep(5)
        # -------------------现在到了repeat密码的地方----------------------
        script = f'document.querySelector(\'input[placeholder="输入新密码"]\').value = "{self.fake_password}";'
        self.browser.execute_script(script)
        # input_frame_1 = self.browser.find_element('//input[@placeholder="输入新密码"]')
        # input_frame_1.send_keys(self.fake_password)
        time.sleep(5)
        script = f'document.querySelector(\'input[placeholder="再次输入新密码"]\').value = "{self.fake_password}";'
        self.browser.execute_script(script)
        time.sleep(5)
        # input_frame_2 = self.browser.find_element('//input[@placeholder="再次输入新密码"]')
        # input_frame_2.send_keys(self.fake_password)
        button_selector = ".button"  # 请根据实际情况提供正确的选择器
        script = f'document.querySelector("{button_selector}").click();'
        self.browser.execute_script(script)
        self.browser.find_element(By.XPATH, "//div[@class='button']")  # TODO 这里要捕获到新密码太弱的框框，如果出现，就重新输密码
        # reset_pwd_btn = self.browser.find_element('//div[@class="button"]')
        # reset_pwd_btn.click()
        return True

    # ==============图像验证处理程序==============
    def parse_img_val(self):
        print(f"getting in parse_img_val")
        # ---------------------------4.获取图片（层级：滑块>缺口背景>满背景）-------------------------------
        # 删除滑块图片
        slider_element = self.browser.find_element(By.XPATH, '//canvas[@class="geetest_canvas_slice geetest_absolute"]')
        gap_img_element = self.browser.find_element(By.XPATH, '//canvas[@class="geetest_canvas_bg geetest_absolute"]')
        self.set_gapbg_opacity_0(gap_img_element)  # 设置 缺口背景 不可见 -> 当前：√滑块 X缺口 X满
        slider_element.screenshot('./img/slider.png')
        self.set_slider_opacity_0(slider_element)  # 设置 滑块 不可见 -> 当前：X滑块 X缺口 X满
        self.set_fullbg_opacity_1()  # 设置 满背景 可见 -> 当前：X滑块 X缺口 √满
        (self.browser.find_element(By.XPATH, '//*[@class="geetest_canvas_fullbg geetest_fade geetest_absolute"]')
         .screenshot('./img/full.png'))
        self.set_fullbg_display_none()  # 设置 满背景 不可见 -> 当前：X滑块 X缺口 X满
        self.add_gap_png(gap_img_element)  # 设置 缺口背景 可见 -> 当前：X滑块 √缺口 X满
        gap_img_element.screenshot('./img/gap.png')
        self.add_slide_png(slider_element)  # 设置 滑块 可见 -> 当前：√滑块 √缺口 X满
        # 执行滑块操作
        print(f"slider_element: {slider_element}")
        # 传统像素检测
        gap_pos = self.detect_diff_img('img/full.png', 'img/gap.png')
        gap_pos -= 5
        # ----------------------------------拖动按钮拼合验证---------------------------------
        slider_btn = self.browser.find_element(By.XPATH, '//*[@class="geetest_slider_button"]')
        self.perform_move(slider_btn, gap_pos)
        # 检测是否通过验证，如果没通过，那就使用验证码刷新按钮，重新获取图片重新点按钮
        self.validate_failed_try_again()

    def validate_failed_try_again(self):
        time.sleep(2)
        val_element = self.browser.find_element(By.XPATH, '//*[@class="geetest_panel geetest_wind"]')
        style_value = val_element.get_attribute("style")  # 获取元素的 style 属性值
        if "display: block; opacity: 1;" in style_value:
            val_refresh_btn = self.browser.find_element(By.XPATH, "//a[@class='geetest_refresh_1']")
            val_refresh_btn.click()
            self.parse_img_val()

    def check_if_msg_wrong(self):
        duplicate_msg_bar = (self.browser.find_element(By.XPATH,
                                                       '//div[@class="form"]/div[@class="formItem"][2]//div[@class="error"]'))
        style_attribute_value = duplicate_msg_bar.get_attribute("style")
        # 输完之后我要点击一下其他地方，系统才会检测验证码是否正确
        registration_title = self.browser.find_element(By.CLASS_NAME, 'title')
        self.browser.execute_script("arguments[0].click();", registration_title)
        # 焦点转移完成
        if "display: none;" in style_attribute_value:
            print(f"说明没有别人没在爬，可以注册: {self.fake_phone}")
        # elif not style_attribute_value:
        else:
            text_attribute_value = duplicate_msg_bar.text
            print(f"有问题，放弃吧。系统将其录入数据库(code: 4): {self.fake_phone}: {text_attribute_value}")
            self.sql_parse_instance.modify_mysql_status_code(self.fake_phone, 4)
            self.browser.close()
            self.browser.quit()
            return False
            # raise SystemExit(-1)

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
    def detect_diff_img(self, full_img_url, gap_img_url):
        image_a = Image.open(full_img_url).convert('RGB')  # 打开原始图片
        image_b = Image.open(gap_img_url).convert('RGB')  # 打开有缺口的图片
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

    def get_gap(self, image1, image2, threshold):
        left = 60
        for i in range(left, image1.size[0]):
            for j in range(image1.size[1]):
                if not self.is_pixel_equal(image1, image2, i, j, threshold):
                    left = i
                    return left
        return left

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

    # 接收短信
    def inject_val_msg(self, retry_times):
        # 去接码平台调用收取验证码API，得到验证消息内容
        msg_ver_code_text = self.tel_msg_rcv.get_msg(self.temp_token, self.fake_phone)
        print(f"msg_ver_code_text: {msg_ver_code_text}")
        # 提取验证消息内容，拿到验证码
        match_un_rcv = re.search(r'尚未收到', msg_ver_code_text)
        if match_un_rcv and retry_times < 4:  # 最高执行5次
            print("没收到验证码短信，请继续等待")
            retry_times += 1
            time.sleep(10)
            return self.inject_val_msg(retry_times)  # 回调
        elif not match_un_rcv:
            print("收到了验证码短信，请进一步处理")
            # match_ver_code = re.search(r'\b\d{6}\b', msg_ver_code_text)
            # match_ver_code = re.findall(r'(?<!\d)\d{6}(?!\d)', msg_ver_code_text)
            match_ver_code = re.findall(r'(?<!\d)\d{6}(?!\d)', msg_ver_code_text)
            print(f"match_ver_code: {match_ver_code}")
            if match_ver_code:
                # verification_code = match_ver_code.group()
                verification_code = match_ver_code[0]
                print("提取到的验证码:", verification_code)
                return verification_code
            else:
                print("未找到6位数字验证码")
                return False
        elif retry_times > 1:
            self.sql_parse_instance.modify_mysql_status_code(self.fake_phone, 3)
            print(f"此手机无法收到验证码，系统将其录入数据库(code: 3)，请放弃使用: {self.fake_phone}")
            self.browser.close()
            self.browser.quit()
            return False
            # raise SystemExit(-1)

    # 点击输入短信
    def input_val_msg(self, verification_code):
        # 将验证码输入到输入框内
        val_msg_input = self.browser.find_element(By.XPATH, '//input[@class="password-input"]')
        val_msg_input.send_keys(verification_code)
        print(f"msg inputted...: {verification_code}")
        return True
