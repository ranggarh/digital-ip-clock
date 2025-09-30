import socket
import datetime

IP = "192.168.2.246"
PORT = 1001

# Format jam dengan colon, misal 14:20
now = datetime.datetime.now().strftime("%H:%M") + "\r"
print("Sending:", repr(now))

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.settimeout(5)
    s.connect((IP, PORT))
    s.send(now.encode("latin1"))
    print("Data sent!")
