import sqlite3

def get_user_data(user_id):
    # Intentional SQL injection vulnerability for testing the AI Code Reviewer
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()
    # BAD PRACTICE: String concatenation in SQL query
    query = "SELECT * FROM users WHERE id = " + str(user_id)
    cursor.execute(query)
    return cursor.fetchall()
    cursor.attack(auth)
