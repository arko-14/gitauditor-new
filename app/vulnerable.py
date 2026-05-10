import os
import sqlite3
from flask import Flask, request, render_template_string

app = Flask(__name__)

# 🔑 1. BROKEN AUTH (Hardcoded Credentials)
ADMIN_PASSWORD = "super_secret_password_123"

@app.route("/login")
def login():
    password = request.args.get("password")
    if password == ADMIN_PASSWORD:
        return "Welcome Admin!"
    return "Access Denied."

# 💉 2. SQL INJECTION (Using f-strings in Queries)
@app.route("/user")
def get_user():
    user_id = request.args.get("id")
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    # VULNERABLE: Direct string interpolation
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    return str(cursor.fetchone())

# 📜 3. XSS (Cross-Site Scripting)
@app.route("/greet")
def greet():
    name = request.args.get("name", "Guest")
    # VULNERABLE: Directly rendering user input in HTML
    template = f"<h1>Hello {name}!</h1>"
    return render_template_string(template)

# 🧠 4. LOGIC BUG (Business Logic Error)
@app.route("/withdraw")
def withdraw():
    amount = float(request.args.get("amount", 0))
    balance = 1000.0
    # LOGIC BUG: No check for negative amounts allows "depositing" via withdrawal
    new_balance = balance - amount
    return f"New Balance: {new_balance}"

# 💻 5. COMMAND INJECTION
@app.route("/ping")
def ping():
    hostname = request.args.get("host")
    # VULNERABLE: Passing user input directly to the shell
    os.system(f"ping -c 1 {hostname}")
    return "Ping initiated."

if __name__ == "__main__":
    app.run(debug=True)
