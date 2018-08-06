#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# written in python3

import pickle
import socket,time
import copy
import sys

def SYN_state():
    global server_isn
    global start
    while True:
        data, addr = s.recvfrom(1024)
        if not data:
            break
        received_header, received_payload = pickle.loads(data)
        if received_header['SYN']:
            start = time.time()
            with open('Receiver_log.txt', 'a') as f:
                f.write('rcv    {:<9.3f} S   {:<5d}  {:<5d}  {:<5d}\n'.format((time.time() - start)*1000, received_header['seq'], 0,received_header['ack']))
            reply_header, reply_payload = copy.deepcopy(init_segment)
            reply_header['SYN'] = reply_header['ACK'] = True
            reply_header['seq'] = server_isn
            reply_header['ack'] = received_header['seq'] + 1
            s.sendto(pickle.dumps([reply_header,reply_payload]),addr)
            with open('Receiver_log.txt', 'a') as f:
                f.write('snd    {:<9.3f} AS  {:<5d}  {:<5d}  {:<5d}\n'.format((time.time() - start)*1000, reply_header['seq'], 0,reply_header['ack']))
            continue
        if received_header['ACK']:
            with open('Receiver_log.txt', 'a') as f:
                f.write('rcv    {:<9.3f} A   {:<5d}  {:<5d}  {:<5d}\n'.format((time.time() - start)*1000, received_header['seq'],0, received_header['ack']))
            server_isn += 1
            return received_header['seq']

def find_wanted_seq(buffer):
    sorted_key = sorted(buffer)
    if sorted(buffer)[0] != first_ack:
        return first_ack
    for i in range(1,len(buffer)):
        if sorted_key[i]-sorted_key[i-1] != len(buffer[sorted_key[i-1]]):
            return sorted_key[i-1] + len(buffer[sorted_key[i-1]])
    return sorted_key[-1] + len(buffer[sorted_key[-1]])


def TRANS_FIN_state():
    global server_isn
    buffer = dict()
    data_amount = 0
    count_duplicate = seg_number = 0
    while True:
        data, addr = s.recvfrom(1024)
        if not data:
            break
        received_header, received_payload = pickle.loads(data)
        if received_header['DATA']:

            with open('Receiver_log.txt', 'a') as f:
                f.write('rcv    {:<9.3f} D   {:<5d}  {:<5d}  {:<5d}\n'.format((time.time() - start)*1000, received_header['seq'],\
                                                                len(received_payload), received_header['ack']))
            if received_header['seq'] not in buffer:
                seg_number += 1
                buffer[received_header['seq']] = received_payload
                data_amount += len(received_payload)

                ack = find_wanted_seq(buffer)
                reply_header, reply_payload = copy.deepcopy(init_segment)
                reply_header['ACK'] = True
                reply_header['seq'] = server_isn
                if received_payload:
                    reply_header['ack'] = ack
                else:
                    reply_header['ack'] = ack+1
                s.sendto(pickle.dumps([reply_header, reply_payload]), addr)
                with open('Receiver_log.txt', 'a') as f:
                    f.write('snd    {:<9.3f} A   {:<5d}  {:<5d}  {:<5d}\n'.format((time.time() - start) * 1000, reply_header['seq']\
                                                                   ,0,reply_header['ack']))
            else:
                count_duplicate += 1
            # print(sorted(buffer))
            # print(len(buffer))
            continue
        if received_header['FIN']:
            with open('Receiver_log.txt', 'a') as f:
                f.write('rcv    {:<9.3f} F   {:<5d}  {:<5d}  {:<5d}\n'.format((time.time() - start) * 1000,
                                                                              received_header['seq'], 0,
                                                                              received_header['ack']))
            reply_header, reply_payload = copy.deepcopy(init_segment)
            reply_header['FIN'] = reply_header['ACK'] = True
            reply_header['seq'] = server_isn
            reply_header['ack'] = received_header['seq'] + 1
            s.sendto(pickle.dumps([reply_header, reply_payload]), addr)
            with open('Receiver_log.txt', 'a') as f:
                f.write('snd    {:<9.3f} FA  {:<5d}  {:<5d}  {:<5d}\n'.format((time.time() - start) * 1000,
                                                                              reply_header['seq'], 0,
                                                                              reply_header['ack']))
            while True:
                data, addr = s.recvfrom(1024)
                if not data:
                    break
                received_header, received_payload = pickle.loads(data)
                with open('Receiver_log.txt', 'a') as f:
                    f.write('rcv    {:<9.3f} A   {:<5d}  {:<5d}  {:<5d}\n'.format((time.time() - start) * 1000,
                                                                                  received_header['seq'], 0,
                                                                                  received_header['ack']))
                if received_header['ACK'] and received_header['ack'] == server_isn +1:
                    break
            with open(output_file, 'w') as fff:
                fff.write('')

            with open(output_file,'ab') as ff:
                for key in sorted(buffer):
                    ff.write(buffer[key])

            with open('Receiver_log.txt', 'a') as f:
                f.write('Amount of (original) Data Received (in bytes): {}\n'.format(data_amount))
                f.write('Number of (original) Data Segments Received): {}\n'.format(seg_number))
                f.write('Number of duplicate segments received (if any): {}\n'.format(count_duplicate))
            break








output_file = sys.argv[2]
port = int(sys.argv[1])
init_header = {'SP': -1 ,'DP': port,'SYN': False, 'ACK': False, 'FIN': False, 'DATA': False, 'seq': 0, 'ack': 0}
init_payload = ''
init_segment = [init_header, init_payload]
server_isn = 154
with open('Receiver_log.txt', 'w') as f:
    f.write('')
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(('127.0.0.1', port))
print('Bind UDP on {}...'.format(port))
start = time.time()
first_ack = SYN_state()
TRANS_FIN_state()

s.close()
