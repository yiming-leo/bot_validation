from SqlParse import SqlParse
from TelMsgRcv import TelMsgRcv
from bot_validation import CrackGeetest


if __name__ == '__main__':
    register_url = "https://passport.haodf.com/nusercenter/registerbymobile"
    fake_password = "Ingru2023"
    msg_username = "leoanother"
    msg_password = "anotherqq"

    mysql_host = '192.168.1.204'
    mysql_port = 3308
    mysql_user = 'root'
    mysql_password = '123456'
    mysql_database = 'haodf'

    # 创建通用实例给不同文件调用
    sql_parse_instance = SqlParse(mysql_host, mysql_port, mysql_user, mysql_password, mysql_database)

    # -----------0-1. 在接码平台获取新号------------
    tel_msg_rcv = TelMsgRcv()
    temp_token = tel_msg_rcv.sing_in(msg_username, msg_password)
    left_amount = tel_msg_rcv.left_amount(temp_token)
    fake_phone = tel_msg_rcv.get_phone(temp_token)
    # msg_ver_code_text = tel_msg_rcv.get_msg(temp_token, fake_phone)  # 谨慎开启！！！

    # -----------1-2. 去mysql里查询是否已有此新号------------

    # -----------2-3. 去haodf找回密码网站看看账号是否被注册过------------

    # -----------3-6. 去haodf用户注册网站注册-----------
    crack = CrackGeetest(fake_phone, fake_password, register_url, temp_token)
    crack.crack()

    # 0：（可以使用）未被别人注册，已被我们注册
    # 1：（账号被封了）因为前面太SB， haodf超用了
    # 2：（别人注册了）已被别人注册，我们无法注册
    # -1：（无法注册）无法接收到短信
    # -2：（特殊无法注册）未被别人注册，我们也无法注册啊这个手机有问题

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
    #   - 0 如果得不到短信，那就获取新号，数据库里记录此手机和状态-1
    #   - 6 如果得到了短信，那就提取短信验证码内容，填充到元素上，数据库里记录此手机和状态0
    # 6. 设置密码，检查阅读协议是否点击（没点就点），然后点击注册按钮，停留10秒，数据库里记录此手机和状态0
