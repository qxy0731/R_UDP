#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# written in python3

import socket,pickle,threading,time
import copy
import sys
import random
import math


def PLD(reply_header, reply_payload, host, port):
    global drop_count
    x = random.random()
    if x <= pdrop:
        drop_count += 1
        # print('drop   {:<9.3f} D   {:<5d}  {:<5d}  {:<5d}'.format((time.time() - start) * 1000, reply_header['seq'], \
        #                                                     len(reply_payload), reply_header['ack']))
        # print('my_seq = {},sendbase = {}'.format(my_seq,send_base))
        f.write('drop   {:<9.3f} D   {:<5d}  {:<5d}  {:<5d}\n'.format((time.time() - start) * 1000, reply_header['seq'], \
                                                            len(reply_payload), reply_header['ack']))
    else:
        # print('snd    {:<9.3f} D   {:<5d}  {:<5d}  {:<5d}'.format((time.time() - start) * 1000, reply_header['seq'], \
        #                                                     len(reply_payload), reply_header['ack']))
        # print('my_seq = {},sendbase = {}'.format(my_seq, send_base))
        s.sendto(pickle.dumps([reply_header, reply_payload]), (host, port))
        f.write('snd    {:<9.3f} D   {:<5d}  {:<5d}  {:<5d}\n'.format((time.time() - start) * 1000, reply_header['seq'], \
                                                            len(reply_payload), reply_header['ack']))

def SYN_state():
    global client_isn
    global start
    reply_header, reply_payload = copy.deepcopy(init_segment)
    reply_header['SYN'] = True
    reply_header['seq'] = client_isn
    start = time.time()
    s.sendto(pickle.dumps([reply_header, reply_payload]), (host, port))
    f.write('snd    {:<9.3f} S   {:<5d}  {:<5d}  {:<5d}\n'.format((time.time()-start)*1000, client_isn,0,0))
    while True:
        data, addr = s.recvfrom(1024)
        received_header, received_payload = pickle.loads(data)
        if received_header['SYN'] and received_header['ACK'] and received_header['ack'] == (client_isn+1):
            client_isn += 1
            f.write('rcv    {:<9.3f} SA  {:<5d}  {:<5d}  {:<5d}\n'.format((time.time() - start) * 1000, received_header['seq'],0, received_header['ack']))
            reply_header, reply_payload = copy.deepcopy(init_segment)
            reply_header['ACK'] = True
            reply_header['ack'] = received_header['seq'] + 1
            reply_header['seq'] = client_isn
            s.sendto(pickle.dumps([reply_header, reply_payload]), addr)
            f.write('snd    {:<9.3f} A   {:<5d}  {:<5d}  {:<5d}\n'.format((time.time() - start) * 1000, reply_header['seq'],0,reply_header['ack']))
            return received_header['seq'] + 1

def receive_thread():
    global send_base
    global retransmit_count
    global last_ack
    global duplicate_count
    while True:
        # lock.acquire()
        # print('try to receive....')
        data, addr = s.recvfrom(1024)
        received_header, received_payload = pickle.loads(data)
        if received_header['ACK']:
            # print('rcv    {:<9.3f} A   {:<5d}  {:<5d}  {:<5d}'.format((time.time() - start) * 1000, received_header['seq'], 0,received_header['ack']))
            # print('my_seq = {},sendbase = {}'.format(my_seq, send_base))
            f.write('rcv    {:<9.3f} A   {:<5d}  {:<5d}  {:<5d}\n'.format((time.time() - start) * 1000, received_header['seq'], 0,received_header['ack']))
            if received_header['ack'] > client_isn + MSS * send_base:
                send_base = math.ceil((received_header['ack'] - client_isn)/MSS)
                # print('sendbase = {} '.format(send_base))
                retransmit_count = 0
            elif received_header['ack'] <= client_isn + MSS * send_base:
                duplicate_count += 1
                # f.write('-----duplicate\n')
                retransmit_count += 1
        if send_base >= len(payload_pool):
            # print('my_seq = {},sendbase = {}'.format(my_seq, send_base))
            last_ack = received_header['ack']
            # print('receive done')
            break
        # finally:
        # print('unlock')
        # lock.release()

def trans_first_window():
    global payload_pool
    global send_base
    global retransmit_count
    global my_seq
    global timer
    global data_amount, seg_number
    with open(file_name, 'rb') as f2:
        a = f2.read()
    data_amount = len(a)
    seg_number = math.ceil(data_amount/MSS)
    if a:      
        for i in range(0, len(a), MSS):
            if i + MSS < len(a):
                payload_pool.append(a[i:i + MSS])
            else:
                payload_pool.append(a[i:])
    else:
        seg_number =1
        payload_pool = [b'']
    my_seq = 0
    reply_header, reply_payload = copy.deepcopy(init_segment)
    reply_header['DATA'] = True
    reply_header['ack'] = ack
    timer = time.time()
    # print(len(payload_pool))
    for i in range(win_cap):
        if my_seq >= len(payload_pool):
            my_seq += 1
            break
        reply_header['seq'] = client_isn + MSS * my_seq
        reply_payload = payload_pool[my_seq]
        my_seq += 1
        PLD(reply_header,reply_payload,host,port)


def send_thread():
    global send_base
    global retransmit_count
    global my_seq
    global timer
    global retran_count
    while True:
        # lock.acquire()
        # print('checking send.....')
        # print(my_seq - send_base- win_cap)
        if my_seq - send_base < win_cap:
            timer = time.time()
            # print('fine')
            reply_header, reply_payload = copy.deepcopy(init_segment)
            reply_header['DATA'] = True
            reply_header['ack'] = ack
            # print(send_base + win_cap - my_seq)
            for i in range(send_base + win_cap - my_seq):
                if my_seq >= len(payload_pool):
                    my_seq = send_base + win_cap
                    break
                reply_header['seq'] = client_isn + MSS * my_seq
                reply_payload = payload_pool[my_seq]
                my_seq += 1
                PLD(reply_header, reply_payload, host, port)
            # if my_seq >= len(payload_pool):
            #     my_seq = send_base + win_cap
        if retransmit_count >= 3:
            # print('fast retransmit')
            reply_header, reply_payload = copy.deepcopy(init_segment)
            reply_header['DATA'] = True
            reply_header['ack'] = ack
            reply_header['seq'] = client_isn + MSS * send_base
            reply_payload = payload_pool[send_base]
            retran_count += 1
            PLD(reply_header, reply_payload, host, port)
            retransmit_count = 0

        if time.time() - timer > timeout / 1000:
            # print('time up')
            reply_header, reply_payload = copy.deepcopy(init_segment)
            reply_header['DATA'] = True
            reply_header['ack'] = ack
            reply_header['seq'] = client_isn + MSS * send_base
            reply_payload = payload_pool[send_base]
            retran_count += 1
            PLD(reply_header, reply_payload, host, port)
            timer = time.time()

        if send_base >= len(payload_pool):
            # print('send done')
            break

        # lock.release()




def FIN_state():
    global ack
    global last_ack
    reply_header, reply_payload = copy.deepcopy(init_segment)
    reply_header['FIN'] = True
    reply_header['seq'] = last_ack
    reply_header['ack'] = ack
    s.sendto(pickle.dumps([reply_header, reply_payload]), (host, port))
    f.write('snd    {:<9.3f} F   {:<5d}  {:<5d}  {:<5d}\n'.format((time.time()-start)*1000, reply_header['seq'],0,reply_header['ack']))
    while True:
        data, addr = s.recvfrom(1024)
        received_header, received_payload = pickle.loads(data)
        if received_header['FIN'] and received_header['ACK'] and received_header['ack'] == (last_ack +1):
            last_ack += 1
            f.write('rcv    {:<9.3f} FA  {:<5d}  {:<5d}  {:<5d}\n'.format((time.time() - start) * 1000, received_header['seq'],0, received_header['ack']))
            reply_header, reply_payload = copy.deepcopy(init_segment)
            reply_header['ACK'] = True
            reply_header['ack'] = received_header['seq'] + 1
            reply_header['seq'] = last_ack
            s.sendto(pickle.dumps([reply_header, reply_payload]), addr)
            f.write('snd    {:<9.3f} A   {:<5d}  {:<5d}  {:<5d}\n'.format((time.time() - start) * 1000, reply_header['seq'],0,reply_header['ack']))
            time.sleep(1)
            break



host, port, file_name, MWS, MSS, timeout, pdrop, seed = [sys.argv[1],int(sys.argv[2]),sys.argv[3], int(sys.argv[4]),\
                                                         int(sys.argv[5]), int(sys.argv[6]),float(sys.argv[7]),\
                                                         int(sys.argv[8])]
random.seed(seed)
win_cap = MWS // MSS
send_base = 0
retransmit_count = 0
my_seq = 0
drop_count =retran_count = duplicate_count= 0
init_header = {'SP': -1 ,'DP': port,'SYN': False, 'ACK': False, 'FIN': False, 'DATA': False, 'seq': 0, 'ack': 0}
init_payload = ''
init_segment = [init_header, init_payload]
client_isn = 121
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

start = time.time()
with open('Sender_log.txt', 'w') as f:
    f.write('')
f = open('Sender_log.txt','a')
ack = SYN_state()
payload_pool = list()

last_ack = 0
lock = threading.Lock()
t1 = threading.Thread(target=send_thread)
t2 = threading.Thread(target=receive_thread)
t2.start()
trans_first_window()
t1.start()
t1.join()
t2.join()
FIN_state()
f.write('Amount of (original) Data Transferred (in bytes): {}\n'.format(data_amount))
f.write('Number of Data Segments Sent(excluding retransmissions): {}\n'.format(seg_number))
f.write('Number of (all) Packets Dropped (by the PLD module): {}\n'.format(drop_count))
f.write('Number of Retransmitted Segments: {}\n'.format( retran_count))
f.write('Number of Duplicate Acknowledgements received: {}\n'.format(duplicate_count))
f.close()

s.close()
