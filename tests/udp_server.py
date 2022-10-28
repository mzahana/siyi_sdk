"""
This server is just for testing
"""
import socket

UDP_IP = "127.0.0.1"
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_PORT))
sock.settimeout(5)

while True:
    try:
        data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
        print("Received some data")
        msg = data.hex()
        print("received message: %s" % msg)
        sock.sendto(data, addr)
    except Exception as e:
        print("Error: {}".format(e))
        break