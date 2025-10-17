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


def checksum(string):
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
    # 1. Build ICMP header
    myChecksum = 0
    
    # Header: type (8 bit) + code (8 bit) + checksum (16 bit) + id (16 bit) + sequence (16 bit)
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    
    # Data section includes timestamp for delay calculation
    data = struct.pack("d", time.time())
    
    # 2. Checksum ICMP packet using given function
    myChecksum = checksum(header + data)
    
    # 3. Insert checksum into packet
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data
    
    # 4. Send packet using socket
    # Dai Meng implements this part
    
    # 5. Record time of sending
    # Dai Meng implements this part
    
    pass


def receiveOnePing(icmpSocket, destinationAddress, ID, timeout):
    # 1. Wait for the socket to receive a reply
    # 2. Once received, record time of receipt, otherwise, handle a timeout
    # 3. Compare the time of receipt to time of sending, producing the total network delay
    # 4. Unpack the packet header for useful information, including the ID
    # 5. Check that the ID matches between the request and reply
    # 6. Return total network delay
    
    # Dai Meng implements this function
    pass


def doOnePing(destinationAddress, timeout):
    # 1. Create ICMP socket
    # 2. Call sendOnePing function
    # 3. Call receiveOnePing function
    # 4. Close ICMP socket
    # 5. Return total network delay
    
    # Zhou Yuxi implements this function
    pass


def ping(host, timeout=1):
    # 1. Look up hostname, resolving it to an IP address
    # 2. Call doOnePing function, approximately every second
    # 3. Print out the returned delay
    # 4. Continue this process until stopped
    
    # Zhou Yuxi implements this function
    pass


ping("lancaster.ac.uk")