import streamlit as st
import sqlite3
from gym_app import run_app  # gym app code wrapped in run_app()

# --- Database ---
conn = sqlite3.connect("gym_data.db", check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER,
              name TEXT,
              age INTEGER,
              weight REAL,
              mail TEXT UNIQUE,
              code TEXT)''')
conn.commit()

# --- Initialize session_state keys ---
for key in ["user_id", "page", "name"]:
    if key not in st.session_state:
        st.session_state[key] = None if key=="user_id" else ""

# --- Login / Signup ---
if st.session_state["user_id"] is None:
    choice = st.radio("Login / Sign Up", ["Login", "Sign Up"])

    if choice == "Sign Up":
        name = st.text_input("Name")
        age = st.number_input("Age", min_value=1)
        kilos = st.number_input("Weight (kg)", min_value=1.0)
        mail = st.text_input("Email")
        code = st.text_input("Password", type="password")

        def signup_callback():
            try:
                c.execute("INSERT INTO users (name, age, weight, mail, code) VALUES (?, ?, ?, ?, ?)",
                          (name, age, kilos, mail, code))
                conn.commit()
                st.success("✅ Account created! Please log in.")
            except sqlite3.IntegrityError:
                st.error("❌ Email already exists.")

        st.button("Create Account", on_click=signup_callback)

    else:  # Login
        mail = st.text_input("Email")
        code = st.text_input("Password", type="password")

       
        def login_callback():
            c.execute("SELECT id, name FROM users WHERE mail=? AND code=?", (mail, code))
            user = c.fetchone()
            if user:
                st.session_state["user_id"] = user[0]
                st.session_state["name"] = user[1]
                st.session_state["page"] = "home"  # navigate to home page
                st.success("✅ Logged in!")
                # No need for experimental_rerun()
            else:
                st.error("❌ Invalid email or password.")

        st.button("Login", on_click=login_callback)

# --- Already logged in ---
else:
    run_app()
