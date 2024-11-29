import requests
import secrets
import threading
from flask import Flask, render_template, session, redirect, url_for, request, flash

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
API_URL = 'http://127.0.0.1:5001'


@app.route('/')
def home():
    """首頁"""
    username = session.get('username')
    money = session.get('money')
    return render_template('home.html', username=username,money = money)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """註冊頁面及提交"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # 使用 json 方式發送資料
        response = requests.post(f'{API_URL}/register', json={'username': username, 'password': password})

        if response.status_code == 201:
            flash('註冊成功！', 'success')
            # 註冊成功後跳轉回首頁
            return redirect(url_for('home'))
        else:
            flash('註冊失敗：' + response.json().get('error', 'Unknown Error'), 'danger')
            return redirect(url_for('register'))
    return render_template('register.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    """登入頁面及提交"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # 使用 json 方式發送資料
        response = requests.post(f'{API_URL}/login', json={'username': username, 'password': password})

        if response.status_code == 200:
            session['username'] = username

            # 調用後端 /balance API 獲取金額並存入 session
            balance_response = requests.get(f'{API_URL}/balance', params={'username': username})
            if balance_response.status_code == 200:
                session['money'] = balance_response.json().get('money', '0')
            else:
                session['money'] = '0'

            flash('登入成功！', 'success')
            return redirect(url_for('home'))
        else:
            flash('登入失敗：' + response.json().get('error', 'Unknown Error'), 'danger')
    return render_template('login.html')

@app.route('/balance', methods=['GET'])
def balance():
    """查看當前金額"""
    username = session.get('username')

    if not username:
        return 0

    # 調用後端的 /balance API
    response = requests.get(f'{API_URL}/balance', params={'username': username})

    if response.status_code == 200:
        flash('無法獲取金額：' + response.json().get('error', 'Unknown Error'), 'danger')
        money = response.json().get('money')
        return render_template('/home', username=username, money=money)
    else:
        flash('無法獲取金額：' + response.json().get('error', 'Unknown Error'), 'danger')
        return redirect(url_for('home'))
@app.route('/logout')
def logout():
    """登出並重定向到首頁"""
    session.clear()
    return redirect(url_for('home'))

@app.route('/blackjackRoom')
def blackjackRoom():
    return render_template('/blackjackRoom.html')


if __name__ == "__main__":
    app.run(debug=True, port=5000)
