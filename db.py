import json
import sqlite3

table_name = "data"

connection = sqlite3.connect("data.db", check_same_thread=False)
cur = connection.cursor()

cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name}(
            user_id INTEGER NOT NULL, 
            english_level TEXT NOT NULL CHECK (english_level IN ("A1", "A2", "B1", "B2", "C1", "C2")), 
            analyse_data TEXT NOT NULL
            )
""")


def save_data(user_id, data):
    json_data = json.dumps(data, default=lambda o: o.__dict__, sort_keys=True)
    assessment = data.get("assessment")
    try:
        cur.execute("INSERT INTO data VALUES (?, ?, json(?))", (user_id, assessment, json_data))
    except sqlite3.IntegrityError:
        print(f"Error in saving user {user_id}")
    connection.commit()


def format_data(rows):
    result = {}
    for user_id, _, data in rows:
        result[user_id] = json.loads(data)
    return result


def get_data_for_user(user_id):
    cur.execute("SELECT * FROM data WHERE user_id = ?", (user_id,))
    rows = cur.fetchall()
    return format_data(rows)


def get_data_by_level(level, limit):
    cur.execute("""SELECT * FROM data WHERE english_level = ? ORDER BY RANDOM() LIMIT ?""",
                (level, limit))
    rows = cur.fetchall()
    return format_data(rows)
