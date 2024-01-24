import pymysql


class SqlParse:
    def __init__(self, mysql_host, mysql_port, mysql_user, mysql_password, mysql_database):
        self.mysql_host = mysql_host
        self.mysql_port = mysql_port
        self.mysql_user = mysql_user
        self.mysql_password = mysql_password
        self.mysql_database = mysql_database
        try:
            # 连接到 MySQL 数据库
            self.connection = pymysql.connect(host=self.mysql_host, port=self.mysql_port, user=self.mysql_user,
                                              password=self.mysql_password, database=self.mysql_database)
            self.cursor = self.connection.cursor()
        except pymysql.Error as err:
            print(f"Error: {err}")

    def save_fake_phone_to_mysql(self, fake_phone, fake_password, status_code):
        # 执行插入操作
        insert_query = "INSERT INTO disease_user (fake_phone, fake_password, status_code) VALUES (%s, %s, %s)"
        insert_values = (fake_phone, fake_password, status_code)
        self.cursor.execute(insert_query, insert_values)
        # 提交事务
        self.connection.commit()
        print("Data inserted successfully.")

    def query_fake_phone_exist(self, fake_phone):
        pass