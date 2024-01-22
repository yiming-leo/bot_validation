from selenium import webdriver
import os
import time
from PIL import Image, ImageChops
from selenium.webdriver.common.by import By

# chrome_path = 'C:/Program Files/Google/Chrome/Application/chromedriver.exe'
# 1.访问网址
browser = webdriver.Chrome()
url = "https://passport.haodf.com/nusercenter/showlogin"  # 获取HTML文件的文件绝对路径

# browser.find_element()
# 2.获取原始图片
# browser.find_element(By.XPATH, '//*[@id="jigsawCanvas"]').screenshot('origin.png')  # 获取原始图片

browser.get(url)  # 访问网址
time.sleep(2)

tel_input = browser.find_element(By.XPATH, '//*[@placeholder="请输入手机号"]')
tel_input.send_keys("16754664381")
# TODO 输入手机号

send_code = browser.find_element(By.XPATH, '//*[@class="sendCode"]')
send_code.click()
# TODO 点击按钮
# TODO 接下来等2秒，就会出现图片验证
print(f"恭喜你到了这一步")
time.sleep(5)

print(f"恭喜你出现了验证")

# TODO 定位到class="geetest_canvas_slice geetest_absolute"，然后获取滑块图片
# TODO 定位到class="geetest_canvas_fullbg geetest_fade geetest_absolute"，设置style="opacity: 1;"，然后获取原始背景图片
# TODO 定位到class="geetest_canvas_bg geetest_absolute"，然后获取缺口背景图片

# 3.获取有缺口的背景图片
full_img = browser.find_element(By.XPATH,
                                '//*[@class="geetest_canvas_fullbg geetest_fade geetest_absolute"]').screenshot(
    'full.png')
slider = browser.find_element(By.XPATH, '//*[@class="geetest_canvas_slice geetest_absolute"]')
slider.click()  # 先模拟点击下，方便下面获取到有缺口的图片
gap_img = browser.find_element(By.XPATH, '//*[@class="geetest_canvas_bg geetest_absolute"]').screenshot('gap.png')

# 4.比较两幅图片的区别，获取需要移动的距离
image_a = Image.open('full.png').convert('RGB')  # 打开原始图片
image_b = Image.open('gap.png').convert('RGB')  # 打开有缺口的图片

x = ImageChops.difference(image_a, image_b).getbbox()  # 比较两个图片的差别
print(x)  # 举个例子：倘若x为：(226, 103, 277, 154)；返回缺口对应的左边横坐标（由左往右看），上边纵坐标（由上往下看），右边横坐标，下边纵坐标
distance = x[0]  # 第一个元素x[0]表示的就是缺口左边横坐标，也就是滑块需要移动的距离
print(f"distance: {distance}")  # 如果例子为：(226, 103, 277, 154)，那么需要移动的距离为226

# 5.开始滑动！
action = webdriver.ActionChains(browser)  # 启动Selenium的动作链
action.click_and_hold(slider).perform()  # 按住滑动按钮不松开
# action.move_by_offset(distance-10, 0)  # 开始滑动！这里-10，是把初始圆角矩形左侧left属性值给减去了，这样更准确
action.release().perform()  # 释放滑块
