import socket


TCP_IP = '192.168.1.200'

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, 80))
s.sendall("GET /cgi-bin/param.cgi?post_image_value&flip&1 HTTP/1.1\nHost: 192.168.1.200\n\n")#flip
s.close

