
import streamlit as st
import pandas as pd
import psycopg2
import sqlite3
import json
import os
import re
import mysql.connector  
from generate_sql import generate_sql_from_nl  # LLM helper for Phase 2

st.set_page_config(page_title="AI -> SQL", layout="wide")
st.title("🧠 AI and SQL ")

st.sidebar.header("📡 Database Configuration")

use_demo = st.sidebar.checkbox("Use Demo Database (SQLite)", value=False)

# ✅ SESSION ID for schema filename (separate from DB username)
username = st.sidebar.text_input("Enter your name or session ID", value="guest")
if not username.strip():
    username = "guest"

# mode = st.sidebar.radio("Select Mode", ["Demo (SQLite)", "Real DB (PostgreSQL)"])

# ✅ DB details (only visible in Real mode)
if not use_demo:
    st.sidebar.header("🔌 Real Database Configuration")
    db_type = st.sidebar.selectbox("Database Type", ["SQL Server", "PostgreSQL", "MySQL", "Oracle"])
    server = st.sidebar.text_input("Server (Host/IP)", value="localhost")
    database = st.sidebar.text_input("Database Name")
    db_user = st.sidebar.text_input("Username")
    db_pass = st.sidebar.text_input("Password", type="password")
    schema = st.sidebar.text_input("Schema Name (e.g., dbo or public)", value="dbo")


# ✅ Connect and extract schema
if st.sidebar.button("🔌 Connect & Extract Schema"):
    try:
        if use_demo:
            conn = sqlite3.connect("sample_demo.db")
            df_tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
            schema_dict = {}
            for table in df_tables['name']:
                df_cols = pd.read_sql(f"PRAGMA table_info({table});", conn)
                schema_dict[table] = df_cols['name'].tolist()
        else:
            if db_type == "PostgreSQL":  # ✅ CHANGED: now branching logic
                conn = psycopg2.connect(
                    host=server,
                    database=database,
                    user=db_user,
                    password=db_pass
                )
                query = f"""
                    SELECT table_name, column_name
                    FROM information_schema.columns
                    WHERE table_schema = '{schema}'
                    ORDER BY table_name, ordinal_position;
                """
                df = pd.read_sql(query, conn)
                schema_dict = {}
                for table in df['table_name'].unique():
                    schema_dict[table] = df[df['table_name'] == table]['column_name'].tolist()

            elif db_type == "MySQL":
                conn = mysql.connector.connect(
                    host=server,
                    database=database,
                    user=db_user,
                    password=db_pass,
                    port=3306  # ✅ DEFAULT port for MySQL
                )
                cursor = conn.cursor()
                cursor.execute("SHOW TABLES;")
                tables = cursor.fetchall()
                schema_dict = {}
                for table_tuple in tables:
                    table = table_tuple[0]
                    cursor.execute(f"DESCRIBE {table};")
                    columns = cursor.fetchall()
                    schema_dict[table] = [col[0] for col in columns]
                cursor.close()
            else:
                st.warning("❗ Unsupported DB type selected.")
                st.stop()

        # ✅ Save schema to file
        schema_file = f"schema_{username}.json"
        with open(schema_file, "w") as f:
            json.dump(schema_dict, f, indent=4)

        st.success("✅ Schema saved successfully")
        st.json(schema_dict)

    except Exception as e:
        st.error(f"❌ Connection or schema extraction failed: {e}")

# 🔵 PHASE 2 & 3: Natural Language to SQL
st.header("💬 Ask Question to Get SQL Query")

nl_query = st.text_input("Ask your question (e.g., 'Total ticket sales in May 2024')")

if st.button("🧠 Generate SQL"):
    try:
        schema_file = f"schema_{username}.json"
        if not os.path.exists(schema_file):
            st.warning("⚠️ Please connect to a database first to fetch schema.")
        else:
            with open(schema_file, "r") as f:
                schema_data = json.load(f)

            schema_str = "\n".join([f"{table}: {', '.join(cols)}" for table, cols in schema_data.items()])

            prompt = f"""
You are a helpful SQL expert. Based on the schema below, write a valid SQL query.

Schema:
{schema_str}

User Question:
{nl_query}
"""

            response = generate_sql_from_nl(prompt)

            # ✅ Clean response to extract SQL only
            match = re.search(r"```sql\s*(.*?)```", response, re.DOTALL | re.IGNORECASE)
            if match:
                sql_query = match.group(1).strip()
            else:
                sql_query = response.strip().split("```")[0].strip()
                sql_query = sql_query.split("Explanation")[0].strip()

            st.subheader("📝 Generated SQL")
            st.code(sql_query, language="sql")

            # ✅ Execute Query
            if use_demo:
                conn = sqlite3.connect("sample_demo.db")
            else:
                if db_type == "PostgreSQL":
                    conn = psycopg2.connect(
                        host=server,
                        database=database,
                        user=db_user,
                        password=db_pass
                    )
                elif db_type == "MySQL":
                    conn = mysql.connector.connect(
                        host=server,
                        database=database,
                        user=db_user,
                        password=db_pass,
                        port=3306
                    )
                else:
                    st.warning("❗ Unsupported DB type selected.")
                    st.stop()

            result_df = pd.read_sql_query(sql_query, conn)
            st.subheader("📊 Query Output")
            st.dataframe(result_df)

            # ✅ Export to CSV
            csv = result_df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download CSV", csv, "query_results.csv", "text/csv")

    except Exception as e:
        st.error(f"❌ Error running query: {e}")