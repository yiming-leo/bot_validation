import re
import time

from PIL import Image
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from TelMsgRcv import TelMsgRcv


# ----------3.去haodf用户注册网站注册---------------
class CrackGeetest:

    def __init__(self, fake_phone, fake_password, register_url, temp_token, sql_parse_instance):
        self.browser = webdriver.Chrome()
        self.url = register_url
        self.fake_password = fake_password
        self.fake_phone = fake_phone
        self.temp_token = temp_token
        self.tel_msg_rcv = TelMsgRcv()

        self.sql_parse_instance = sql_parse_instance

    # ==============主程序==============
    def crack(self):
        self.browser.get(self.url)
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
        style_attribute = element.get_attribute("style")
        print(f"style_attribute: {style_attribute}")
        if "display: block; opacity: 1;" in style_attribute:
            print("element正确，需要执行验证拼图操作")
            self.parse_img_val()
        else:
            print(f"element错误，无需执行验证拼图操作")
        self.login()

    # ==============图像验证处理程序==============
    def parse_img_val(self):
        print(f"getting in parse_img_val")
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

    # ==============末尾登录程序==============
    def login(self):
        time.sleep(0.5)
        self.check_if_duplicate_user_use()  # 检测一下是否发送用户重复检测，如果重复了，那么说明有人也在爬，那就--放弃--吧！
        time.sleep(15)  # 等待短信发送15s
        self.check_if_duplicate_user_use()  # 再再检测一下是否发送用户重复检测，如果重复了，那么说明有人也在爬，那就--放弃--吧！
        rcv_msg = self.inject_val_msg(1)  # 提取短信
        self.input_val_msg(rcv_msg)  # 输入短信验证码
        self.check_if_msg_wrong()  # 点击查看验证码是否错误，错误就--放弃--吧！
        self.input_password(self.fake_password)  # 没有错误就点击设置密码
        self.click_submit()  # 点击提交注册
        time.sleep(15)
        self.modify_save_phone()  # 保存手机号和手机状态到mysql
        time.sleep(5)
        print(f">>===>>结束<<===<<")
        self.browser.close()
        self.browser.quit()
        raise SystemExit(0)

    # -------------------------------------------组件-----------------------------------
    # 监测一下是否撞上了别人也在注册的号（这里有4种奇怪的问题：1. 别人在注册撞号了， 2. 手机验证码不正确， 3.数据错误请重试， 4. 请求过多重发验证码）
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
            raise SystemExit(-1)

    # 检测一下是否发送用户重复检测，如果重复了，那么说明有人也在爬
    def check_if_duplicate_user_use(self):
        duplicate_msg_bar = (self.browser.find_element(By.XPATH,
                                                       '//div[@class="form"]/div[@class="formItem"][1]//div[@class="error"]'))
        style_attribute_value = duplicate_msg_bar.get_attribute("style")
        if "display: none;" in style_attribute_value:
            print(f"说明没有别人没在爬，可以注册: {self.fake_phone}")
        # elif not style_attribute_value:
        else:
            # 说明有人在爬，放弃此号吧！
            print(f"撞号了，放弃吧。系统将其录入数据库(code: 4): {self.fake_phone}")
            self.sql_parse_instance.modify_mysql_status_code(self.fake_phone, 4)
            raise SystemExit(-1)

    # 保存手机号、密码、手机状态码到mysql
    def modify_save_phone(self):
        # 调用main程序
        print(f"成功注册账号，系统将其录入数据库(code: 0): {self.fake_phone}")
        self.sql_parse_instance.modify_mysql_status_code(self.fake_phone, 0)

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
            time.sleep(6)
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
            raise SystemExit(-1)

    # 点击输入短信
    def input_val_msg(self, verification_code):
        # 将验证码输入到输入框内
        val_msg_input = self.browser.find_element(By.XPATH, '//input[@type="text"]')
        val_msg_input.send_keys(verification_code)
        print(f"msg inputted...: {verification_code}")
        return True

    # 点击注册
    def click_submit(self):
        submit_btn = self.browser.find_element(By.XPATH, '//button[@class="submit"]')
        submit_btn.click()
        print(f"点击了注册按钮...")

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
            self.parse_img_val()

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
