import streamlit as st
import pandas as pd
from datetime import date

from database import init_db, get_conn
from habits_page import habits_page

# -------------------- CONFIG --------------------
st.set_page_config(page_title="Daily Organization", page_icon="🧠", layout="wide")

init_db()  # asegura tablas
today = date.today().isoformat()

# -------------------- HELPERS --------------------
def load_active_habits(conn):
    return pd.read_sql_query(
        "SELECT id, name, category FROM habits WHERE active=1 ORDER BY id ASC",
        conn
    )

def load_today_done_map(conn, day):
    df = pd.read_sql_query(
        "SELECT habit_id, done FROM habit_logs WHERE day=?",
        conn,
        params=(day,)
    )
    return {int(r["habit_id"]): int(r["done"]) for _, r in df.iterrows()}

def upsert_habit_log(conn, habit_id: int, day: str, done: int):
    conn.execute(
        """
        INSERT INTO habit_logs (habit_id, day, done)
        VALUES (?, ?, ?)
        ON CONFLICT(habit_id, day) DO UPDATE SET done=excluded.done
        """,
        (habit_id, day, done)
    )
    conn.commit()

def create_habit(conn, name: str, category: str):
    conn.execute(
        "INSERT INTO habits (name, category, active) VALUES (?, ?, 1)",
        (name.strip(), category)
    )
    conn.commit()

# -------------------- NAV STATE --------------------
if "page" not in st.session_state:
    st.session_state.page = "🏠 Dashboard"

# Sidebar nav
st.sidebar.title("🧠 DailyOrganization")
choice = st.sidebar.radio("Ir a:", ["🏠 Dashboard", "✅ Hábitos"], index=0 if st.session_state.page == "🏠 Dashboard" else 1)
st.session_state.page = choice

# -------------------- DASHBOARD --------------------
def dashboard_page():
    conn = get_conn()

    # HEADER
    st.title("🧠 Daily Organization")
    st.caption("Your calm place to organize your life")
    st.write(f"📅 {date.today()}")

    st.divider()

    col1, col2 = st.columns(2)

    # -------- LEFT COLUMN --------
    with col1:
        st.subheader("⭐ Top 3 priorities")
        st.text_input("1️⃣ Most important task")
        st.text_input("2️⃣ Second priority")
        st.text_input("3️⃣ Third priority")

        st.divider()

        st.subheader("📌 Routine today")
        st.checkbox("Drink water 💧")
        st.checkbox("Move my body 🏃‍♀️")
        st.checkbox("Self-care 🌸")
        st.checkbox("Sleep well 😴")

        st.divider()

        # ✅ HABITS BLOCK (REAL)
        st.subheader("✅ Habits – Today")

        habits = load_active_habits(conn)

        if habits.empty:
            st.info("No tienes hábitos aún. Crea uno aquí mismo 👇")
        else:
            done_map = load_today_done_map(conn, today)

            completed = 0
            total = len(habits)

            for _, h in habits.iterrows():
                hid = int(h["id"])
                default = bool(done_map.get(hid, 0))
                checked = st.checkbox(
                    f"{h['name']}  ·  _{h['category']}_",
                    value=default,
                    key=f"dash_habit_{hid}"
                )
                upsert_habit_log(conn, hid, today, 1 if checked else 0)
                completed += 1 if checked else 0

            if total > 0:
                st.progress(completed / total)
                st.caption(f"{completed} / {total} habits completed today")

        # Quick actions
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📊 Open habits tracker", use_container_width=True):
                st.session_state.page = "✅ Hábitos"
                st.rerun()
        with c2:
            if st.button("➕ Add new habit", use_container_width=True):
                st.session_state.show_add_habit = True

        # Quick add form (inline)
        if st.session_state.get("show_add_habit", False):
            with st.expander("➕ Add a habit (quick)", expanded=True):
                new_name = st.text_input("Habit name", placeholder="Ej: Skincare AM / Inglés / 8k pasos", key="new_habit_name")
                new_cat = st.selectbox("Category", ["General", "Salud", "Estudio", "Ejercicio", "Skincare", "Casa", "Trabajo"], key="new_habit_cat")

                cols = st.columns(2)
                with cols[0]:
                    if st.button("Create habit ✅"):
                        if new_name.strip():
                            create_habit(conn, new_name, new_cat)
                            st.success("Hábito creado 💛")
                            st.session_state.show_add_habit = False
                            st.rerun()
                        else:
                            st.warning("Pon un nombre primero.")
                with cols[1]:
                    if st.button("Cancel"):
                        st.session_state.show_add_habit = False
                        st.rerun()

    # -------- RIGHT COLUMN --------
    with col2:
        st.subheader("⏰ Focus of the day")
        st.radio(
            "Choose your main focus",
            ["University / Work", "Health", "Projects", "Rest"],
            horizontal=True
        )

        st.divider()

        st.subheader("📂 Projects – one small action")
        st.text_input("Tesis")
        st.text_input("Startup")
        st.text_input("English / Personal growth")

        st.divider()

        st.subheader("🍽️ Meals & Inventory (summary)")
        st.info("🥚 Low inventory: eggs, rice")

        st.subheader("💸 Expenses (today)")
        st.metric("Spent today", "Bs 0")

    st.caption("✨ If today feels heavy, just do one small thing.")
    conn.close()

# -------------------- ROUTER --------------------
if st.session_state.page == "🏠 Dashboard":
    dashboard_page()
elif st.session_state.page == "✅ Hábitos":
    habits_page()
