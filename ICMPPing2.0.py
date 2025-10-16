#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import socket
import os
import sys
import struct
import time
import select
import binascii  
import pandas

ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request messages
ICMP_ECHO_REPLY = 0    # ICMP type code for echo reply messages


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


def receiveOnePing(icmpSocket, destinationAddress, ID, timeout):
    # 等待数据接收，设置超时
    startedSelect = time.time()
    whatReady = select.select([icmpSocket], [], [], timeout)
    waitTime = time.time() - startedSelect

    if not whatReady[0]:  # 超时
        return None

    timeReceived = time.time()
    recPacket, addr = icmpSocket.recvfrom(1024)

    # 解析IP头（前20字节）
    ipHeader = recPacket[:20]
    ipVersion, ipTypeOfService, ipLength, ipID, ipFlags, ipTTL, ipProtocol, \
    ipChecksum, ipSrc, ipDst = struct.unpack("!BBHHHBBHII", ipHeader)

    # 解析ICMP包（IP头之后）
    icmpHeader = recPacket[20:28]
    icmpType, icmpCode, icmpChecksum, icmpID, icmpSequence = struct.unpack(
        "!BBHHH", icmpHeader
    )

    # 验证是否是当前请求的回复
    if icmpType == ICMP_ECHO_REPLY and icmpID == ID:
        # 提取数据部分长度（总长度 - IP头 - ICMP头）
        dataSize = len(recPacket) - 28
        # 计算往返延迟（毫秒）
        delay = (timeReceived - float(struct.unpack("!d", recPacket[28:28+8])[0])) * 1000
        return delay

    return None


def sendOnePing(icmpSocket, destinationAddress, ID, sequence):
    # 构建ICMP头部（初始校验和为0）
    icmpHeader = struct.pack(
        "!BBHHH", ICMP_ECHO_REQUEST, 0, 0, ID, sequence
    )
    # 添加数据部分（8字节时间戳）
    data = struct.pack("!d", time.time())
    # 计算校验和
    checksumVal = checksum(icmpHeader + data)
    # 重新打包ICMP头部（包含正确校验和）
    icmpHeader = struct.pack(
        "!BBHHH", ICMP_ECHO_REQUEST, 0, checksumVal, ID, sequence
    )
    # 组合完整数据包
    packet = icmpHeader + data
    # 发送数据包
    icmpSocket.sendto(packet, (destinationAddress, 1))  # 端口号不影响ICMP


def doOnePing(destinationAddress, timeout, sequence):
    # 创建ICMP套接字
    try:
        icmpSocket = socket.socket(
            socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP
        )
    except PermissionError:
        print("错误：需要管理员/root权限运行此程序")
        sys.exit(1)
    except socket.error as e:
        print(f"创建套接字失败：{e}")
        return None

    # 获取当前进程ID作为ICMP包标识符
    ID = os.getpid() & 0xFFFF  # 限制为16位

    # 发送Ping请求
    sendOnePing(icmpSocket, destinationAddress, ID, sequence)
    # 接收Ping回复
    delay = receiveOnePing(icmpSocket, destinationAddress, ID, timeout)

    # 关闭套接字
    icmpSocket.close()
    return delay


def ping(host, timeout=1):
    try:
        # 解析主机名到IP地址
        destinationAddress = socket.gethostbyname(host)
        print(f"正在 Ping {host} [{destinationAddress}] 具有 32 字节的数据:")
    except socket.gaierror:
        print(f"无法解析主机 {host}")
        return

    sequence = 1
    try:
        while True:  # 持续Ping直到手动停止
            # 执行一次Ping
            delay = doOnePing(destinationAddress, timeout, sequence)
            
            if delay is not None:
                print(f"来自 {destinationAddress} 的回复: 字节=32 时间={delay:.2f}ms")
            else:
                print("请求超时。")
            
            sequence += 1
            time.sleep(1)  # 每秒发送一次

    except KeyboardInterrupt:
        # 处理Ctrl+C停止
        print("\nPing 统计信息:")
        print(f"    目标 {host} [{destinationAddress}]")
        # 这里可以添加更详细的统计（如发送/接收数量），简化版本省略


if __name__ == "__main__":
    # 可修改为目标主机，如 "baidu.com" 或 "127.0.0.1"
    ping("lancaster.ac.uk")