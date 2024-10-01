import sqlite3


class Connect():
    def __init__(self, db_name):
        self.con = sqlite3.connect(db_name)
        self.cursor = self.con.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('create table if not exists users (id integer auto_increment, token text)')
        self.con.commit()

    def auth_token(self, token):
        self.cursor.execute('select * from users where token = ?', (token,))
        if self.cursor.fetchone():
            return True #если токен уже зарегистрирован в kivy
        return False #если не зарегистрирован

    def add_token(self, token):
        if not self.auth_token(token):
            self.cursor.execute('insert into users (token) values (?)', (token,))
            self.con.commit()
