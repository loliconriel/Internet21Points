import sqlite3
from flask import Flask, request, jsonify,render_template
from flask_cors import CORS

app = Flask(__name__)
DATABASE = 'user_data.db'
CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:5000"}})
blackJackRoomList = [
    {
        'id': 1,
        'name': '房間 1',
        'capacity': 4,
        'current_players': 0,
        'description': '這是房間1的描述',
        'players': [
            # 範例玩家資料
            # {'username': 'player1', 'seat': 1, 'bet': 0, 'hand': [], 'points': 0, 'last_action_time': None}
        ],
        'dealer': {'hand': [], 'points': 0},  # 莊家的手牌與點數
        'current_turn': None,  # 當前輪到的玩家
        'turn_start_time': None  # 當前玩家開始計時的時間
    },
    # 其他房間資料結構類似
]
# 初始化資料庫並創建表
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS User (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                money TEXT DEFAULT '20'
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
    """增加金額"""
    data = request.json
    username = data.get('username')
    if not username:
        return jsonify({"error": "未提供用戶名"}), 400

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT money FROM User WHERE username = ?", (username,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "用戶不存在"}), 404

        # 將金額字串轉為數字進行加法運算
        current_money = int(user[0])
        new_money = min(current_money + 300, 300)  # 最大限制為 300
        new_money_str = str(new_money)  # 回存為字串

        cursor.execute("UPDATE User SET money = ? WHERE username = ?", (new_money_str, username))
        conn.commit()

    return jsonify({"money": new_money_str})  # 回傳字串金額

@app.route('/get_money', methods=['GET'])
def get_money():
    """獲取用戶的金額資訊"""
    username = request.args.get('username')

    if not username:
        return jsonify({'error': '未提供用戶名'}), 400

    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT money FROM User WHERE username = ?", (username,))
            user = cursor.fetchone()

            if user:
                return jsonify({'money': user[0]}), 200  # 金額保留字串
            else:
                return jsonify({'error': '用戶不存在'}), 404
    except sqlite3.Error as e:
        return jsonify({'error': f'資料庫錯誤: {str(e)}'}), 500
@app.route('/blackjackLobby',methods=['GET'])
def blackjackLobby():
    # 返回房間列表
    return jsonify({'blackJackRooms' : blackJackRoomList}), 200

# 動態生成房間頁面
@app.route('/blackjackRoom/<int:blackJackRoomID>', methods=['GET'])
def room_page(blackJackRoomID):
    blackJackRoom = next((r for r in blackJackRoomList if r['id'] == blackJackRoomID), None)
    
    if blackJackRoom is None:
        return jsonify({'error': '房間不存在'}), 404
    
    return jsonify({'blackJackRoom': blackJackRoom})

@app.route('/createBlackJackRoom', methods=['POST'])
def create_room():
    global blackJackRoomList
    data = request.json

    # 創建新的房間資料
    blackJackRoomID = len(blackJackRoomList) + 1
    blackJackRoom = {
        'id': blackJackRoomID,
        'name': data.get('name', f'房間 {blackJackRoomID}'),
        'description': data.get('description', '這是一個新的房間'),
        'capacity': data.get('max_players', 4),  # 預設最大人數為4
        'current_players': 0  # 新房間初始人數為0
    }
    # 將房間添加到列表
    blackJackRoomList.append(blackJackRoom)
    return jsonify({'message': '房間創建成功', 'blackJackRoom': blackJackRoom}), 201

@app.route('/blackjackRoom/<int:blackJackRoomID>/player/<int:seat>/action', methods=['POST'])
def blackjackRoom_player_action(blackJackRoomID, seat):
    """
    處理玩家對座位的操作，包括入座、離座和下注。
    """
    data = request.get_json()
    player_name = data.get('playerName')
    action = data.get('action')
    amount = data.get('amount', 0)  # 預設下注金額為 0

    # 找到房間
    blackJackRoom = next((room for room in blackJackRoomList if room['id'] == blackJackRoomID), None)
    if not blackJackRoom:
        return jsonify({'error': '房間不存在'}), 404

    # 處理不同操作
    if action == 'sit':
        # 確認座位是否被占用
        if any(player['seat'] == seat for player in blackJackRoom['players']):
            return jsonify({'error': '座位已被佔用'}), 400

        # 確認玩家是否已經選擇其他座位
        if any(player['username'] == player_name for player in blackJackRoom['players']):
            return jsonify({'error': '玩家已在其他座位上'}), 400

        # 記錄玩家座位
        blackJackRoom['players'].append({'username': player_name, 'seat': seat, 'bet': 0})
        blackJackRoom['current_players'] += 1

    elif action == 'leave':
        # 移除玩家的座位記錄
        blackJackRoom['players'] = [player for player in blackJackRoom['players'] if player['username'] != player_name]
        blackJackRoom['current_players'] -= 1

    elif action == 'bet':
        # 設定玩家的下注金額
        for player in blackJackRoom['players']:
            if player['username'] == player_name:
                player['bet'] = amount
                break
        else:
            return jsonify({'error': '玩家尚未入座'}), 400
    else:
        return jsonify({'error': '未知操作'}), 400

    # 返回當前房間的座位占用狀態
    occupied_buttons = {player['seat']: player['username'] for player in blackJackRoom['players']}
    return jsonify({'message': f'{action} 動作已完成', 'occupiedButtons': occupied_buttons}), 200


@app.route('/blackjackRoom/<int:blackJackRoomID>/get', methods=['GET'])
def get_blackjack_room_state(blackJackRoomID):
    """
    獲取房間狀態，包括座位占用資訊。
    """
    blackJackRoom = next((room for room in blackJackRoomList if room['id'] == blackJackRoomID), None)
    if not blackJackRoom:
        return jsonify({'error': '房間不存在'}), 404

    occupied_buttons = {player['seat']: player['username'] for player in blackJackRoom['players']}
    return jsonify({'blackJackRoom': blackJackRoom, 'occupiedButtons': occupied_buttons})




if __name__ == "__main__":
    init_db()  # 啟動應用時初始化資料庫
    app.run(debug=True, port=5001)  # 假設後端服務器運行在 5001 端口
