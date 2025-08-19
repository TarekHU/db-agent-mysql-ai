from flask import Flask, request, jsonify, render_template, session
from flask_session import Session
from collections import defaultdict
import requests
import pymysql
import traceback

from config import Config

# -----------------------------------------------------------------------------
# Flask App Setup
# -----------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = "super-secret-key"

# Sessions stored on server filesystem
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Force development mode (no need for `export FLASK_APP`)
app.config["ENV"] = "development"
app.config["DEBUG"] = True

# -----------------------------------------------------------------------------
# Globals
# -----------------------------------------------------------------------------
schema_columns = ""
schema_relationships = ""
last_generated_sql = None  # Stores the last generated SQL query

# -----------------------------------------------------------------------------
# DB Connection
# -----------------------------------------------------------------------------
def connect_db():
    """Connect to MySQL using config."""
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

# -----------------------------------------------------------------------------
# Preload Schema
# -----------------------------------------------------------------------------
def preload_schema():
    """Load DB schema (tables, columns, FKs) into memory at startup."""
    global schema_columns, schema_relationships
    conn = None
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Foreign key relationships
        fk_query = """
            SELECT 
                TABLE_NAME AS fk_table,
                COLUMN_NAME AS fk_column,
                REFERENCED_TABLE_NAME AS referenced_table,
                REFERENCED_COLUMN_NAME AS referenced_column
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE REFERENCED_TABLE_NAME IS NOT NULL
              AND TABLE_SCHEMA = %s
            ORDER BY TABLE_NAME, COLUMN_NAME
        """
        cursor.execute(fk_query, (Config.DB_NAME,))
        fk_results = cursor.fetchall()

        schema_relationships = "\n".join(
            f"- {row['fk_table']}.{row['fk_column']} → {row['referenced_table']}.{row['referenced_column']}"
            for row in fk_results
        ) or "No foreign key relationships found."

        # Table columns
        col_query = """
            SELECT 
                TABLE_SCHEMA,
                TABLE_NAME,
                COLUMN_NAME,
                DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s
            ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION
        """
        cursor.execute(col_query, (Config.DB_NAME,))
        col_results = cursor.fetchall()

        table_columns = defaultdict(list)
        for row in col_results:
            table_key = f"{row['TABLE_SCHEMA']}.{row['TABLE_NAME']}"
            table_columns[table_key].append(f"{row['COLUMN_NAME']} ({row['DATA_TYPE']})")

        schema_columns = "\n".join(
            f"\n📄 {table}:\n  " + "\n  ".join(cols)
            for table, cols in table_columns.items()
        )

        print("✅ Schema loaded at startup")

    except Exception as e:
        print(f"❌ Failed to preload schema: {e}")
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

# -----------------------------------------------------------------------------
# Chat with LLM (OpenRouter API)
# -----------------------------------------------------------------------------
def chat_with_local_model(prompt, user_input, token):
    """Send user request + schema prompt to OpenRouter API."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    data = {
        "model": "openai/gpt-4o-mini",  # Change to another if needed
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_input}
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get_response", methods=["POST"])
def get_response():
    """Handle user request and generate SQL using AI."""
    global last_generated_sql
    user_input = request.form.get("user_input")

    # Load history
    chat_history = session.get("chat_history", [])

    # If user wants to execute last SQL
    if user_input.strip().lower() == "/execute":
        if last_generated_sql:
            return execute_sql_and_return(last_generated_sql)
        return jsonify({"error": "❌ No SQL query to execute. Please generate one first."}), 400

    # Build history context
    history_prompt = "".join(
        f"\n💬 User: {msg[1]}" if msg[0] == "user" else f"\n🤖 DB Agent: {msg[1]}"
        for msg in chat_history
    )

    # System prompt
    prompt = f"""
You are a DB Agent connected to a MySQL database.

Use ONLY the real schema below when answering queries. Never guess.

🔗 Foreign Key Relationships:
{schema_relationships}

📘 Table Columns:
{schema_columns}

📜 Conversation so far:
{history_prompt}

💬 New User Request:
{user_input}

🎯 Format your reply like this:
Explanation
SQL:
<valid query>
"""

    try:
        response_text = chat_with_local_model(prompt, user_input, Config.OPENROUTER_API_KEY)

        # Save chat history
        chat_history.append(("user", user_input))
        chat_history.append(("bot", response_text))
        session["chat_history"] = chat_history

        # Capture SQL
        if "SQL:" in response_text:
            last_generated_sql = response_text.split("SQL:")[-1].strip().replace("```sql", "").replace("```", "").strip()

        return jsonify({"response": response_text})

    except Exception as e:
        error_msg = f"❌ Error in /get_response: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        return jsonify({"error": error_msg}), 500

@app.route("/clear_history", methods=["POST"])
def clear_history():
    session.pop("chat_history", None)
    return jsonify({"message": "✅ History cleared."})

@app.route("/run_sql", methods=["POST"])
def run_sql():
    sql_query = request.form.get("sql_query")
    return execute_sql_and_return(sql_query)

# -----------------------------------------------------------------------------
# SQL Executor with Retry
# -----------------------------------------------------------------------------
def execute_sql_and_return(sql_query, retry=True):
    """Execute SQL safely, retry via AI if it fails."""
    global last_generated_sql
    conn = None
    try:
        # Remove Markdown code fences if present
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

        conn = connect_db()
        cursor = conn.cursor()

        if sql_query.lower().startswith("select"):
            cursor.execute(sql_query)
            rows = cursor.fetchall()
            return jsonify({"type": "select", "results": rows})
        else:
            cursor.execute(sql_query)
            conn.commit()
            return jsonify({"type": "action", "message": "✅ Query executed successfully."})

    except Exception as e:
        error_msg = f"❌ SQL execution failed: {str(e)}"
        print(error_msg)
        traceback.print_exc()

        # Retry with AI only once
        if retry and last_generated_sql:
            try:
                fix_prompt = f"""
The following SQL query failed with error: {str(e)}

SQL:
{last_generated_sql}

Please suggest a corrected version of this query based ONLY on the schema.
"""
                fixed_response = chat_with_local_model(
                    f"Schema:\n{schema_columns}\nRelationships:\n{schema_relationships}",
                    fix_prompt,
                    Config.OPENROUTER_API_KEY
                )

                if "SQL:" in fixed_response:
                    fixed_sql = fixed_response.split("SQL:")[-1].strip().replace("```sql", "").replace("```", "").strip()
                    last_generated_sql = fixed_sql
                    print(f"🔄 Retrying with fixed SQL: {fixed_sql}")
                    return execute_sql_and_return(fixed_sql, retry=False)

                return jsonify({"error": error_msg, "ai_response": fixed_response}), 500

            except Exception as retry_err:
                retry_msg = f"❌ Retry with AI failed: {str(retry_err)}"
                print(retry_msg)
                traceback.print_exc()
                return jsonify({"error": error_msg, "retry_error": retry_msg}), 500

        return jsonify({"error": error_msg}), 500

    finally:
        if conn:
            conn.close()

# -----------------------------------------------------------------------------
# Startup
# -----------------------------------------------------------------------------
with app.app_context():
    preload_schema()

if __name__ == "__main__":
    # Just run: python app.py
    app.run(host="0.0.0.0", port=5000, debug=True)
