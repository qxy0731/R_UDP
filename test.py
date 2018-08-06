#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket,pickle,threading,time
import copy,random
random.seed(50)


print(time.time())
time.sleep(1)
print(time.time())
# def PLD():
#     pdrop = 0.4
#     x = random.random()
#     return x <= pdrop
# win_cap = 6
# MSS = 30
# with open('text2.txt', 'r') as f:
#     a = f.read()
# payload_pool = list()
# for i in range(0,len(a),MSS):
#     if i+30 < len(a):
#         payload_pool.append(a[i:i+MSS])
#     else:
#         payload_pool.append(a[i:])
# print(payload_pool)
    # def receiving():
#     pass
#
#
# start = time.time()
# init_header = {'SYN': False, 'ACK': False, 'FIN': False, 'DATA': False, 'seq': 0, 'ack': 0}
# init_payload = ''
# init_segment = [init_header, init_payload]
# client_isn = 121
#
# s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# print(init_segment)
# reply_header, reply_payload = copy.deepcopy(init_segment)
# reply_header['SYN'] = True
# reply_header['seq'] = client_isn
# print(init_segment)