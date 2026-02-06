import streamlit as st
from datetime import date

st.set_page_config(
    page_title="Daily Organization",
    page_icon="🧠",
    layout="wide"
)

# HEADER
st.title("🧠 Daily Organization")
st.caption("Your calm place to organize your life")
st.write(f"📅 {date.today()}")

st.divider()

# COLUMNAS
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

    # 🧠 HABITS SECTION
    st.subheader("✅ Habits – Today")

    h1 = st.checkbox("Water 💧", key="habit_water")
    h2 = st.checkbox("Exercise 🏋️‍♀️", key="habit_exercise")
    h3 = st.checkbox("Skincare 🧴", key="habit_skincare")

    completed = sum([h1, h2, h3])
    total = 3

    st.progress(completed / total)
    st.caption(f"{completed} / {total} habits completed")

    if st.button("📊 Open habits tracker"):
        st.info("➡️ Go to the Habits section from the sidebar")

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
