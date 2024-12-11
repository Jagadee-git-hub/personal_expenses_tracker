import pandas as pd
import mysql.connector as conn
data1 = pd.read_csv("E:\Pycharm\ReviewFlask\expense_tracker\dataset_expenses.txt")

def get_db_connection():
    return conn.connect(
        host="localhost",
        user='root',
        password='Jaga$&4216',
        database='expense_tracker'
    )
mydb = get_db_connection()
cursor = mydb.cursor()
for index,row in data1.iterrows():
    rows = '''Insert Into expenses (id,date,amount,category,notes,user_id)
            values(%s,%s,%s,%s,%s,%s)'''
    values = (row['id'], row['date'], row['amount'], row['category'], row['notes'], row['user_id'])
    cursor.execute(rows,values)

mydb.commit()
cursor.close()
mydb.close()
