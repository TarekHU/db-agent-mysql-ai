🧠 DB Agent — MySQL-Powered AI Assistant
📌 Overview

The DB Agent is an AI-powered Flask application that connects to a MySQL database, preloads its schema (tables, columns, and foreign key relationships), and allows users to interact with the database using natural language queries. It returns AI-generated SQL queries based strictly on the real schema.

Built for developers, data analysts, and QA engineers, this tool helps:

Explore database structures

Auto-generate valid SQL queries

Understand foreign key relationships

⚙️ Features

🔗 Extracts all table names, columns, and foreign key relationships

🧠 Injects schema into the AI prompt to avoid hallucination

📝 Uses LLM (OpenRouter GPT-4o-mini) to generate SQL

💬 Clean chat interface with English support

⚡ Preloads schema at app startup for fast responses

📥 Export query results to Excel

📁 Project Structure
db-agent-app/
├── app.py                  # Flask application (main logic)
├── config.py               # DB and API credentials
├── templates/
│   └── index.html          # Chat interface
├── requirements.txt        # Python dependencies
└── README.md

🚀 Installation Guide
1. Clone the Repository
git clone https://github.com/yourname/db-agent-app.git
cd db-agent-app

2. Setup Virtual Environment
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

3. Install Dependencies
pip install -r requirements.txt

4. Configure Your Database

Edit the config.py file:

class Config:
    DB_HOST = "localhost"
    DB_PORT = 3306                # Default MySQL port
    DB_NAME = "your_database"
    DB_USER = "your_username"
    DB_PASSWORD = "your_password"
    OPENROUTER_API_KEY = "sk-or-xxxx"

▶️ Running the Application

Simply run:

python app.py


Then open:
📍 http://localhost:5000

✅ No need to set FLASK_APP since app runs directly in development mode.

💬 Using the Chat Interface

Type natural language queries like:

"Get all orders with customer name and total"

The app responds with:

SELECT o.id, o.total, c.name
FROM orders o
JOIN customers c ON o.customer_id = c.id;


If your response contains a SQL query, you can run it directly via the ⬇ Run SQL button.

You can export results to Excel using the 📥 Export to Excel button.

Clear chat history using 🗑️ Clear Chat.

📌 Notes

AI model: openai/gpt-4o-mini via OpenRouter

Schema is loaded once at startup for speed and consistency

Works with any MySQL database

Handles SELECT and action queries (INSERT, UPDATE, DELETE) safely

📬 Contact

For feedback or support, reach out to: tarekhussien100@gmail.com

📝 License (MIT)

This project is open-source and free to use. You can:

Use it for personal, commercial, or educational purposes

Copy, modify, and share it freely

Include it in your own projects

The only rules are:

Keep the original copyright notice and license in the project

The software comes “as-is” — the author isn’t responsible if something goes wrong