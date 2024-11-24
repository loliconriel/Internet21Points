import sqlite3
import secrets
from flask import Flask, request, jsonify, render_template,session,redirect,flash

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
DATABASE = 'user_data.db'  # 定義資料庫名稱

# 初始化資料庫並創建表
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        # 創建 User 表，包含 money 欄位，初始值為 '0'
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS User (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                money TEXT DEFAULT '0'
            )
        ''')
        conn.commit()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            # 檢查是否已存在該用戶
            cursor.execute('SELECT id FROM User WHERE username = ?', (username,))
            existing_user = cursor.fetchone()
            if existing_user:
                return jsonify({'error': 'Username already exists'}), 400

            # 插入新用戶
            cursor.execute(
                'INSERT INTO User (username, password) VALUES (?, ?)',
                (username, password)
            )
            conn.commit()

        return jsonify({'message': 'User registered successfully'}), 201

    except sqlite3.Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

# 插入使用者資料的 API
@app.route('/add_user', methods=['POST'])
def add_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO User (username, password) VALUES (?, ?)',
            (username, password)
        )
        conn.commit()

    return jsonify({'message': 'User added successfully'}), 201

# 獲取所有使用者資料的 API
@app.route('/users', methods=['GET'])
def get_users():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, money FROM User')
        users = cursor.fetchall()

    return jsonify({'users': [{'id': user[0], 'username': user[1], 'money': user[2]} for user in users]}), 200

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return render_template('login.html', error="請輸入帳號和密碼")

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, username FROM User WHERE username = ? AND password = ?', (username, password))
            user = cursor.fetchone()

        if user:
            # 記錄用戶的登入狀態
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash('登入成功！', 'success')
            return redirect('/')
        else:
            return render_template('login.html', error="帳號或密碼錯誤")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()  # 清除所有 session 資料
    flash('已登出', 'info')
    return redirect('/')


if __name__ == "__main__":
    init_db()  # 啟動應用時初始化資料庫
    app.run(debug=True)
