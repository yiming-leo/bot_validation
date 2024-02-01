import os
import time
from datetime import datetime

from SqlParse import SqlParse
from TelMsgRcv import TelMsgRcv
from RegisterParse import CrackGeetest
from DetectIsRegistered import CrackRegistered
from reset_pwd_module.ResetPwd import ResetPassword


register_url = "https://passport.haodf.com/nusercenter/registerbymobile"
reset_pwd_url = "https://passport.haodf.com/nusercenter/help/resetpassword"
fake_password = "Ingru2023"
msg_username = "leoanother"
msg_password = "anotherqq"

mysql_host = '192.168.1.204'
mysql_port = 3308
mysql_user = 'root'
mysql_password = '123456'
mysql_database = 'db_haodf'

selenium_remote_driver_url = 'http://192.168.2.15:4444'

# 创建通用实例给不同文件调用
sql_parse_instance = SqlParse(mysql_host, mysql_port, mysql_user, mysql_password, mysql_database)
tel_msg_rcv = TelMsgRcv()
temp_token = tel_msg_rcv.sing_in(msg_username, msg_password)

# -----------1-2. 去mysql里查询是否已有此新号------------
while True:
    time.sleep(5)  # 防止过度查询被封号
    left_amount = tel_msg_rcv.left_amount(temp_token)
    fake_phone = None
    print(f"钱包里还有￥{left_amount}元钱")
    if float(left_amount) <= 0.99:
        raise SystemExit(f"钱包没钱了，要充钱。当前金额：{left_amount}")
    # 循环扫数据库，抽到任何block字段>=3的就要来注册一遍，抽到==2的就执行重置密码操作
    while True:
        fake_phone = sql_parse_instance.get_fake_phone_from_mysql_status(2)
        if fake_phone:  # 得到了fake_phone
            break
    # TODO 这里要处理2状态的数据
    reset_pwd_instance = ResetPassword(fake_phone, fake_password, reset_pwd_url, temp_token,
                                       sql_parse_instance,
                                       selenium_remote_driver_url)
    if reset_pwd_instance.reset_account_password():
        sql_parse_instance.modify_mysql_status_code(fake_phone, 0)
    else:
        print("密码重置失败")
    break
