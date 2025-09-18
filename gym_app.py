import streamlit as st
import sqlite3
import datetime
import login

for key, default in [("user_id", None), ("page", "login"), ("name", "")]:
    if key not in st.session_state:
        st.session_state[key] = default


def run_app():
    # --- Ensure user is logged in ---
    if "user_id" not in st.session_state:
        st.error("❌ You must log in first.")
        st.stop()

    user_id = st.session_state["user_id"]

    # -------------------------
    # Database Setup
    # -------------------------
    conn = sqlite3.connect("gym_data.db", check_same_thread=False)
    c = conn.cursor()

    # Programs table
    c.execute('''CREATE TABLE IF NOT EXISTS programs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  name TEXT,
                  days INTEGER,
                  date_created TEXT)''')

    # Exercises table
    c.execute('''CREATE TABLE IF NOT EXISTS exercises
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  program_id INTEGER,
                  day INTEGER,
                  name TEXT,
                  type TEXT,
                  target_sets INTEGER,
                  target_reps INTEGER)''')

    # Workouts table
    c.execute('''CREATE TABLE IF NOT EXISTS workouts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  program_id INTEGER,
                  exercise_name TEXT,
                  date TEXT)''')

    # Workout sets table
    c.execute('''CREATE TABLE IF NOT EXISTS workout_sets
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  workout_id INTEGER,
                  set_number INTEGER,
                  reps INTEGER,
                  weight REAL)''')

    # Personal records table
    c.execute('''CREATE TABLE IF NOT EXISTS personal_records (
                    exercise_name TEXT,
                    user_id INTEGER,
                    max_weight REAL,
                    reps INTEGER DEFAULT 0,
                    PRIMARY KEY (exercise_name, user_id)
                 )''')
    conn.commit()

    # -------------------------
    # Session State Defaults
    # -------------------------
    for key in ["page", "selected_program", "selected_exercise", "current_workout"]:
        if key not in st.session_state:
            st.session_state[key] = None

    def go_to(page):
        st.session_state["page"] = page

    # -------------------------
    # Home Page
    # -------------------------
    if st.session_state["page"] == "home":
        st.title("🏋️ Personal Gym App")
        st.write(f"Hello, {st.session_state.get('user_name', st.session_state['name'])}!")
        st.write("Choose an option:")

        st.button("📅 Create a Program", on_click=lambda: go_to("create_program"))

        # Logout button
        def logout():
            for key in ["user_id", "user_name", "selected_program", "selected_exercise", "current_workout", "page"]:
                st.session_state.pop(key, None)
        st.button("🔒 Logout", on_click=logout)

        # Show existing programs
        c.execute("SELECT name, id FROM programs WHERE user_id=?", (user_id,))
        programs = c.fetchall()
        if programs:
            program_names = [p[0] for p in programs]
            selected_program_name = st.selectbox("Select Existing Program", program_names)
            def select_program():
                program_id = [p[1] for p in programs if p[0] == selected_program_name][0]
                st.session_state["selected_program"] = program_id
                go_to("program_page")
            st.button("Select Program", on_click=select_program)

    # -------------------------
    # Create Program Page
    # -------------------------
    elif st.session_state["page"] == "create_program":
        st.header("📅 Create a New Program")
        st.text_input("Program Name", key="prog_name_input")
        st.number_input("Number of Days (1–7)", min_value=1, max_value=7, step=1, key="prog_days_input")

        def create_program_callback():
            prog_name = st.session_state.get("prog_name_input")
            prog_days = st.session_state.get("prog_days_input")
            if prog_name:
                c.execute(
                    "INSERT INTO programs (user_id, name, days, date_created) VALUES (?, ?, ?, ?)",
                    (user_id, prog_name, prog_days, str(datetime.date.today()))
                )
                conn.commit()
                st.success(f"✅ Program '{prog_name}' created!")

        st.button("Create Program", on_click=create_program_callback)
        st.button("⬅️ Back to Home", on_click=lambda: go_to("home"))

    # -------------------------
    # Program Page
    # -------------------------
    elif st.session_state["page"] == "program_page":
        prog_id = st.session_state["selected_program"]
        c.execute("SELECT name, days FROM programs WHERE id=? AND user_id=?", (prog_id, user_id))
        result = c.fetchone()
        if result:
            prog_name, prog_days = result
            st.header(f"📋 Program: {prog_name} ({prog_days} days)")
        else:
            st.error("❌ Program not found.")
            st.button("⬅️ Back to Home", on_click=lambda: go_to("home"))
            return

        st.subheader("Options:")
        st.button("➕ Add Exercises", on_click=lambda: go_to("add_exercises"))
        st.button("💪 Log Workout", on_click=lambda: go_to("log_workout"))
        st.button("📖 View Exercises & Stats", on_click=lambda: go_to("view_program_exercises"))
        st.button("🗑️ Delete This Program", on_click=lambda: go_to("delete_program"))
        st.button("⬅️ Back to Home", on_click=lambda: go_to("home"))

    # -------------------------
    # Add Exercises
    # -------------------------
    elif st.session_state["page"] == "add_exercises":
        prog_id = st.session_state["selected_program"]
        c.execute("SELECT name, days FROM programs WHERE id=? AND user_id=?", (prog_id, user_id))
        result = c.fetchone()
        if result:
            prog_name, prog_days = result
            st.header(f"➕ Add Exercises to Program: {prog_name}")
        else:
            st.error("❌ Program not found.")
            st.button("⬅️ Back to Home", on_click=lambda: go_to("home"))
            return

        day_choice = st.selectbox("Day of Program", list(range(1, prog_days + 1)))
        st.text_input("Exercise Name", key="ex_name_input")
        st.radio("Exercise Type", ["Strength", "Cardio"], key="ex_type_input")

        if st.session_state["ex_type_input"] == "Strength":
            st.number_input("Target Sets", min_value=1, step=1, key="target_sets_input")
            st.number_input("Target Reps per set", min_value=1, step=1, key="target_reps_input")

        def add_exercise_callback():
            ex_name = st.session_state.get("ex_name_input")
            ex_type = st.session_state.get("ex_type_input")
            sets = st.session_state.get("target_sets_input")
            reps = st.session_state.get("target_reps_input")
            if ex_name:
                c.execute(
                    "INSERT INTO exercises (user_id, program_id, day, name, type, target_sets, target_reps) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (user_id, prog_id, day_choice, ex_name, ex_type, sets, reps)
                )
                conn.commit()
                st.success(f"✅ Added exercise '{ex_name}' to Day {day_choice}")

        st.button("Add Exercise", on_click=add_exercise_callback)
        st.button("⬅️ Back to Program Page", on_click=lambda: go_to("program_page"))

    # -------------------------
    # Delete Program
    # -------------------------
    elif st.session_state["page"] == "delete_program":
        prog_id = st.session_state["selected_program"]
        c.execute("SELECT name FROM programs WHERE id=? AND user_id=?", (prog_id, user_id))
        result = c.fetchone()
        if result:
            prog_name = result[0]
            st.write(f"Are you sure you want to delete '{prog_name}'?")

            def delete_program_callback():
                c.execute("DELETE FROM programs WHERE id=? AND user_id=?", (prog_id, user_id))
                conn.commit()
                st.success(f"✅ Program '{prog_name}' deleted!")
                st.session_state["selected_program"] = None
                go_to("home")

            st.button("Delete Program", on_click=delete_program_callback)
        else:
            st.error("❌ Program not found.")

        st.button("⬅️ Back to Program Page", on_click=lambda: go_to("program_page"))

    # -------------------------
    # View Exercises & Stats
    # -------------------------
    # -------------------------
# View Exercises & Stats
# -------------------------
    elif st.session_state["page"] == "view_program_exercises":
        prog_id = st.session_state["selected_program"]
        c.execute("SELECT name, days FROM programs WHERE id=? AND user_id=?", (prog_id, st.session_state["user_id"]))
        result = c.fetchone()
        if result:
            prog_name, prog_days = result
            st.header(f"📖 Exercises & Stats - {prog_name}")
        else:
            st.error("❌ Program not found for this user.")
            st.button("⬅️ Back to Home", on_click=lambda: st.session_state.update({"page": "home"}))
    
        # Callback to go to exercise details
        def show_exercise_details(ex_name):
            st.session_state["selected_exercise"] = ex_name
            st.session_state["page"] = "exercise_details"
    
        for day in range(1, prog_days + 1):
            st.subheader(f"Day {day}")
            c.execute("SELECT * FROM exercises WHERE program_id=? AND day=? AND user_id=?", (prog_id, day, st.session_state["user_id"]))
            exercises = c.fetchall()
            if exercises:
                for ex in exercises:
                    _, _, _, _, ex_name, ex_type, t_sets, t_reps = ex
                    col1, col2 = st.columns([6,1])
                    col1.write(f"- {ex_name} [{ex_type}]")
                    if ex_type == "Strength" and t_sets and t_reps:
                        col1.caption(f"Target: {t_sets} sets × {t_reps} reps")
                    # PR
                    c.execute("SELECT max_weight, reps FROM personal_records WHERE exercise_name=? AND user_id=?", (ex_name, st.session_state["user_id"]))
                    pr = c.fetchone()
                    if pr:
                        col1.caption(f"🏆 PR: {pr[0]} kg × {pr[1]} reps")
                    # Info button
                    col2.button(
                        "ℹ️",
                        key=f"info_{day}_{ex_name}",
                        on_click=show_exercise_details,
                        args=(ex_name,)
                    )
            else:
                st.write("No exercises added yet.")
    
        st.button("⬅️ Back to Program Page", on_click=lambda: st.session_state.update({"page": "program_page"}))


# -------------------------
# Exercise Details Page
# -------------------------
    elif st.session_state["page"] == "exercise_details":
        user_id = st.session_state["user_id"]
        prog_id = st.session_state["selected_program"]
        ex_name = st.session_state.get("selected_exercise")
    
        if not ex_name:
            st.error("No exercise selected.")
        else:
            st.header(f"📋 Exercise Details: {ex_name}")
    
            # Fetch exercise info (type & targets)
            c.execute("SELECT type, target_sets, target_reps FROM exercises WHERE program_id=? AND name=? AND user_id=?", (prog_id, ex_name, user_id))
            ex_info = c.fetchone()
            if ex_info:
                ex_type, target_sets, target_reps = ex_info
                st.subheader("Exercise Info")
                st.write(f"Type: **{ex_type}**")
                if ex_type == "Strength":
                    st.write(f"Target: **{target_sets} sets × {target_reps} reps**")
            else:
                st.warning("Exercise not found in this program.")
    
            # Personal Record
            c.execute("SELECT max_weight, reps FROM personal_records WHERE exercise_name=? AND user_id=?", (ex_name, user_id))
            pr = c.fetchone()
            st.subheader("🏆 Personal Record")
            if pr:
                st.write(f"**{pr[0]} kg × {pr[1]} reps**")
            else:
                st.write("No personal record recorded yet.")
    
            # Workout History
            c.execute("""
                SELECT w.date, ws.set_number, ws.reps, ws.weight
                FROM workouts w
                JOIN workout_sets ws ON w.id = ws.workout_id
                WHERE w.exercise_name=? AND w.user_id=?
                ORDER BY w.date ASC, ws.set_number ASC
            """, (ex_name, user_id))
            logs = c.fetchall()
    
            st.subheader("📝 Workout History")
            if logs:
                current_date = None
                for log in logs:
                    date, set_number, reps, weight = log
                    if date != current_date:
                        st.markdown(f"**Date: {date}**")
                        current_date = date
                    st.write(f"Set {set_number}: {weight} kg × {reps} reps")
            else:
                st.write("No workout logs yet.")
    
            # Back button
            st.button("⬅️ Back to Program Exercises", on_click=lambda: st.session_state.update({"page": "view_program_exercises"}))


    # -------------------------
    # Log Workout Page
    # -------------------------
    elif st.session_state["page"] == "log_workout":
        prog_id = st.session_state["selected_program"]
        c.execute("SELECT name, days FROM programs WHERE id=? AND user_id=?", (prog_id, user_id))
        result = c.fetchone()
        if result:
            prog_name, prog_days = result
            st.header(f"💪 Log Workout - {prog_name}")
        else:
            st.error("❌ Program not found.")
            st.button("⬅️ Back to Home", on_click=lambda: go_to("home"))
            return

        # Fetch exercises
        c.execute("SELECT id, day, name, type, target_sets, target_reps FROM exercises WHERE program_id=? AND user_id=?", (prog_id, user_id))
        exercises = c.fetchall()
        if exercises:
            ex_names_display = [f"{e[2]} [{e[3]}] (Day {e[1]})" for e in exercises]
            selected_ex_display = st.selectbox("Choose Exercise", ex_names_display)
            ex_row = exercises[ex_names_display.index(selected_ex_display)]
            ex_id, day, ex_name, ex_type, target_sets, target_reps = ex_row

            today = str(datetime.date.today())

            def start_workout():
                c.execute("INSERT INTO workouts (user_id, program_id, exercise_name, date) VALUES (?, ?, ?, ?)",
                          (user_id, prog_id, ex_name, today))
                workout_id = c.lastrowid
                conn.commit()
                st.session_state["current_workout"] = {
                    "id": workout_id,
                    "exercise_name": ex_name,
                    "type": ex_type,
                    "target_sets": target_sets,
                    "target_reps": target_reps
                }

            if not st.session_state.get("current_workout") or st.session_state["current_workout"].get("exercise_name") != ex_name:
                st.button("Start Logging", on_click=start_workout)

            workout = st.session_state.get("current_workout")
            if workout and workout.get("exercise_name") == ex_name:
                st.subheader(f"Logging: {ex_name} [{ex_type}]")

                if ex_type == "Strength":
                    st.info(f"📌 Target: {target_sets} sets × {target_reps} reps")
                    num_sets = st.number_input("Number of sets performed", min_value=1, step=1, key="num_sets_input")
                    reps_inputs, weight_inputs = [], []

                    for s in range(1, num_sets + 1):
                        st.write(f"Set {s}")
                        reps = st.number_input(f"Reps (Set {s})", min_value=1, step=1, key=f"reps_{s}")
                        weight = st.number_input(f"Weight (kg, Set {s})", min_value=0.0, step=0.5, key=f"weight_{s}")
                        reps_inputs.append(reps)
                        weight_inputs.append(weight)

                    def save_strength_callback():
                        for idx, (r, w) in enumerate(zip(reps_inputs, weight_inputs), start=1):
                            c.execute("""INSERT INTO workout_sets (user_id, workout_id, set_number, reps, weight)
                                         VALUES (?, ?, ?, ?, ?)""",
                                      (user_id, workout["id"], idx, r, w))
                            # Update PR
                            c.execute("SELECT max_weight, reps FROM personal_records WHERE exercise_name=? AND user_id=?",
                                      (ex_name, user_id))
                            record = c.fetchone()
                            if record is None or w > record[0]:
                                c.execute("""REPLACE INTO personal_records (user_id, exercise_name, max_weight, reps)
                                             VALUES (?, ?, ?, ?)""",
                                          (user_id, ex_name, w, r))
                        conn.commit()
                        st.success("✅ Strength workout saved!")
                        st.session_state["current_workout"] = None

                    st.button("Save Strength Workout", on_click=save_strength_callback)

                elif ex_type == "Cardio":
                    distance = st.number_input("Distance (km)", min_value=0.0, step=0.1, key="cardio_distance")
                    duration = st.number_input("Duration (minutes)", min_value=0.0, step=1.0, key="cardio_duration")

                    def save_cardio_callback():
                        c.execute("""INSERT INTO workout_sets (user_id, workout_id, set_number, reps, weight)
                                     VALUES (?, ?, ?, ?, ?)""",
                                  (user_id, workout["id"], 1, int(duration), distance))
                        conn.commit()
                        st.success("✅ Cardio workout saved!")
                        st.session_state["current_workout"] = None

                    st.button("Save Cardio Workout", on_click=save_cardio_callback)

        else:
            st.info("No exercises available. Add some first.")

        st.button("⬅️ Back to Program Page", on_click=lambda: go_to("program_page"))

if st.session_state["user_id"] is None:
    login.show_login()
else:
    run_app()
