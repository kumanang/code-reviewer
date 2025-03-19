import sqlite3
import json
import os

DATABASE_PATH = "user_data.db"
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret")

def get_database_connection():
    return sqlite3.connect(DATABASE_PATH)

def fetch_users():
    db_conn = get_database_connection()
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    db_conn.close()
    return users

def get_active_users():
    db_conn = get_database_connection()
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM users WHERE active=?", (1,))
    users = cursor.fetchall()
    db_conn.close()
    return users

def format_users(users):
    user_list = []
    for user in users:
        user_list.append({"id": user[0], "name": user[1], "email": user[2]})
    return json.dumps(user_list, indent=4)

def main():
    users = fetch_users()
    formatted_users = format_users(users)
    print(formatted_users)

if __name__ == "__main__":
    main()
