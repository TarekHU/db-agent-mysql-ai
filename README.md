# 🧠 DB Agent — MySQL-Powered AI Assistant

## 📌 Overview

**DB Agent** is an AI-powered Flask application that connects to a MySQL database, preloads its schema (tables, columns, and foreign key relationships), and allows users to interact with the database using natural language queries. It returns AI-generated SQL queries based strictly on the real schema.

Built for developers, data analysts, and QA engineers, this tool helps:

- Explore database structures  
- Auto-generate valid SQL queries  
- Understand foreign key relationships

## ⚙️ Features

* 🔗 Extracts all table names, columns, and foreign key relationships
* 🧠 Injects schema into the AI prompt to avoid hallucination
* 📝 Uses LLM (DeepSeek via OpenRouter) to generate SQL
* 💬 Clean chat interface (Arabic & English support)
* ⚡ Preloads schema at app startup for performance

---

## 📁 Project Structure

```
db-agent-app/
├── app.py                  # Flask application (main logic)
├── config.py               # DB and API credentials
├── templates/
│   └── index.html          # Chat interface
├── requirements.txt        # Python dependencies
└── README.md
```

---

## 🚀 Installation Guide

### 1. Clone the Repository

```bash
git clone https://github.com/yourname/db-agent-app.git
cd db-agent-app
```

### 2. Setup Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Your Database

Edit the `config.py` file:

```python
class Config:
    DB_HOST = "localhost"
    DB_PORT = 3306       # Default MySQL port
    DB_NAME = "your_database"
    DB_USER = "your_username"
    DB_PASSWORD = "your_password"
    OPENROUTER_API_KEY = "sk-or-xxxx"
```

---

## ▶️ Running the Application

```bash
export FLASK_APP=app.py        # Windows: set FLASK_APP=app.py
flask run
```

Then open:
📍 [http://localhost:5000](http://localhost:5000)

---

## 🧪 Example Prompt

> "Get all orders with customer name and total"

**Response**:

```sql
SELECT o.id, o.total, c.name
FROM orders o
JOIN customers c ON o.customer_id = c.id;
```

---

## 📌 Notes

* AI model: `deepseek/deepseek-r1:free` via OpenRouter
* All schema is loaded once at startup for speed and consistency
* Works well with any MySQL database
* Handles SELECT and action queries (INSERT, UPDATE, DELETE) safely

---

## 📬 Contact

For feedback or support, reach out to: \[[tarekhussien100@gmail.com](mailto:tarekhussien100@gmail.com)

---

## 📝 License

MIT License
