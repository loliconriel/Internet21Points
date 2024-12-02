import sqlite3
import time
import threading
import requests
import random
from flask import Flask, request, jsonify,render_template
from flask_cors import CORS

app = Flask(__name__)
TIMER_SECONDS = 10
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
        'game_running': False,  # 遊戲狀態
        'bet_timing' : True
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
def filter_room_data(room):
    """過濾掉不必要的屬性，包括 deck"""
    return {key: value for key, value in room.items() if key not in ['deck', 'timer']}
def reset_game(room):
    """重置遊戲狀態"""
    room['timer_start_time'] = time.time()
    room['timer_remaining'] = TIMER_SECONDS
    room['timer_running'] = True
    room['game_running'] = False
    room['current_turn'] = None
    room['turn_start_time'] = None
    room['deck'] = None

    # 重置莊家數據
    room['dealer'] = {'hand': [], 'points': 0}

    # 重置玩家數據，但保留座位和賭注
    for player in room['players']:
        player['hand'] = []  # 清空手牌
        player['points'] = 0  # 重置點數
        player['stand'] = False  # 重置為未停牌
        player['timeout'] = False  # 重置超時狀態
        player['bet'] = 0

def get_user_money(username):
    """根據使用者名稱取得該使用者的金額"""
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            # 查詢該使用者的金額
            cursor.execute('SELECT money FROM User WHERE username = ?', (username,))
            result = cursor.fetchone()

            if result:
                # 返回金額（這裡是文字型別的數據）
                return result[0]
            else:
                return None  # 用戶不存在
    except sqlite3.Error as e:
        # 發生資料庫錯誤時返回 None
        print(f"Database error: {e}")
        return None
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

@app.route('/balance', methods=['GET'])
def get_balance(username = None):
    """獲取使用者的當前金額"""
    if(username==None):username = request.args.get('username')
    
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
def update_player_balances(results, players):
    """根據遊戲結果更新玩家的金額"""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        for player in players:
            result = results[player['username']]
            money = get_user_money(player['username'])
            bet = player['bet']
            if result == "贏了！":
                new_balance = int(money) + bet
            elif result == "平手！":
                new_balance = int(money)
            else:
                new_balance = int(money) - bet
            print(new_balance)
            cursor.execute("UPDATE User SET money = ? WHERE username = ?", (str(new_balance), player['username']))
        conn.commit()

@app.route('/blackjackLobby', methods=['GET'])
def blackjackLobby():
    """返回房間列表，過濾 timer"""
    filtered_rooms = [filter_room_data(room) for room in blackJackRoomList]
    return jsonify({'blackJackRooms': filtered_rooms}), 200

# 動態生成房間頁面
@app.route('/blackjackRoom/<int:blackJackRoomID>', methods=['GET'])
def room_page(blackJackRoomID):
    """返回單個房間，過濾 timer"""
    room = next((r for r in blackJackRoomList if r['id'] == blackJackRoomID), None)
    if not room:
        return jsonify({'error': '房間不存在'}), 404
    return jsonify({'blackJackRoom': filter_room_data(room)}), 200

@app.route('/createBlackJackRoom', methods=['POST'])
def create_room():
    global blackJackRoomList
    data = request.json

    # 確保數據有效性
    room_name = data.get('name', f'房間 {len(blackJackRoomList) + 1}')
    description = data.get('description', '這是一個新的房間')
    max_players = int(data.get('capacity', 4))
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

def shuffle_deck():
    """產生一副撲克牌並洗牌"""
    suits = 'CDHS'  # 黑桃、紅心、梅花、方塊
    ranks = [str(i) for i in range(1, 14)]  # A ~ K
    deck = [rank + suit for rank in ranks for suit in suits] * 6  # 6 副牌
    random.shuffle(deck)
    return deck
def calculate_score(cards):
    """計算 21 點手牌分數"""
    score = 0
    aces = 0
    for card in cards:
        rank = card[:-1]  # 排除花色，僅取數值部分
        if rank in ['11', '12', '13']:  # J, Q, K
            score += 10
        elif rank == '1':  # Ace
            score += 1
            aces += 1
        else:
            score += int(rank)

    # 考慮 Ace 作為 11 的情況
    while aces > 0 and score + 10 <= 21:
        score += 10
        aces -= 1
    return score
def determine_results(players, dealer_hand):
    """判斷玩家與莊家的遊戲結果"""
    dealer_score = calculate_score(dealer_hand)
    results = {}
    for player in players:
        player_score = player['points']
        if player_score > 21:
            results[player['username']] = "爆牌，輸了！"
        elif dealer_score > 21 or player_score > dealer_score:
            results[player['username']] = "贏了！"
        elif player_score < dealer_score:
            results[player['username']] = "輸了！"
        else:
            results[player['username']] = "平手！"
    return results


def start_game(room):
    """開始 21 點遊戲並按座位順序處理決策"""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()

        # 初始化牌堆
        room['deck'] = shuffle_deck()

        # 清空莊家手牌
        room['dealer']['hand'] = []
        room['dealer']['points'] = 0

        # 清空玩家初始狀態
        for player in room['players']:
            player['hand'] = [room['deck'].pop(), room['deck'].pop()]  # 發兩張牌
            player['points'] = calculate_score(player['hand'])
            player['stand'] = False  # 初始化未停牌狀態
            player['timeout'] = False  # 是否超時自動停牌

        # 給莊家發牌
        room['dealer']['hand'] = [room['deck'].pop(), room['deck'].pop()]
        room['dealer']['points'] = calculate_score(room['dealer']['hand'])

        # 遊戲決策邏輯
        room['game_running'] = True
        while any(not player['stand'] and player['points'] <= 21 for player in room['players']):
            for player in room['players']:
                # 跳過已經停牌或爆牌的玩家
                if player['stand'] or player['points'] > 21:
                    continue

                # 設置當前回合的玩家
                room['current_turn'] = player['username']
                room['turn_start_time'] = time.time()

                # 等待玩家行動
                action_done = False
                while time.time() - room['turn_start_time'] < 10:  # 等待 10 秒
                    if player['stand'] or player['points'] > 21:
                        action_done = True
                        break
                    time.sleep(1)  # 每秒檢查一次

                # 超時自動停牌
                if not action_done:
                    print(f"玩家 {player['username']} 超時，執行自動停牌")
                    player['stand'] = True
                    player['timeout'] = True

        # 莊家邏輯
        while room['dealer']['points'] < 17:
            card = room['deck'].pop()
            room['dealer']['hand'].append(card)
            room['dealer']['points'] = calculate_score(room['dealer']['hand'])

        # 結算
        results = determine_results(room['players'], room['dealer']['hand'])
        update_player_balances(results, room['players'])
        time.sleep(10)
        # 重置遊戲狀態
        room['game_running'] = False
        print("遊戲結束，結果已結算。")
        reset_game(room)


def countdown_timer(room):
    """倒數計時"""
    while True:
        room['timer_running'] = True
        while room['timer_remaining'] > 0:
            time.sleep(1)
            room['timer_remaining'] -= 1
            if room['current_players'] == 0:
                reset_game(room)
                return
        if room['current_players'] > 0:
            start_game(room)
        room['timer_running'] = False
    
@app.route('/blackjackRoom/<int:blackJackRoomID>/player/<int:seat>/action', methods=['POST'])
def blackjackRoom_player_action(blackJackRoomID, seat):
    """處理玩家的座位操作，包括入座與離座"""
    data = request.get_json()
    player_name = data.get('playerName')
    action = data.get('action')
    bet = data.get('amount', 0)

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
            room['timer'] = threading.Thread(target=countdown_timer, args=(room,))
            room['timer'].start()
        
    elif action == 'leave':
        # 移除玩家
        room['players'] = [player for player in room['players'] if player['username'] != player_name]
        room['current_players'] -= 1

        # 如果所有玩家都離開，重置計時器和遊戲狀態
        if room['current_players'] == 0:
            reset_game(room)
    elif action == 'bet':
        timer_remaining = calculate_timer_remaining(room)
        if timer_remaining <= 0:
            return jsonify({'error': '下注已截止'}), 400
        # 查找玩家是否在房間中
        player = next((player for player in room['players'] if player['username'] == player_name), None)
        if not player:
            return jsonify({'error': '玩家未入座'}), 400
        
        # 更新玩家投注金額
        if isinstance(bet, int) and bet > 0:
            player['bet'] = bet
        else:
            return jsonify({'error': '投注金額必須為正整數'}), 400
    elif action == 'hit':
        # 找到玩家並處理加牌
        player = next((player for player in room['players'] if player['username'] == player_name), None)
        if not player:
            return jsonify({'error': '玩家未入座'}), 400
        
        # 發一張牌
        if 'deck' not in room:
            room['deck'] = shuffle_deck()
        card = room['deck'].pop()
        player['hand'].append(card)
        player['points'] = calculate_score(player['hand'])

        # 檢查爆牌
        if player['points'] > 21:
            room['turn_start_time'] = 0
            return jsonify({'message': '爆牌，回合結束', 'player': player}), 200
            
        else:
            room['turn_start_time'] = time.time()
        return jsonify({'message': '加牌成功', 'player': player}), 200

    elif action == 'stand':
        
        # 停牌邏輯，設定玩家完成本回合
        player = next((player for player in room['players'] if player['username'] == player_name), None)
        if not player:
            return jsonify({'error': '玩家未入座'}), 400
        
        player['stand'] = True
        room['turn_start_time'] = 0
        return jsonify({'message': '停牌成功', 'player': player}), 200
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
    """獲取房間狀態"""
    room = next((r for r in blackJackRoomList if r['id'] == blackJackRoomID), None)
    username = request.args.get('username')  # 從查詢參數獲取 username
    if not room:
        return jsonify({'error': '房間不存在'}), 404

    filtered_room = filter_room_data(room)
    occupied_buttons = {player['seat']: player['username'] for player in room['players']}
    players_bet = {player['seat']: player['bet'] for player in room['players']}  # 玩家賭注
    user_balance = 0

    # 計算當前決策玩家的剩餘時間
    decision_time_remaining = None
    if room['current_turn'] and room['turn_start_time']:
        elapsed_time = time.time() - room['turn_start_time']
        decision_time_remaining = max(0, TIMER_SECONDS - int(elapsed_time))

    if username:
        user_balance = get_user_money(username)
    return jsonify({
        'blackJackRoom': filtered_room,
        'occupiedButtons': occupied_buttons,
        'playersBet': players_bet,  # 返回賭注資訊
        'timer_remaining': calculate_timer_remaining(room),
        'game_running': room['game_running'],
        'user_balance': user_balance,
        'dealer': room['dealer'],  # 返回莊家的手牌與點數
        'current_turn': room['current_turn'],  # 當前決策玩家
        'decision_time_remaining': decision_time_remaining,  # 剩餘時間
    }), 200





if __name__ == "__main__":
    init_db()  # 啟動應用時初始化資料庫
    app.run(debug=True, port=5001)  # 假設後端服務器運行在 5001 端口
