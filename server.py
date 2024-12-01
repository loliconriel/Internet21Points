import sqlite3
import time
import threading
from flask import Flask, request, jsonify,render_template
from flask_cors import CORS

app = Flask(__name__)
TIMER_SECONDS = 30
DATABASE = 'user_data.db'
CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:5000"}})
blackJackRoomList = [
    {
        'id': 1,
        'name': '房間 1',
        'capacity': 4,
        'current_players': 0,
        'description': '這是房間1的描述',
        'players': [],
        'dealer': {'hand': [], 'points': 0},
        'current_turn': None,
        'turn_start_time': None,
        'timer': None,  # 房間的倒數計時器
        'timer_remaining': TIMER_SECONDS,  # 倒數剩餘時間
        'game_running': False  # 遊戲狀態
    },
    # 可添加更多房間
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

    # 確保數據有效性
    room_name = data.get('name', f'房間 {len(blackJackRoomList) + 1}')
    description = data.get('description', '這是一個新的房間')
    max_players = int(data.get('capacity', 4))
    print(data)
    # 檢查最大玩家數是否合理
    if not isinstance(max_players, int) or max_players <= 0:
        return jsonify({'error': '最大玩家數必須為正整數'}), 400

    # 創建新的房間數據結構
    new_room = {
        'id': len(blackJackRoomList) + 1,  # 動態生成房間 ID
        'name': room_name,
        'capacity': max_players,
        'current_players': 0,
        'description': description,
        'players': [],  # 初始化玩家列表
        'dealer': {'hand': [], 'points': 0},  # 初始化莊家的數據
        'current_turn': None,
        'turn_start_time': None,
        'timer': None,  # 倒數計時器
        'timer_remaining': TIMER_SECONDS,  # 倒數時間
        'game_running': False  # 初始遊戲狀態
    }

    # 將房間添加到列表
    blackJackRoomList.append(new_room)
    return jsonify({'message': '房間創建成功', 'blackJackRoom': new_room}), 201

# 開始遊戲
def start_game(room):
    """開始房間遊戲"""
    room['game_running'] = True
    print(f"房間 {room['name']} 開始遊戲！")

def reset_game(room):
    room['timer_remaining'] = TIMER_SECONDS

# 倒數計時邏輯
def countdown_timer(room):
    """倒數計時器"""
    while room['timer_remaining'] > 0:
        time.sleep(1)
        room['timer_remaining'] -= 1
        print(f"房間 {room['name']} 倒數中：{room['timer_remaining']} 秒")
        
        # 如果房間沒人則停止計時
        if room['current_players'] == 0:
            room['timer_remaining'] = TIMER_SECONDS  # 重置倒數時間
            print(f"房間 {room['name']} 無玩家，重置計時器")
            return

    # 倒數結束，開始遊戲
    if room['current_players'] > 0:
        start_game(room)

@app.route('/blackjackRoom/<int:blackJackRoomID>/player/<int:seat>/action', methods=['POST'])
def blackjackRoom_player_action(blackJackRoomID, seat):
    """處理玩家的座位操作，包括入座與離座"""
    data = request.get_json()
    player_name = data.get('playerName')
    action = data.get('action')

    # 找到對應的房間
    room = next((r for r in blackJackRoomList if r['id'] == blackJackRoomID), None)
    if not room:
        return jsonify({'error': '房間不存在'}), 404

    if action == 'sit':
        # 確認座位是否被佔用
        if any(player['seat'] == seat for player in room['players']):
            return jsonify({'error': '座位已被佔用'}), 400

        # 確認玩家是否已經在其他座位
        if any(player['username'] == player_name for player in room['players']):
            return jsonify({'error': '玩家已經入座'}), 400

        # 添加玩家
        room['players'].append({'username': player_name, 'seat': seat, 'bet': 0})
        room['current_players'] += 1

        # 如果這是第一位玩家，啟動倒數計時
        if room['current_players'] == 1 and not room['game_running']:
            room['timer_start_time'] = time.time()  # 記錄倒數開始的時間戳

    elif action == 'leave':
        # 移除玩家
        room['players'] = [player for player in room['players'] if player['username'] != player_name]
        room['current_players'] -= 1

        # 如果所有玩家都離開，重置計時器和遊戲狀態
        if room['current_players'] == 0:
            room['timer_start_time'] = None  # 清除計時器
            room['game_running'] = False

    else:
        return jsonify({'error': '未知操作'}), 400

    # 返回房間狀態
    occupied_buttons = {player['seat']: player['username'] for player in room['players']}
    return jsonify({'message': f'{action} 動作已完成', 'occupiedButtons': occupied_buttons}), 200



def calculate_timer_remaining(room):
    """計算房間的倒數剩餘時間"""
    if not room.get('timer_start_time'):  # 無倒數計時
        return TIMER_SECONDS
    elapsed_time = time.time() - room['timer_start_time']
    remaining_time = max(0, TIMER_SECONDS - int(elapsed_time))  # 確保不為負數
    return remaining_time


@app.route('/blackjackRoom/<int:blackJackRoomID>/get', methods=['GET'])
def get_blackjack_room_state(blackJackRoomID):
    """獲取房間狀態，包括動態計算倒數剩餘時間"""
    room = next((r for r in blackJackRoomList if r['id'] == blackJackRoomID), None)
    if not room:
        return jsonify({'error': '房間不存在'}), 404
    print(room)
    # 計算剩餘時間
    timer_remaining = calculate_timer_remaining(room)

    occupied_buttons = {player['seat']: player['username'] for player in room['players']}
    return jsonify({
        'blackJackRoom': {
            key: value for key, value in room.items() if key != 'timer_start_time'  # 過濾不必要的屬性
        },
        'occupiedButtons': occupied_buttons,
        'timer_remaining': timer_remaining,
        'game_running': room['game_running']
    }), 200




if __name__ == "__main__":
    init_db()  # 啟動應用時初始化資料庫
    app.run(debug=True, port=5001)  # 假設後端服務器運行在 5001 端口
