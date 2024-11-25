import socket
import threading
import random

# 每個房間最多 4 名玩家
MAX_PLAYERS = 4
ROOM_COUNT = 4
DECK_COUNT = 6

# 初始化房間狀態
rooms = {f"room{i+1}": [] for i in range(ROOM_COUNT)}
room_locks = {f"room{i+1}": threading.Lock() for i in range(ROOM_COUNT)}
room_conditions = {f"room{i+1}": threading.Condition(room_locks[f"room{i+1}"]) for i in range(ROOM_COUNT)}

def shuffle_deck():
    """產生 6 副撲克牌並洗牌"""
    deck = [i for i in range(1, 14) for _ in range(4)] * DECK_COUNT
    random.shuffle(deck)
    return deck

def calculate_score(hand):
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
    while True:
        dealer_score = calculate_score(dealer_hand)
        if dealer_score < 17:
            dealer_hand.append(deck.pop())  
        else:
            break 
    return dealer_hand

def broadcast(room, message):
    """向房間內的所有玩家廣播訊息"""
    with room_locks[room]:
        for client in rooms[room]:
            try:
                client.sendall(message.encode())
            except:
                rooms[room].remove(client)

def handle_client(client_socket, addr):
    client_socket.sendall("Welcome to blackjack！\n".encode())
    while True:
        # 顯示 Lobby 狀態
        lobby_status = "\n".join([f"{room} ({len(rooms[room])}/{MAX_PLAYERS})" for room in rooms])
        client_socket.sendall((lobby_status + "\n加入房間：").encode())
        
        # 接收玩家選擇的房間
        room_choice = client_socket.recv(1024).decode().strip()
        if room_choice not in rooms:
            client_socket.sendall("無效的房間號，請重新選擇。\n".encode())
            continue

        # 加入房間時加鎖
        with room_locks[room_choice]:
            if len(rooms[room_choice]) >= MAX_PLAYERS:
                client_socket.sendall("房間已滿，請選擇其他房間。\n".encode())
                continue
            rooms[room_choice].append(client_socket)
            client_socket.sendall(f"成功加入 {room_choice}！等待其他玩家...\n".encode())

            # 如果房間人數滿，啟動遊戲
            if len(rooms[room_choice]) == MAX_PLAYERS:
                with room_conditions[room_choice]:
                    room_conditions[room_choice].notify_all()

        # 等待遊戲開始
        with room_conditions[room_choice]:
            while len(rooms[room_choice]) < MAX_PLAYERS:
                room_conditions[room_choice].wait()

        # 發牌流程
        deck = shuffle_deck()
        dealer_hand = [deck.pop(), deck.pop()]
        hands = {client: [deck.pop(), deck.pop()] for client in rooms[room_choice]}

        # 廣播莊家的第一張牌給所有玩家
        broadcast(room_choice, f"莊家第一張牌：{dealer_hand[0]}\n")
        for client in rooms[room_choice]:
            client.sendall(f"你的牌：{hands[client]}\n".encode())

        # 玩家輪流加牌
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

        # 莊家動作
        dealer_hand = dealer_play(deck, dealer_hand)

        # 廣播莊家結果及結算
        broadcast(room_choice, f"莊家最終牌：{dealer_hand}\n")
        for client in rooms[room_choice]:
            player_score = calculate_score(hands[client])
            dealer_score = calculate_score(dealer_hand)
            if player_score > 21:
                result = "爆牌，輸了！"
            elif dealer_score > 21 or player_score > dealer_score:
                result = "贏了！"
            elif player_score < dealer_score:
                result = "輸了！"
            else:
                result = "平手！"
            client.sendall(f"你的最終結果：{result}\n".encode())
        break

    client_socket.close()

def main():
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
