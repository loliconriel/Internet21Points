import socket
import threading
import random

MAX_PLAYERS = 4
ROOM_COUNT = 4
DECK_COUNT = 6

rooms = {f"room{i+1}": [] for i in range(ROOM_COUNT)}
room_locks = {f"room{i+1}": threading.Lock() for i in range(ROOM_COUNT)}

def shuffle_deck():
    deck = [i for i in range(1, 14) for _ in range(4)] * DECK_COUNT
    random.shuffle(deck)
    return deck

def broadcast(room, message):
    with room_locks[room]:
        for client in rooms[room]:
            try:
                client.sendall(message.encode())
            except Exception as e:
                print(f"廣播失敗: {e}")
                rooms[room].remove(client)

def handle_client(client_socket, addr):
    client_socket.sendall("Welcome to blackjack！\n".encode())
    room_choice = None

    try:
        # 選擇房間並加入
        while True:
            lobby_status = "\n".join([f"{room} ({len(rooms[room])}/{MAX_PLAYERS})" for room in rooms])
            client_socket.sendall((lobby_status + "\n加入房間：").encode())

            room_choice = client_socket.recv(1024).decode().strip()

            if room_choice not in rooms:
                client_socket.sendall("無效的房間號，請重新選擇。\n".encode())
                continue

            with room_locks[room_choice]:
                if len(rooms[room_choice]) >= MAX_PLAYERS:
                    client_socket.sendall("房間已滿，請選擇其他房間。\n".encode())
                    continue
                rooms[room_choice].append(client_socket)
                client_socket.sendall(f"成功加入 {room_choice}！等待其他玩家...\n".encode())

                # 當房間滿員後，廣播通知並開始遊戲
                if len(rooms[room_choice]) == MAX_PLAYERS:
                    print(f"房間 {room_choice} 已滿，遊戲即將開始！")
                    broadcast(room_choice, "房間已滿，遊戲即將開始！")
                    break

            # 等待其他玩家加入
            while len(rooms[room_choice]) < MAX_PLAYERS:
                pass  # 等待滿員

            # 發牌階段，準備洗牌
            deck = shuffle_deck()
            dealer_hand = [deck.pop(), deck.pop()]
            hands = {client: [deck.pop(), deck.pop()] for client in rooms[room_choice]}

            broadcast(room_choice, f"莊家第一張牌：{dealer_hand[0]}\n")
            for client in rooms[room_choice]:
                client.sendall(f"你的牌：{hands[client]}\n".encode())

            # 玩家操作：詢問是否加牌
            for client in rooms[room_choice]:
                while True:
                    client.sendall("是否加牌？(y/n): ".encode())
                    choice = client.recv(1024).decode().strip()
                    if choice.lower() == 'y':
                        card = deck.pop()
                        hands[client].append(card)
                        client.sendall(f"你抽到的牌是 {card}\n".encode())
                        if sum(hands[client]) > 21:
                            client.sendall("你爆牌了！\n".encode())
                            break
                    elif choice.lower() == 'n':
                        break

            # 向所有玩家顯示莊家牌
            broadcast(room_choice, f"莊家最終牌：{dealer_hand}\n")
            break

    finally:
        if room_choice and client_socket in rooms[room_choice]:
            with room_locks[room_choice]:
                rooms[room_choice].remove(client_socket)
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
