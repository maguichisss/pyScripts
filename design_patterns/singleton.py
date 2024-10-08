# Design pattern singleton
# example connection to a sqlite database
# based on https://youtu.be/YXV0L8YdPxg

import sqlite3

class Singleton:
    _instance = []
    def __new__(self, *args, **kwargs):
        if self not in self._instance:
            self._instance.append(super().__new__(self))
        return self._instance[0]

#o1, o2, o3 = Singleton(), Singleton(), Singleton()
#print(o1 is o2)
#print(o1 is o3)

class DBConnection(Singleton):
    conn = None
    def __init__(self):
        if self.conn is None:
            self.conn = sqlite3.connect('users.db')

    def execute_query(self, query):
        cursor = self.conn.cursor()
        cursor.execute(query)
        self.conn.commit()
        #self.conn.close()

db1 = DBConnection()
db1.execute_query("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, created TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
db1.execute_query('delete from users') # warning, deletes all data in table
db1.execute_query('INSERT INTO users (name) VALUES ("Isabel")')

db2 = DBConnection()
db2.execute_query('INSERT INTO users (name) VALUES ("MAU")')
db2.execute_query('INSERT INTO users (name) VALUES ("BlanCA")')

db3 = DBConnection()
db3.execute_query('INSERT INTO users (name) VALUES ("Aris")')
db3.execute_query("INSERT INTO users (name) VALUES ('Milo')")
db3.execute_query("INSERT INTO users (name) VALUES ('Doly')")

print(db1 is db2)
print(db1 is db3)
db2.conn.close()
