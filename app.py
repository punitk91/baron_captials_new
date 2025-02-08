from flask import Flask, render_template, request, redirect, url_for, session, g
from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash

import sqlite3
import pandas as pd
app = Flask(__name__)
app.secret_key = 'your_secret_key'
DATABASE = 'database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    
    if user:
        session['username'] = username
        session['role'] = user[0]
        return redirect(url_for('dashboard'))
    return render_template('index.html', error='Invalid Credentials')

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        db = get_db()
        cursor = db.cursor()
        
        if session['role'] == 'superadmin':
            return redirect(url_for('superadmin_dashboard'))
        
        elif session['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))

        elif session['role'] == 'user':
            cursor.execute("SELECT id, investment_type, quantity, price FROM investments WHERE username=?", (session['username'],))
            investments = cursor.fetchall()
            return render_template('user_dashboard.html', username=session['username'], investments=investments)

    return redirect(url_for('home'))



@app.route('/superadmin_dashboard')
def superadmin_dashboard():
    if 'username' in session and session['role'] == 'superadmin':
        db = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT id, username, role FROM users")
        users = cursor.fetchall()

        cursor.execute("SELECT id, username, investment_type FROM user_interests")
        user_interests = cursor.fetchall()

        cursor.execute("SELECT id, username, investment_type, quantity, price FROM investments")
        investments = cursor.fetchall()

        return render_template('superadmin_dashboard.html', users=users, investments=investments, user_interests=user_interests)

    return redirect(url_for('home'))




@app.route('/remove_interest/<int:interest_id>')
def remove_interest(interest_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM user_interests WHERE id=?", (interest_id,))
    db.commit()
    
    flash("User interest removed!", "success")
    return redirect(url_for('superadmin_dashboard'))



@app.route('/add_user', methods=['POST'])
def add_user():
    if 'username' in session and session['role'] == 'superadmin':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
            db.commit()
        except sqlite3.IntegrityError:
            return redirect(url_for('dashboard', error="Username already exists."))
    return redirect(url_for('dashboard'))

@app.route('/delete_admin/<int:user_id>')
def delete_admin(user_id):
    if 'username' in session and session['role'] == 'superadmin':
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM users WHERE id=? AND role='admin'", (user_id,))
        db.commit()
    return redirect(url_for('dashboard'))





@app.route('/show_interest', methods=['POST'])
def show_interest():
    if 'username' in session:
        username = session['username']
        investment_type = request.form.get('investment_type')

        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO user_interests (username, investment_type) VALUES (?, ?)", (username, investment_type))
        db.commit()

        flash("Your interest has been recorded!", "success")
        return redirect(url_for('dashboard'))

    return redirect(url_for('home'))




@app.route('/download_excel')
def download_excel():
    if 'username' in session:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, investment_type, quantity, price FROM investments WHERE username=?", (session['username'],))
        investments = cursor.fetchall()
        
        df = pd.DataFrame(investments, columns=['ID', 'Type', 'Quantity', 'Price'])
        file_path = "user_portfolio.xlsx"
        df.to_excel(file_path, index=False)
        return send_file(file_path, as_attachment=True)
    return redirect(url_for('home'))


@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if 'username' in session and session['role'] == 'superadmin':
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
        db.commit()
    return redirect(url_for('dashboard'))


@app.route('/add_admin', methods=['POST'])
def add_admin():
    if 'username' in session and session['role'] == 'superadmin':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, 'admin')", (username, password))
            db.commit()
        except sqlite3.IntegrityError:
            return redirect(url_for('dashboard', error="Username already exists."))
    return redirect(url_for('dashboard'))



@app.route('/add_investment', methods=['POST'])
def add_investment():
    if 'username' in session and session['role'] == 'superadmin':
        username = request.form['username']
        investment_type = request.form['investment_type']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO investments (username, investment_type, quantity, price) VALUES (?, ?, ?, ?)",
                       (username, investment_type, quantity, price))
        db.commit()
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
