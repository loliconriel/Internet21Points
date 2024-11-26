import secrets
import requests
from flask import Flask, request, jsonify, render_template, session, redirect, flash

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# 設置後端 API 服務器的 URL
API_URL = 'http://127.0.0.1:5001'  # 假設後端服務器運行在 5001 端口

# 註冊 API
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    # 向後端的註冊 API 發送請求
    response = requests.post(f'{API_URL}/register', json={'username': username, 'password': password})

    if response.status_code == 201:
        return jsonify({'message': 'User registered successfully'}), 201
    else:
        return jsonify(response.json()), response.status_code

# 登入 API
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    # 向後端的登入 API 發送請求
    response = requests.post(f'{API_URL}/login', json={'username': username, 'password': password})

    if response.status_code == 200:
        user_data = response.json()
        session['username'] = user_data['username']
        flash('登入成功！', 'success')
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify(response.json()), response.status_code

# 登出 API
@app.route('/logout')
def logout():
    session.clear()  # 清除所有 session 資料
    flash('已登出', 'info')
    return redirect('/')

# 獲取用戶列表（示例功能）
@app.route('/users', methods=['GET'])
def get_users():
    # 向後端的用戶列表 API 發送請求
    response = requests.get(f'{API_URL}/users')

    if response.status_code == 200:
        return jsonify(response.json()), 200
    else:
        return jsonify({'error': 'Unable to fetch users'}), response.status_code

# 首頁
@app.route('/')
def home():
    if 'username' in session:
        return render_template('home.html', username=session['username'])
    else:
        return render_template('home.html')

# 註冊頁面
@app.route('/register_page')
def register_page():
    return render_template('register.html')

# 登入頁面
@app.route('/login_page')
def login_page():
    return render_template('login.html')

if __name__ == "__main__":
    app.run(debug=True, port=5000)  # 假設前端應用運行在 5000 端口
