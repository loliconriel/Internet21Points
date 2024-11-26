import socket
import threading
import random

# 每個房間最多 4 名玩家
MAX_PLAYERS = 4
ROOM_COUNT = 4
DECK_COUNT = 6

# 初始化房間狀態和事件同步機制
rooms = {f"room{i+1}": [] for i in range(ROOM_COUNT)}
room_events = {f"room{i+1}": threading.Event() for i in range(ROOM_COUNT)}
room_dealer_hands = {f"room{i+1}": [] for i in range(ROOM_COUNT)}  # 儲存莊家手牌

def shuffle_deck():
    """產生 6 副撲克牌並洗牌"""
    deck = [i for i in range(1, 14) for _ in range(4)] * DECK_COUNT
    random.shuffle(deck)
    return deck

def calculate_score(hand):
    """計算手牌分數"""
    score = 0
    ace_count = 0

    for card in hand:
        if card == 1:  
            ace_count += 1
            score += 11  
        elif card >= 10:  
            score += 10
        else:
            score += card

    while score > 21 and ace_count > 0:
        score -= 10
        ace_count -= 1

    return score

def dealer_play(deck, dealer_hand):
    """莊家進行操作"""
    while True:
        dealer_score = calculate_score(dealer_hand)
        if dealer_score < 17:
            dealer_hand.append(deck.pop())  
        else:
            break 
    return dealer_hand

def determine_results(hands, dealer_hand):
    """判斷結果"""
    dealer_score = calculate_score(dealer_hand)
    results = {}

    for client, hand in hands.items():
        player_score = calculate_score(hand)

        if player_score > 21:
            results[client] = "爆牌，輸了！"
        elif dealer_score > 21 or player_score > dealer_score:
            results[client] = "贏了！"
        elif player_score < dealer_score:
            results[client] = "輸了！"
        else:
            results[client] = "平手！"

    return results

def handle_client(client_socket, addr):
    """處理每個連線玩家"""
    client_socket.sendall("歡迎來到 21 點！\n".encode())
    
    while True:
        # 顯示 Lobby 狀態
        lobby_status = "\n".join([f"{room} ({len(rooms[room])}/{MAX_PLAYERS})" for room in rooms])
        client_socket.sendall((lobby_status + "\n加入房間：").encode())
        
        # 接收玩家選擇的房間
        room_choice = client_socket.recv(1024).decode().strip()
        if room_choice not in rooms:
            client_socket.sendall("無效的房間號，請重新選擇。\n".encode())
            continue
        
        # 確認房間人數
        if len(rooms[room_choice]) >= MAX_PLAYERS:
            client_socket.sendall("房間已滿，請選擇其他房間。\n".encode())
            continue

        # 加入房間
        rooms[room_choice].append(client_socket)
        client_socket.sendall(f"成功加入 {room_choice}！等待其他玩家...\n".encode())
    
        while True:
            # 如果房間人數滿了，觸發事件開始遊戲
            if len(rooms[room_choice]) == MAX_PLAYERS:
                room_events[room_choice].set()

            # 等待遊戲開始
            room_events[room_choice].wait()
            
            # 發牌邏輯
            if not room_dealer_hands[room_choice]:  # 確保每輪莊家手牌一致
                deck = shuffle_deck()  # Initialize the deck before dealing hands
                room_dealer_hands[room_choice] = [deck.pop(), deck.pop()]

            dealer_hand = room_dealer_hands[room_choice]
            hands = {client: [deck.pop(), deck.pop()] for client in rooms[room_choice]}

            # 廣播莊家第一張牌和每個玩家的手牌
            for client in rooms[room_choice]:
                client.sendall(f"莊家第一張牌：{dealer_hand[0]}\n".encode())
                client.sendall(f"你的牌：{hands[client]}\n".encode())

            # 玩家回合依序進行
            for client in rooms[room_choice]:
                    while True:
                        client.sendall("是否加牌？(y/n): ".encode())
                        choice = client.recv(1024).decode().strip()
                        if choice.lower() == 'y':
                            card = deck.pop()
                            hands[client].append(card)
                            client.sendall(f"你抽到的牌是 {card}\n".encode())
                            client.sendall(f"你的牌：{hands[client]}\n".encode())
                            if calculate_score(hands[client]) > 21:
                                client.sendall("你爆牌了！\n".encode())
                                break
                        elif choice.lower() == 'n':
                            break

            # 等待所有玩家完成回合
            if client_socket == rooms[room_choice][-1]:
                room_events[room_choice].clear()

            # 莊家操作
            if not room_events[room_choice].is_set():
                dealer_hand = dealer_play(deck, dealer_hand)

            # 比較結果並結算
            result = determine_results(hands, dealer_hand)
            for client in rooms[room_choice]:
                client.sendall(f"遊戲結束！莊家牌：{dealer_hand}\n".encode())
                client.sendall(f"你的結果：{result[client]}\n".encode())

            # 是否繼續遊戲
            i = 0
            while i < len(rooms[room_choice]):
                print(i)
                client = rooms[room_choice][i]
                client.sendall("是否重新開始？(y/n): ".encode())
                choice = client.recv(1024).decode().strip()
                if choice.lower() != 'y':
                    client.sendall("離開遊戲。\n".encode())
                    rooms[room_choice].remove(client)
                else:
                    i += 1 


            # 若人數不足，廣播等待訊息
            if len(rooms[room_choice]) < MAX_PLAYERS:
                for client in rooms[room_choice]:
                    client.sendall("人數未滿，請稍等。\n".encode())

            # 若所有人選擇繼續，重置狀態
            if len(rooms[room_choice]) == MAX_PLAYERS:
                room_events[room_choice].set()

        



def main():
    """主伺服器函數"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("", 8888))
    server.listen(ROOM_COUNT * MAX_PLAYERS)
    print("伺服器啟動中，等待玩家連線...")

    while True:
        client_socket, addr = server.accept()
        print(f"玩家 {addr} 已連線。")
        threading.Thread(target=handle_client, args=(client_socket, addr)).start()

if __name__ == "__main__":
    main()
