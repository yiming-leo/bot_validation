import os
import time
from datetime import datetime

from SqlParse import SqlParse
from TelMsgRcv import TelMsgRcv
from RegisterParse import CrackGeetest
from DetectIsRegistered import CrackRegistered

if __name__ == '__main__':
    os.makedirs('img', exist_ok=True)  # 看看img目录是否正常
    os.makedirs('log', exist_ok=True)  # 看看log目录是否正常
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

    while True:  # 爬取失败的重试
        while True:  # haodf账号被注册的重试
            while True:  # mysql号码存在的重试
                # -----------0-1. 在接码平台获取新号------------
                fake_phone = tel_msg_rcv.get_phone(temp_token)
                print(f"当前虚拟号码：{fake_phone}")
                left_amount = tel_msg_rcv.left_amount(temp_token)
                print(f"钱包里还有￥{left_amount}元钱")
                if float(left_amount) <= 0.99:
                    raise SystemExit(f"钱包没钱了，要充钱。当前金额：{left_amount}")
                # -----------1-2. 去mysql里查询是否已有此新号------------
                is_already_in_db = sql_parse_instance.query_fake_phone_exist(fake_phone)
                print(f"{fake_phone}已经存在数据库了吗: {is_already_in_db}")
                time.sleep(5)  # 防止过度查询被封号
                if not is_already_in_db:
                    break  # 到0-1去重新得到一个新的手机号，这里需要无限迭代，直到得到一个新号为止
            # -----------2-3. 去haodf找回密码网站看看账号是否被注册过------------
            crack_registered_instance = CrackRegistered(fake_phone, reset_pwd_url, selenium_remote_driver_url)
            is_can_be_used = crack_registered_instance.detect_is_registered()
            print(f"is_can_be_used: {is_can_be_used}")
            if is_can_be_used:
                print(f"终于找到一个可用的手机了: {fake_phone} 时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}")
                sql_parse_instance.save_fake_phone_to_mysql(fake_phone, fake_password, 5)
                break
            else:
                print(f"mysql已存在账号: {fake_phone} 时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}")
                sql_parse_instance.save_fake_phone_to_mysql(fake_phone, fake_password, 2)
        # -----------3-6. 去haodf用户注册网站注册-----------
        crack_geetest_instance = CrackGeetest(fake_phone, fake_password, register_url, temp_token, sql_parse_instance,
                                              selenium_remote_driver_url)
        crack_result = crack_geetest_instance.crack()
        if crack_result:  # 如果正常执行，那就结束；不正常？那就重来一遍
            print(f"当前时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} ")
            raise SystemExit(0)

    # 0：（可以使用）未被别人注册，已被我们注册
    # 1：（账号被封了）因为前面太SB， haodf超用了
    # 2：（别人注册了）已被别人注册，我们无法注册
    # 3：（无法注册）无法接收到短信
    # 4：（注册撞上了）我们在注册的时候，他们也在注册，导致验证码不正确
    # 5：（没注册）未被别人注册，我们也没注册，可以去手动注册
    # 6：（注册异常）当我们注册时候，点击按钮没反应

    # 0. 在接码平台获取新号
    # 1. 去mysql里查询是否已有此新号，
    #   - 0 如果有，那就重新回到0
    # 2. 去haodf找回密码网站看看账号是否被注册过，https://passport.haodf.com/nusercenter/help/resetpassword
    #   - 0 如果跳出来“图片验证框”或2个<p class="password-text">，内容有“已向您的手机发送了一条验证短信”，说明已被注册，那就数据库里记录此手机和状态2，然后重新回到0
    #   - 3 如果有弹窗<div id="js-bubble" role="alert" style="display: inline-block; opacity: 0;">存在几秒，之后inline-block又变回none，那就说明没被注册
    # ---------------至此已确认现在拿到的手机号没被注册（同时也筛掉了被封禁的手机）-----------------
    # 3. 去haodf用户注册网站注册，填入手机号，https://passport.haodf.com/nusercenter/registerbymobile
    # 4. 点击获取验证码，跳出校验框进行校验，调用自动校验通过图片校验，通过之后验证码会发送
    # 5. 在30s内，去接码平台得到短信
    #   - 0 如果得不到短信，那就获取新号，数据库里记录此手机和状态3
    #   - 6 如果得到了短信，那就提取短信验证码内容，填充到元素上，数据库里记录此手机和状态0
    # 6. 设置密码，检查阅读协议是否点击（没点就点），然后点击注册按钮，停留10秒，数据库里记录此手机和状态0
