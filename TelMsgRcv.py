import re

import requests
import urllib.parse


# 接码平台功能模块
# 1. 登录（必做的事情，因为需要获取token，要长久保存）
# 2. 查询余额（循环到余额>=0.35为止，因为无法扣钱了）
# 3. 获取手机号（免费，得到手机号，然后交给下一步处理）
# 4. 获取短信（收费0.35一次，中文关键字需要先转unicode编码）


class TelMsgRcv:
    def __init__(self):
        self.base_url = "http://api.uomsg.com/zc/data.php"

    # ------------------1. 登录（必做的事情，因为需要获取token，要长久保存）--------------------
    def sing_in(self, username, password):
        # 构建请求参数
        params = {
            "code": "signIn",
            "user": username,
            "password": password
        }
        response = requests.get(self.base_url, params=params)
        print(f">>===>>^^^sing_in^^^<<===<<")
        if response.status_code == 200:
            print(f"Token: {response.text}")
            return response.text
        else:
            print(f"Request failed. Status code: {response.status_code}")
            return None

    # ------------------2. 查询余额（循环到余额>=0.35为止，因为无法扣钱了）------------------
    def left_amount(self, token):
        # 确保已登录并获取到 token
        if not token:
            print("Please sign in first.")
            return None
        # 构建请求参数
        params = {
            "code": "leftAmount",
            "token": token
        }
        response = requests.get(self.base_url, params=params)
        print(f">>===>>$$$left_amount$$$<<===<<")
        if response.status_code == 200:
            print(f"Left Amount: {response.text}")
            return response.text
        else:
            print(f"Request failed. Status code: {response.status_code}")
            return None

    # ------------------3. 获取手机号（免费，得到手机号，然后交给下一步处理）------------------
    def get_phone(self, token, province="全部", card_type="实卡"):
        # 确保已登录并获取到 token
        if not token:
            print("Please sign in first.")
            return None
        # 构建请求参数
        params = {
            "code": "getPhone",
            "token": token,
            "phone": "",  # 可以留空，接口会自动分配手机号
            "province": province,
            "cardType": card_type
        }
        response = requests.get(self.base_url, params=params)
        print(f">>===>>###get_phone###<<===<<")
        if response.status_code == 200:
            print(f"Phone Number: {response.text}")
            return response.text
        else:
            print(f"Request failed. Status code: {response.status_code}")
            return None

    # ------------------4. 获取短信（收费0.35一次，中文关键字需要先转unicode编码）------------------
    def get_msg(self, token, phone_number, keyword="好大夫在线"):
        keyword_unicode = keyword
        # 确保已登录并获取到 token
        if not token:
            print("Please sign in first.")
            return None
        # 转换中文关键字为 Unicode 编码
        print(f"keyword_unicode: {keyword_unicode}")
        # 构建请求参数
        params = {
            "code": "getMsg",
            "token": token,
            "phone": phone_number,
            "keyWord": keyword_unicode
        }
        response = requests.get(self.base_url, params=params)
        print(f">>===>>@@@get_msg@@@<<===<<")
        if response.status_code == 200:
            print(f"Message VerCode Text: {response.text}")
            have_error_text = re.search(r'ERROR', response.text)
            if have_error_text:
                print(f"请求失败！ {response.text}")
                return None
            return response.text
        else:
            print(f"Request failed. Status code: {response.status_code}")
            return None
