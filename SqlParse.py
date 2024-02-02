import pymysql


class SqlParse:
    def __init__(self, mysql_host, mysql_port, mysql_user, mysql_password, mysql_database):
        self.mysql_host = mysql_host
        self.mysql_port = mysql_port
        self.mysql_user = mysql_user
        self.mysql_password = mysql_password
        self.mysql_database = mysql_database
        self.mysql_cursor = None
        try:
            # 连接到 MySQL 数据库
            self.connection = pymysql.connect(host=self.mysql_host, port=self.mysql_port, user=self.mysql_user,
                                              password=self.mysql_password, database=self.mysql_database)
            self.mysql_cursor = self.connection.cursor()
        except pymysql.Error as err:
            print(f"Error: {err}")

    def save_fake_phone_to_mysql(self, fake_phone, fake_password, status_code):
        # 执行插入操作
        insert_query = "INSERT INTO disease_user (phone, password, block) VALUES (%s, %s, %s)"
        insert_values = (fake_phone, fake_password, status_code)
        self.mysql_cursor.execute(insert_query, insert_values)
        # 提交事务
        self.connection.commit()
        print(f"数据新增成功==>{fake_phone}, {fake_password}, {status_code}")

    # True: 存在于db里; False: db内不存在
    def query_fake_phone_exist(self, fake_phone):
        try:
            search_query = "SELECT * FROM disease_user WHERE phone=%s"
            self.mysql_cursor.execute(search_query, (fake_phone,))
            result = self.mysql_cursor.fetchone()
            return bool(result)
        except Exception as e:
            print(f"Exception Occurred: {e}")

    def modify_mysql_status_code(self, fake_phone, status_code):
        try:
            modify_query = "UPDATE disease_user SET block=%s WHERE phone=%s"
            self.mysql_cursor.execute(modify_query, (status_code, fake_phone))
            self.connection.commit()
            print(f"数据修改成功==>{fake_phone}, {status_code}")
        except Exception as e:
            print(f"Exception Occurred: {e}")

    def modify_mysql_status_code_register_date_block_date(self, fake_phone, status_code, register_date, block_date):
        try:
            modify_query = "UPDATE disease_user SET block=%s, register_date=%s, block_date=%s WHERE phone=%s"
            self.mysql_cursor.execute(modify_query, (status_code, register_date, block_date, fake_phone))
            self.connection.commit()
            print(f"数据修改成功==>{fake_phone}, {status_code}, {register_date}, {block_date}")
        except Exception as e:
            print(f"Exception Occurred: {e}")

    def get_fake_phone_from_mysql_status(self, block_values):
        try:
            modify_query = "SELECT phone FROM disease_user WHERE block=%s ORDER BY RAND() LIMIT 1"
            self.mysql_cursor.execute(modify_query, (block_values,))
            # self.connection.commit()
            result = self.mysql_cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Exception Occurred: {e}")
