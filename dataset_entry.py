import pandas as pd
import mysql.connector as conn

# Read your dataset
data1 = pd.read_csv(r"E:\Pycharm\ReviewFlask\expense_tracker\dataset_expenses.txt")

def get_db_connection():
    """Ensure database and table exist, then return active connection."""
    # Step 1: connect without database first
    temp_db = conn.connect(
        host="localhost",
        user="root",
        password="Jaga@4216"
    )
    temp_cursor = temp_db.cursor()
    temp_cursor.execute("CREATE DATABASE IF NOT EXISTS expense_tracker")
    temp_cursor.close()
    temp_db.close()

    # Step 2: reconnect with the created database
    mydb = conn.connect(
        host="localhost",
        user="root",
        password="Jaga@4216",
        database="expense_tracker"
    )
    cursor = mydb.cursor()

    # Step 3: create the table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INT PRIMARY KEY,
            date DATE,
            amount DECIMAL(10,2),
            category VARCHAR(100),
            notes TEXT,
            user_id INT
        )
    """)
    cursor.close()
    return mydb


# --- MAIN EXECUTION ---
mydb = get_db_connection()
cursor = mydb.cursor()

# Step 4: Insert all rows
for index, row in data1.iterrows():
    query = '''INSERT INTO expenses (id, date, amount, category, notes, user_id)
               VALUES (%s, %s, %s, %s, %s, %s)
               ON DUPLICATE KEY UPDATE
               date=VALUES(date), amount=VALUES(amount),
               category=VALUES(category), notes=VALUES(notes),
               user_id=VALUES(user_id)'''
    values = (row['id'], row['date'], row['amount'], row['category'], row['notes'], row['user_id'])
    cursor.execute(query, values)

# Step 5: Save and close
mydb.commit()
cursor.close()
mydb.close()

print("✅ Data successfully inserted into MySQL!")
