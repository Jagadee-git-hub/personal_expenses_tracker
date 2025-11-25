from flask import Flask, render_template, request, redirect, session, url_for, flash, send_file
import mysql.connector as conn
from unicodedata import category
from werkzeug.security import generate_password_hash as generate,check_password_hash as check
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns
import base64
import io
import os
from dotenv import load_dotenv
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'Jaga_#4216')
load_dotenv()
us_er = os.getenv('user')
passw = os.getenv('password')
data_base = os.getenv('database')
#Database connection
def get_db_connection():
    return conn.connect(
        host="localhost",
        user = us_er ,
        password= passw,
        database= data_base
    )
# --- Initialize database and tables if not exist ---
def init_db():
    temp_db = conn.connect(
        host="localhost",
        user="root",
        password="Jaga@4216"
    )
    temp_cursor = temp_db.cursor()
    temp_cursor.execute("CREATE DATABASE IF NOT EXISTS expense_tracker")
    temp_cursor.close()
    temp_db.close()

    mydb = conn.connect(
        host="localhost",
        user="root",
        password="Jaga@4216",
        database="expense_tracker"
    )
    cursor = mydb.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        )
    """)

    # Expenses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            date DATE,
            amount DECIMAL(10,2),
            category VARCHAR(100),
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    mydb.commit()
    cursor.close()
    mydb.close()

#home page routing
@app.route('/')
def home():
    return render_template('home.html')
#registration page route
@app.route('/register',methods =['GET','POST'])

def register():
    if request.method =='POST':
        email = request.form['email']
        username = request.form['username']
        password = generate(request.form['password'])

        mydb = get_db_connection()
        cursor = mydb.cursor()
        try :
            cursor.execute('''Insert Into users(username,email,password) Values
            (%s,%s,%s)''', (username,email,password))
            mydb.commit()
            flash("Registration Successful /n Login to page","success")
            return redirect(url_for('login'))
        except ValueError as e :
            flash(e+"\nuser already exists ","error")
        except Exception as e :
            flash(e+"\n please try again","error")
        finally:
            cursor.close()
            mydb.close()
    return render_template('register.html')
# login page route
@app.route('/login',methods = ['GET','POST'])
def login():
    if request.method =='POST':
        email = request.form['email']
        password = request.form['password']

        mydb = get_db_connection()
        cursor = mydb.cursor(dictionary=True)

        cursor.execute('''select * from users where email =%s''', (email,) )
        user = cursor.fetchone()
        cursor.close()
        mydb.close()
        if user and check(user['password'],password):
            session['user_id'] = user['id']
            session['userame'] = user['username']
            flash("Login succesful!","success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password","danger")
    return render_template('login.html')
#graphical representation
def save_plot():
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()
    return plot_url

def create_plot(expenses):
    df = pd.DataFrame(expenses)
    if df.empty:
        return None,None
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M')
    df['amount'] = pd.to_numeric(df['amount'])
    # Plot Expenses by Category
    if 'category' in df.columns and 'amount' in df.columns:
        category_expenses = df.groupby('category')['amount'].sum().reset_index()
        plt.figure(figsize=(10,6))
        sns.barplot(data=category_expenses, x='category', y='amount')
        plt.title('Expenses by Category')
        plt.xlabel('Category')
        plt.ylabel('Total Amount')
        category_plot = save_plot()
    else:
        category_plot = None
    if 'month' in df.columns and 'category' in df.columns and 'amount' in df.columns:
        monthly_expenses_by_category = df.groupby(['month', 'category'])['amount'].sum().reset_index()
        monthly_expenses_by_category['month'] = monthly_expenses_by_category['month'].astype(str)
        plt.figure(figsize=(10,6))
        sns.barplot(data=monthly_expenses_by_category, x='month', y='amount', hue='category')
        plt.title('Monthly Expenses by Category')
        plt.xlabel('Month')
        plt.ylabel('Total Amount')
        monthly_plot = save_plot()
    else:
        monthly_plot = None
    return category_plot,monthly_plot
#plot page route
@app.route('/graphs')
def graphs():
    if 'user_id' not in session:
        flash('please login to View Graphs','info')
        return redirect(url_for('login'))
    user_id = session['user_id']
    mydb = get_db_connection()
    cursor = mydb.cursor(dictionary=True)
    cursor.execute('''select * from expenses where user_id = %s''', (user_id,))
    expenses = cursor.fetchall()
    cursor.close()
    mydb.close()
    category_plot,monthly_plot = create_plot(expenses)
    return render_template('plots.html',expenses = expenses,
                           category_plot = category_plot,monthly_plot = monthly_plot)

#dashboard page route
@app.route('/dashboard')
def dashboard():
    if "user_id" not in session:
        flash("please login to the page ","warning")
        return redirect(url_for('login'))
    user_id = session['user_id']
    mydb = get_db_connection()
    cursor = mydb.cursor(dictionary=True)
    cursor.execute(f'''select * from expenses where user_id = {user_id}''')
    expenses = cursor.fetchall()
    total_expenses = sum(expense['amount'] for expense in expenses)
    category_expenses = {}
    monthly_expenses = {}
    for expense in expenses:
        category = expense['category']
        month = expense['date'].strftime('%B %Y')
        if category not in category_expenses:
            category_expenses[category] = 0
        if month not in monthly_expenses:
            monthly_expenses[month] = 0
        category_expenses[category] += expense['amount']
        monthly_expenses[month] += expense['amount']
    cursor.close()
    mydb.close()
    return render_template('dashboard.html',expenses = expenses,
                           total_expenses=total_expenses,category_expenses = category_expenses,
                           monthly_expenses=monthly_expenses)
@app.route('/add_expenses',methods = ['POST'])
def add_expenses():
    if 'user_id' not in session:
        flash('please login to add expenses','info')
        return redirect(url_for('login'))
    user_id = session['user_id']
    date = request.form['date']
    amount = request.form['amount']
    category = request.form['category']
    notes = request.form['notes']
    mydb = get_db_connection()
    cursor = mydb.cursor()
    try :
        cursor.execute('''Insert Into expenses(user_id,date,amount,category,notes) 
                        Values(%s,%s,%s,%s,%s)''',(user_id,date,amount,category,notes))
        mydb.commit()
        flash("Expense added successfully","info")
    except Exception as e :
        flash(str(e)+"\n Please try again","error")
    finally:
        cursor.close()
        mydb.close()
    return redirect(url_for('dashboard'))


@app.route('/export_csv')
def export_csv():
    if "user_id" not in session:
        flash("please login again ","warning")
        return redirect(url_for("login"))
    user_id = session['user_id']
    mydb = get_db_connection()
    cursor = mydb.cursor(dictionary=True)
    cursor.execute(f"select * from expenses where user_id = {user_id}")
    expenses = cursor.fetchall()
    cursor.close()
    mydb.close()
    if not expenses :
        flash("no data found ","info")
        return redirect(url_for('dashboard'))
    df = pd.DataFrame(expenses)
    df.to_csv('expenses.csv',index=False)
    return send_file('expenses.csv',as_attachment=True)
# logout page route
@app.route('/delete_expense/<int:expense_id>', methods=['POST'])
def delete_expense(expense_id):
    if 'user_id' not in session:
        flash('Please log in to delete expenses', 'info')
        return redirect(url_for('login'))

    mydb = get_db_connection()
    cursor = mydb.cursor()

    try:
        cursor.execute('DELETE FROM expenses WHERE id = %s AND user_id = %s', (expense_id, session['user_id']))
        mydb.commit()
        flash('Expense deleted successfully', 'info')
    except Exception as e:
        flash(str(e) + '\nPlease try again', 'error')
    finally:
        cursor.close()
        mydb.close()

    return redirect(url_for('dashboard'))


@app.route('/update_expense/<int:expense_id>', methods=['GET', 'POST'])
def update_expense(expense_id):
    if 'user_id' not in session:
        flash('Please log in to update expenses', 'info')
        return redirect(url_for('login'))

    mydb = get_db_connection()
    cursor = mydb.cursor(dictionary=True)

    if request.method == 'POST':
        date = request.form['date']
        amount = request.form['amount']
        category = request.form['category']
        notes = request.form['notes']

        try:
            cursor.execute('''
                UPDATE expenses 
                SET date = %s, amount = %s, category = %s, notes = %s 
                WHERE id = %s AND user_id = %s
            ''', (date, amount, category, notes, expense_id, session['user_id']))
            mydb.commit()
            flash('Expense updated successfully', 'info')
        except Exception as e:
            flash(str(e) + '\nPlease try again', 'error')
        finally:
            cursor.close()
            mydb.close()
        return redirect(url_for('dashboard'))

    cursor.execute('SELECT * FROM expenses WHERE id = %s AND user_id = %s', (expense_id, session['user_id']))
    expense = cursor.fetchone()
    cursor.close()
    mydb.close()

    return render_template('update_expense.html', expense=expense)


@app.route('/logout') 
def logout():
    session.clear()
    flash("logged out succesfully","success")
    return redirect(url_for('home'))
if __name__ == '__main__':
    init_db()
    app.run(debug =True)
