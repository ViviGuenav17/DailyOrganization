import streamlit as st
import pandas as pd
from datetime import date
import calendar

from database import get_conn, init_db

def month_days(year: int, month: int):
    _, last = calendar.monthrange(year, month)
    return list(range(1, last + 1))

def ymd(y, m, d):
    return f"{y:04d}-{m:02d}-{d:02d}"

def load_habits(conn):
    return pd.read_sql_query(
        "SELECT id, name, category FROM habits WHERE active=1 ORDER BY id ASC",
        conn
    )

def load_logs_for_month(conn, year: int, month: int):
    start = ymd(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end = ymd(year, month, last_day)

    return pd.read_sql_query(
        """
        SELECT habit_id, day, done
        FROM habit_logs
        WHERE day BETWEEN ? AND ?
        """,
        conn,
        params=(start, end)
    )

def upsert_log(conn, habit_id: int, day: str, done: int):
    conn.execute(
        """
        INSERT INTO habit_logs (habit_id, day, done)
        VALUES (?, ?, ?)
        ON CONFLICT(habit_id, day) DO UPDATE SET done=excluded.done
        """,
        (habit_id, day, done)
    )
    conn.commit()

def habits_page():
    init_db()
    conn = get_conn()

    st.header("✅ Hábitos")

    tabs = st.tabs(["📅 Hoy", "🗓️ Mes", "📊 Progreso", "⚙️ Gestionar"])

    # --- HOY ---
    with tabs[0]:
        today = date.today().isoformat()
        habits = load_habits(conn)

        if habits.empty:
            st.info("Aún no tienes hábitos activos. Ve a ⚙️ Gestionar para crear el primero.")
        else:
            logs_today = pd.read_sql_query(
                "SELECT habit_id, done FROM habit_logs WHERE day=?",
                conn, params=(today,)
            )
            done_map = {int(r["habit_id"]): int(r["done"]) for _, r in logs_today.iterrows()}

            for _, row in habits.iterrows():
                hid = int(row["id"])
                checked = st.checkbox(
                    f"{row['name']}  ·  _{row['category']}_",
                    value=bool(done_map.get(hid, 0)),
                    key=f"today_{hid}"
                )
                upsert_log(conn, hid, today, 1 if checked else 0)

    # --- MES (TABLA) ---
    with tabs[1]:
        now = date.today()
        colA, colB = st.columns(2)
        with colA:
            year = st.selectbox("Año", list(range(now.year - 2, now.year + 1)), index=2)
        with colB:
            month = st.selectbox("Mes", list(range(1, 13)), index=now.month - 1)

        habits = load_habits(conn)
        if habits.empty:
            st.info("Crea hábitos en ⚙️ Gestionar para ver la tabla mensual.")
        else:
            days = month_days(year, month)
            logs = load_logs_for_month(conn, year, month)

            grid = pd.DataFrame({"Hábito": habits["name"], "Categoría": habits["category"]})
            for d in days:
                grid[str(d)] = False

            if not logs.empty:
                day_to_col = {ymd(year, month, d): str(d) for d in days}
                id_to_name = dict(zip(habits["id"], habits["name"]))
                name_to_idx = {n: i for i, n in enumerate(grid["Hábito"].tolist())}

                for _, lg in logs.iterrows():
                    hid = int(lg["habit_id"])
                    day = lg["day"]
                    if hid in id_to_name and day in day_to_col:
                        name = id_to_name[hid]
                        grid.loc[name_to_idx[name], day_to_col[day]] = bool(int(lg["done"]))

            edited = st.data_editor(
                grid,
                use_container_width=True,
                hide_index=True,
                num_rows="fixed",
                column_config={
                    "Hábito": st.column_config.TextColumn(disabled=True),
                    "Categoría": st.column_config.TextColumn(disabled=True),
                    **{str(d): st.column_config.CheckboxColumn() for d in days}
                }
            )

            if st.button("💾 Guardar cambios del mes"):
                name_to_id = dict(zip(habits["name"], habits["id"]))
                for _, r in edited.iterrows():
                    hid = int(name_to_id[r["Hábito"]])
                    for d in days:
                        upsert_log(conn, hid, ymd(year, month, d), 1 if bool(r[str(d)]) else 0)
                st.success("Guardado 💛")

    # --- PROGRESO ---
    with tabs[2]:
        now = date.today()
        year, month = now.year, now.month
        habits = load_habits(conn)

        if habits.empty:
            st.info("Crea hábitos para ver progreso.")
        else:
            days = month_days(year, month)
            logs = load_logs_for_month(conn, year, month)

            stats = []
            for _, h in habits.iterrows():
                hid = int(h["id"])
                done_days = int(logs[(logs["habit_id"] == hid) & (logs["done"] == 1)].shape[0]) if not logs.empty else 0
                pct = round(100 * done_days / len(days), 1)
                stats.append({"Hábito": h["name"], "Categoría": h["category"], "Hechos": done_days, "Total": len(days), "%": pct})

            st.dataframe(pd.DataFrame(stats).sort_values("%", ascending=False), use_container_width=True, hide_index=True)

    # --- GESTIONAR ---
    with tabs[3]:
        st.subheader("➕ Crear hábito")
        name = st.text_input("Nombre", placeholder="Ej: Agua / Ejercicio / Skincare AM")
        category = st.selectbox("Categoría", ["General", "Salud", "Estudio", "Ejercicio", "Skincare", "Casa", "Trabajo"])

        if st.button("Crear hábito"):
            if name.strip():
                conn.execute("INSERT INTO habits (name, category, active) VALUES (?, ?, 1)", (name.strip(), category))
                conn.commit()
                st.success("Hábito creado 💛")
                st.rerun()
            else:
                st.warning("Pon un nombre primero.")

        st.divider()
        st.caption("Puedes desactivar hábitos sin borrar tu historial.")

        habits_all = pd.read_sql_query("SELECT id, name, category, active FROM habits ORDER BY id ASC", conn)
        for _, h in habits_all.iterrows():
            hid = int(h["id"])
            active = bool(int(h["active"]))
            cols = st.columns([4, 3, 2])
            cols[0].write(f"**{h['name']}**")
            cols[1].write(f"_{h['category']}_")
            if cols[2].button("Desactivar" if active else "Activar", key=f"toggle_{hid}"):
                conn.execute("UPDATE habits SET active=? WHERE id=?", (0 if active else 1, hid))
                conn.commit()
                st.rerun()

    conn.close()

