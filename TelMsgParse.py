from TelMsgRcv import TelMsgRcv


class GetNewPhone:
    def __init__(self, msg_username, msg_password):
        self.msg_username = msg_username
        self.msg_password = msg_password

    # 组装token，拿到新的假电话号码，得到加电话号码和临时token
    def get_new_fake_phone(self):
        tel_msg_rcv = TelMsgRcv()
        temp_token = tel_msg_rcv.sing_in(self.msg_username, self.msg_password)
        fake_phone = tel_msg_rcv.get_phone(temp_token)
        return fake_phone, temp_token
