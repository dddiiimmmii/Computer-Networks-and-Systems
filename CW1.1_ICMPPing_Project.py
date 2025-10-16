#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import socket
import os
import sys
import struct
import time
import select
import binascii

ICMP_ECHO_REQUEST = 8
ICMP_ECHO_REPLY = 0

# Wang Qihan - Basic modules (checksum & ICMP packet building)

def checksum(string):
    # calculate checksum for ICMP packet
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0
    
    while count < countTo:
        thisVal = string[count+1] * 256 + string[count]
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2
    
    if countTo < len(string):
        csum = csum + string[len(string) - 1]
        csum = csum & 0xffffffff
    
    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    
    answer = socket.htons(answer)
    
    return answer


def sendOnePing(icmpSocket, destinationAddress, ID):
    # Build ICMP header and packet
    myChecksum = 0
    
    # make header first with checksum = 0
    # format: type, code, checksum, id, sequence
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    
    # put timestamp in data section for RTT calculation
    data = struct.pack("d", time.time())
    
    # calculate checksum on header + data
    myChecksum = checksum(header + data)
    
    # rebuild header with real checksum
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    
    packet = header + data
    
    # Dai Meng will add socket send code here
    # icmpSocket.sendto(packet, (destinationAddress, 1))
    # also need to record send time
    
    pass


def receiveOnePing(icmpSocket, destinationAddress, ID, timeout):
    # Dai Meng's part - network receive & parse
    # wait for reply, calculate delay, check ID matches
    pass


def doOnePing(destinationAddress, timeout):
    # Zhou Yuxi's part - main control logic
    # create socket, call send/receive, close socket
    pass


def ping(host, timeout=1):
    # Zhou Yuxi's part - overall logic
    # resolve hostname, loop ping calls, print stats
    pass


ping("lancaster.ac.uk")