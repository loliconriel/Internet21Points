import socket

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("127.0.0.1", 8888))
    game_started = False

    while True:
        data = client.recv(1024).decode()
        print(data)

        if "加入房間" in data and not game_started:
            room = input()
            client.sendall(room.encode())

        elif "是否加牌" in data:
            game_started = True
            choice = input()
            client.sendall(choice.encode())

        elif "是否重新開始" in data:
            choice = input()
            client.sendall(choice.encode())
            if choice.lower() == 'n':
                game_started = False

if __name__ == "__main__":
    main()
