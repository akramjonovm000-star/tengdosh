import sqlite3
try:
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT role, COUNT(*) FROM staff GROUP BY role")
    print(cursor.fetchall())
    conn.close()
except Exception as e:
    print(f"Error: {e}")
