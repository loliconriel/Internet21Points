import socket

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("127.0.0.1", 8888))

    while True:
        data = client.recv(1024).decode()
        print(data)

        if "加入房間" in data:
            room = input("請輸入房間號碼: ")
            client.sendall(room.encode())

        elif "是否加牌" in data:
            choice = input(data)
            client.sendall(choice.encode())

        elif "是否重新開始" in data:
            choice = input(data)
            client.sendall(choice.encode())

if __name__ == "__main__":
    main()
