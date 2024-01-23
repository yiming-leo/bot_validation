import cv2
import numpy as np
from selenium import webdriver
import os
import time
from PIL import Image, ImageChops
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# chrome_path = 'C:/Program Files/Google/Chrome/Application/chromedriver.exe'
# 1.访问网址

class CrackGeetest:

    def __init__(self):
        self.browser = webdriver.Chrome()
        self.url = "https://passport.haodf.com/nusercenter/showlogin"

    def crack(self):

        self.browser.get(self.url)  # 访问网址
        time.sleep(2)

        print(f"url访问成功")

        tel_input = self.browser.find_element(By.XPATH, '//*[@placeholder="请输入手机号"]')
        tel_input.send_keys("13111111111")

        send_code = self.browser.find_element(By.XPATH, '//*[@class="sendCode"]')
        send_code.click()

        print(f"请求验证成功")

        time.sleep(2)

        # self.browser.find_element()
        element = WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='geetest_panel geetest_wind']"))
        )
        print(f"element: {element}")

        style_attribute = element.get_attribute("style")
        print(f"style_attribute: {style_attribute}")

        if "display: block; opacity: 1;" in style_attribute:
            print("Style attribute matches the expected value!")
            self.login()
        else:
            print(f"element错误")
            self.crack()

        # TODO 定位到class="geetest_canvas_slice geetest_absolute"，然后获取滑块图片
        # TODO 定位到class="geetest_canvas_fullbg geetest_fade geetest_absolute"，设置style="opacity: 1;"，然后获取原始背景图片
        # TODO 定位到class="geetest_canvas_bg geetest_absolute"，然后获取缺口背景图片

    def login(self):
        print(f"getting in login")
        # 3.获取图片（层级：滑块>缺口背景>满背景）
        # ------------------删除滑块图片
        slider_element = self.browser.find_element(By.XPATH, '//canvas[@class="geetest_canvas_slice geetest_absolute"]')
        slider_element.screenshot('slider.png')
        self.browser.execute_script("""
        var element = arguments[0];
        element.parentNode.removeChild(element);
        """, slider_element)
        print("==>1: remove slider_element")
        time.sleep(5)
        # ------------------删除缺口图片
        gap_img_element = self.browser.find_element(By.XPATH, '//canvas[@class="geetest_canvas_bg geetest_absolute"]')
        gap_img = gap_img_element.screenshot('gap.png')
        self.browser.execute_script("""
        var element = arguments[0];
        element.parentNode.removeChild(element);
        """, gap_img_element)
        print("==>2: remove gap_img_element")
        time.sleep(5)
        # ------------------获取完整图片
        # ------------------修改 canvas 元素的 style 属性
        result = self.browser.execute_script("""
        var canvasElement = document.querySelector('.geetest_canvas_fullbg.geetest_fade.geetest_absolute');
        if (canvasElement) {
            canvasElement.setAttribute('style', 'opacity: 1;');
            return 'set success';
        }else {
            return 'style element_not_found';
        }
        """)
        print("==>3: modify style: display->X")
        time.sleep(5)
        full_img = (
            self.browser.find_element(By.XPATH, '//*[@class="geetest_canvas_fullbg geetest_fade geetest_absolute"]')
            .screenshot('full.png'))
        # ------------------修改 canvas 元素的 style 属性
        result2 = self.browser.execute_script("""
                var canvasElement = document.querySelector('.geetest_canvas_fullbg.geetest_fade.geetest_absolute');
                if (canvasElement) {
                    canvasElement.setAttribute('style', 'display: none; opacity: 1;');
                    return 'set success';
                }else {
                    return 'style element_not_found';
                }
                """)
        print("==>3: add style: display->none")
        time.sleep(20)
        # -----------------TODO 把他们删除的的都加回来
        # ------------------添加滑块和缺口图片
        self.browser.execute_script("""
        var canvasElement = document.createElement("canvas");
        canvasElement.className = "geetest_canvas_slice geetest_absolute";
        canvasElement.height = "160";
        canvasElement.width = "260";
        canvasElement.style = "opacity: 1; display: block"

        var targetDiv = document.querySelector('.geetest_slicebg.geetest_absolute');
        if (targetDiv) {
            targetDiv.appendChild(canvasElement);
        }
        """)
        print("==>2: create element: slide_png")
        time.sleep(20)

        self.browser.execute_script("""
        var canvasElement = document.createElement("canvas");
        canvasElement.className = "geetest_canvas_bg geetest_absolute";
        canvasElement.height = "160";
        canvasElement.width = "260";

        var targetDiv = document.querySelector('.geetest_slicebg.geetest_absolute');
        if (targetDiv) {
            targetDiv.appendChild(canvasElement);
        }
        """)
        print("==>1: create element: gap_png")
        time.sleep(5)

        time.sleep(10)
        # -----------------执行滑块操作
        print(f"slider_element: {slider_element}")
        # -------传统像素检测-----------
        image_a = Image.open('full.png').convert('RGB')  # 打开原始图片
        image_b = Image.open('gap.png').convert('RGB')  # 打开有缺口的图片
        gap_pos = self.get_gap(image_a, image_b, 60)
        print(f"gap_pos: {gap_pos}")

        # ----------通用模块-------------

        slider_btn = self.browser.find_element(By.XPATH, '//*[@class="geetest_slider_button"]')
        # 5.开始滑动！
        action = webdriver.ActionChains(self.browser)  # 启动Selenium的动作链
        action.click_and_hold(slider_btn).perform()  # 按住滑动按钮不松开

        # 模拟人类手动滑动，逐渐增加速度
        # distance = gap_pos  # 你的滑动距离
        # speed = 10  # 初始速度
        # acceleration = 1.3  # 加速度
        #
        # for i in range(1, distance + 1):
        #     action.move_by_offset(speed, 0).perform()
        #     speed += acceleration

        action.move_by_offset(gap_pos - 10, 0)  # 开始滑动！

        action.release().perform()  # 释放滑块
        time.sleep(5)
        print(f"结束")

    def pillow_detect(self, slider_element):
        slider_element.click()  # 先模拟点击下，方便下面获取到有缺口的图片
        # 4.比较两幅图片的区别，获取需要移动的距离
        image_a = Image.open('full.png').convert('RGB')  # 打开原始图片
        image_b = Image.open('gap.png').convert('RGB')  # 打开有缺口的图片

        x = ImageChops.difference(image_a, image_b).getbbox()  # 比较两个图片的差别

        print(x)  # 举个例子：倘若x为：(226, 103, 277, 154)；返回缺口对应的（左上角的 x 坐标）（左上角的 y 坐标）（右下角的 x 坐标）（右下角的 y 坐标）
        distance = x[0]  # 第一个元素x[0]表示的就是缺口左边横坐标，也就是滑块需要移动的距离
        print(f"distance: {distance}")  # 如果例子为：(226, 103, 277, 154)，那么需要移动的距离为226

    def cv2_detect(self):
        image_a = cv2.imread('full.png')
        image_b = cv2.imread('gap.png')
        # 转换为灰度图
        gray_a = cv2.cvtColor(image_a, cv2.COLOR_BGR2GRAY)
        gray_b = cv2.cvtColor(image_b, cv2.COLOR_BGR2GRAY)
        # 计算差异
        difference = cv2.absdiff(gray_a, gray_b)
        # 获取差异位置
        y, x = np.where(difference > 0)
        # 计算差异的边界框
        bbox = (min(x), min(y), max(x), max(y))
        print(f"bbox:{bbox}")

    def canny_detect(self):
        image_a = cv2.imread('full.png', cv2.IMREAD_GRAYSCALE)
        image_b = cv2.imread('gap.png', cv2.IMREAD_GRAYSCALE)
        # 进行 Canny 边缘检测
        edges_a = cv2.Canny(image_a, 350, 600)
        edges_b = cv2.Canny(image_b, 350, 600)
        # 计算差异
        difference = cv2.absdiff(edges_a, edges_b)
        # 获取差异位置
        y, x = np.where(difference > 0)
        # 计算差异的边界框
        bbox = (min(x), min(y), max(x), max(y))
        boxx = max(x) - min(x)
        boxy = max(y) - min(y)
        print(f"boxx: {boxx}")
        print(f"boxy: {boxy}")
        print(f"Bbox: {bbox}")

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
