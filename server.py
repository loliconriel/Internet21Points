import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)
DATABASE = 'user_data.db'

# 初始化資料庫並創建表
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS User (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                money TEXT DEFAULT '0'
            )
        ''')
        conn.commit()

# 註冊 API
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()  # 使用 get_json() 來解析 JSON 資料

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM User WHERE username = ?', (username,))
            existing_user = cursor.fetchone()
            if existing_user:
                return jsonify({'error': 'Username already exists'}), 400

            cursor.execute('INSERT INTO User (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
        return jsonify({'message': 'User registered successfully'}), 201

    except sqlite3.Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500



# 登入 API
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, username FROM User WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()

    if user:
        return jsonify({'message': 'Login successful', 'username': user[1]}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 400

# 獲取所有用戶的 API
@app.route('/users', methods=['GET'])
def get_users():
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, money FROM User')
            users = cursor.fetchall()

        return jsonify({'users': [{'id': user[0], 'username': user[1], 'money': user[2]} for user in users]}), 200
    except sqlite3.Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500
@app.route('/balance', methods=['GET'])
def get_balance():
    """獲取使用者的當前金額"""
    username = request.args.get('username')

    if not username:
        return jsonify({'error': 'Username is required'}), 400

    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT money FROM User WHERE username = ?', (username,))
            result = cursor.fetchone()

            if result:
                return jsonify({'username': username, 'money': result[0]}), 200
            else:
                return jsonify({'error': 'User not found'}), 404
    except sqlite3.Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    
@app.route('/add_money', methods=['POST'])
def add_money():
    """增加金額 API"""
    data = request.get_json()  # 從 JSON 請求中提取數據
    username = data.get('username')
    if not username:
        return jsonify({'error': '缺少用戶名參數'}), 400

    with sqlite3.connect('user_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT money FROM User WHERE username = ?', (username,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({'error': '用戶不存在'}), 404

        current_money = int(result[0])
        if current_money >= 300:
            return jsonify({'error': '金額已達到上限'}), 400

        # 增加金額
        new_money = current_money + 300
        cursor.execute('UPDATE User SET money = ? WHERE username = ?', (new_money, username))
        conn.commit()

    return jsonify({'money': new_money}), 200

if __name__ == "__main__":
    init_db()  # 啟動應用時初始化資料庫
    app.run(debug=True, port=5001)  # 假設後端服務器運行在 5001 端口
