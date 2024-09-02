import json
import sqlite3


class DBService:
    def __init__(self):
        self.conn = sqlite3.connect("data/sqlite.db")

    def init_db(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS personal_settings (
                user_id TEXT PRIMARY KEY,
                settings_json JSON
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                access_token TEXT
            );
        """)
        self.conn.commit()
        self.conn.close()

    def get_db_connection(self):
        return self.conn

    def close_db_connection(self):
        self.conn.close()

    def save_personal_settings(self, user_id, personal_settings_json_data):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO personal_settings (user_id, settings_json)
            VALUES (?, ?)
        """,
            (user_id, json.dumps(personal_settings_json_data)),
        )
        conn.commit()
        conn.close()

    def load_personal_settings(self, user_id):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT settings_json FROM personal_settings WHERE user_id = ?
        """,
            (user_id,),
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return json.loads(row[0])
        return None

    def save_user_token(self, user_id, access_token):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO users (user_id, access_token)
            VALUES (?, ?)
        """,
            (user_id, access_token),
        )
        conn.commit()
        conn.close()

    def load_user_token(self, user_id):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT access_token FROM users WHERE user_id = ?
        """,
            (user_id,),
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0]
        return None
