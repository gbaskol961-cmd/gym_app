import sqlite3

conn = sqlite3.connect("gym_data.db")
c = conn.cursor()

# Create users table if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT,
    age INTEGER,
    weight REAL,
    mail TEXT,
    code TEXT
)''')

# Add mail column if it doesn't exist (optional if table already exists without mail)
try:
    c.execute("ALTER TABLE users ADD COLUMN mail TEXT")
except sqlite3.OperationalError:
    print("Column 'mail' already exists")

conn.commit()
conn.close()

print("Database setup complete!")