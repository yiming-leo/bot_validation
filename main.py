import time

from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


class CrackGeetest:

    def __init__(self):
        self.browser = webdriver.Chrome()
        self.url = "https://passport.haodf.com/nusercenter/showlogin"

    def crack(self):
        self.browser.get(self.url)  # 访问网址
        time.sleep(2)
        print(f"url访问成功")
        tel_input = self.browser.find_element(By.XPATH, '//*[@placeholder="请输入手机号"]')
        tel_input.send_keys("13111111112")
        send_code = self.browser.find_element(By.XPATH, '//*[@class="sendCode"]')
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
        # 3.获取图片（层级：滑块>缺口背景>满背景）
        # ------------------删除滑块图片------------------
        slider_element = self.browser.find_element(By.XPATH, '//canvas[@class="geetest_canvas_slice geetest_absolute"]')
        slider_element.screenshot('slider.png')
        self.browser.execute_script("""
            var element = arguments[0];
            element.style.opacity = '0';
        """, slider_element)
        print("==>1: remove slider_element")
        time.sleep(0.5)
        # ------------------删除缺口图片------------------
        gap_img_element = self.browser.find_element(By.XPATH, '//canvas[@class="geetest_canvas_bg geetest_absolute"]')
        gap_img_element.screenshot('gap.png')
        self.browser.execute_script("""
            var element = arguments[0];
            element.style.opacity = '0';
        """, gap_img_element)
        print("==>2: remove gap_img_element")
        time.sleep(0.5)
        # ------------------修改 canvas 元素的 style 属性------------------
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
        (self.browser.find_element(By.XPATH, '//*[@class="geetest_canvas_fullbg geetest_fade geetest_absolute"]')
         .screenshot('full.png'))
        # ------------------修改 canvas 元素的 style 属性------------------
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
        # -----------------把他们删除的的都加回来------------------
        # 将滑块图片的透明度设置为不透明（1）
        self.browser.execute_script("""
            var element = arguments[0];
            element.style.opacity = '1';
        """, slider_element)
        print("==>2: create element: slide_png")
        time.sleep(0.5)
        # ------------------将滑块图片的透明度设置为不透明（1）------------------
        self.browser.execute_script("""
                    var element = arguments[0];
                    element.style.opacity = '1';
                """, gap_img_element)
        print("==>1: create element: gap_png")
        time.sleep(0.5)
        # -----------------执行滑块操作------------------
        print(f"slider_element: {slider_element}")
        # -------传统像素检测-----------
        image_a = Image.open('full.png').convert('RGB')  # 打开原始图片
        image_b = Image.open('gap.png').convert('RGB')  # 打开有缺口的图片
        gap_pos = self.get_gap(image_a, image_b, 60)
        print(f"gap_pos: {gap_pos}")
        gap_pos -= 5
        # ----------通用模块-------------
        slider_btn = self.browser.find_element(By.XPATH, '//*[@class="geetest_slider_button"]')
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
        # ---------检测是否通过验证，如果没通过，那就使用验证码刷新按钮，重新获取图片重新点按钮----------
        time.sleep(2)
        val_element = self.browser.find_element(By.XPATH, '//*[@class="geetest_panel geetest_wind"]')
        style_value = val_element.get_attribute("style")  # 获取元素的 style 属性值
        if "display: block; opacity: 1;" in style_value:
            val_refresh_btn = self.browser.find_element(By.XPATH, "//a[@class='geetest_refresh_1']")
            val_refresh_btn.click()
            self.login()
        print(f"结束")

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


if __name__ == '__main__':
    crack = CrackGeetest()
    crack.crack()
