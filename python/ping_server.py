#!/usr/bin/python

import socket

HOST = ''
PORT = 11288

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((HOST, PORT))

while 1:
    data, addr = server.recvfrom(1024)
    print 'Connection:', addr
    print 'Data:', data
    server.sendto(data, addr)

conn.close()
