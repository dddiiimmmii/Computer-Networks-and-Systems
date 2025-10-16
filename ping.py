import os
import sys
import socket
import struct
import time
import select

# ICMP消息类型
ICMP_ECHO_REQUEST = 8  # 回声请求
ICMP_ECHO_REPLY = 0    # 回声回复
ICMP_TIMEOUT = 11      # 超时
ICMP_DEST_UNREACH = 3  # 目标不可达

def checksum(source_string):
    """
    计算校验和，用于验证ICMP包的完整性
    """
    sum = 0
    max_count = (len(source_string) // 2) * 2
    count = 0
    while count < max_count:
        val = source_string[count + 1] * 256 + source_string[count]
        sum = sum + val
        sum = sum & 0xffffffff  # 确保在32位内
        count = count + 2

    # 处理奇数长度的情况
    if max_count < len(source_string):
        sum = sum + source_string[len(source_string) - 1]
        sum = sum & 0xffffffff

    # 折叠校验和
    sum = (sum >> 16) + (sum & 0xffff)
    sum = sum + (sum >> 16)
    answer = ~sum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

def create_icmp_packet(seq, pid):
    """
    创建ICMP回声请求包
    """
    # ICMP头部：类型(8)、代码(8)、校验和(16)、标识符(16)、序列号(16)
    header = struct.pack('!BBHHH', ICMP_ECHO_REQUEST, 0, 0, pid, seq)
    
    # 数据部分：发送时间戳 + 填充数据
    data_size = 56
    data = bytes([i & 0xff for i in range(data_size)])
    send_time = struct.pack('d', time.time())
    data = send_time + data
    
    # 计算校验和
    checksum_val = checksum(header + data)
    
    # 重新打包头部，包含正确的校验和
    header = struct.pack('!BBHHH', ICMP_ECHO_REQUEST, 0, socket.htons(checksum_val), pid, seq)
    
    return header + data

def ping(host, timeout=2, count=None):
    """
    向目标主机发送ICMP回声请求并处理响应
    host: 目标主机名或IP地址
    timeout: 超时时间(秒)
    count: 发送次数，None表示无限次直到中断
    """
    # 获取目标主机的IP地址
    try:
        dest_ip = socket.gethostbyname(host)
        print(f"正在 Ping {host} [{dest_ip}] 具有 64 字节的数据:")
    except socket.gaierror as e:
        print(f"无法解析主机 {host}: {e}")
        return
    
    # 创建原始套接字
    try:
        # 使用ICMP协议
        icmp = socket.getprotobyname("icmp")
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
    except PermissionError:
        print("需要管理员权限来运行此程序，请使用sudo或管理员身份运行")
        return
    except socket.error as e:
        print(f"创建套接字失败: {e}")
        return
    
    # 进程ID用于标识ICMP包
    pid = os.getpid() & 0xFFFF  # 确保在16位范围内
    
    # 统计信息
    sent = 0
    received = 0
    rtts = []
    
    try:
        seq = 1
        while count is None or sent < count:
            # 创建并发送ICMP包
            packet = create_icmp_packet(seq, pid)
            sock.sendto(packet, (dest_ip, 1))  # 端口号在这里无关紧要
            sent += 1
            
            # 等待响应
            start_select = time.time()
            ready = select.select([sock], [], [], timeout)
            select_time = time.time() - start_select
            
            # 超时
            if not ready[0]:
                print(f"来自 {dest_ip} 的回复: 超时")
                seq += 1
                time.sleep(1)  # 等待1秒再发送下一个包
                continue
            
            # 接收响应
            recv_time = time.time()
            recv_packet, addr = sock.recvfrom(1024)
            received += 1
            
            # 解析IP头（20字节）
            ip_header = recv_packet[:20]
            ip_version, ip_type, ip_length, ip_id, ip_flags, ip_ttl, ip_protocol, \
            ip_checksum, ip_src, ip_dst = struct.unpack('!BBHHHBBHII', ip_header)
            
            # 解析ICMP头
            icmp_header = recv_packet[20:28]
            icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_seq = struct.unpack('!BBHHH', icmp_header)
            
            # 验证是否是我们发送的包的回复
            if icmp_type == ICMP_ECHO_REPLY and icmp_id == pid and icmp_seq == seq:
                # 提取数据部分的发送时间戳
                data = recv_packet[28:]
                send_time = struct.unpack('d', data[:8])[0]
                rtt = (recv_time - send_time) * 1000  # 转换为毫秒
                rtts.append(rtt)
                
                # 显示结果
                print(f"来自 {addr[0]} 的回复: 字节=64 时间={rtt:.2f}ms TTL={ip_ttl}")
            elif icmp_type == ICMP_TIMEOUT:
                print(f"来自 {addr[0]} 的回复: TTL 传输中过期")
            elif icmp_type == ICMP_DEST_UNREACH:
                print(f"来自 {addr[0]} 的回复: 目标主机不可达")
            else:
                print(f"来自 {addr[0]} 的回复: 类型={icmp_type} 代码={icmp_code}")
            
            seq += 1
            time.sleep(1)  # 等待1秒再发送下一个包
            
    except KeyboardInterrupt:
        # 用户中断（Ctrl+C）
        print("\nPing 统计信息:")
        print(f"    针对 {host} [{dest_ip}]:")
        print(f"    数据包: 已发送 = {sent}, 已接收 = {received}, 丢失 = {sent - received} ({(sent - received)/sent*100:.1f}% 丢失)")
        
        if rtts:
            print("往返行程的估计时间(以毫秒为单位):")
            print(f"    最短 = {min(rtts):.2f}ms, 最长 = {max(rtts):.2f}ms, 平均 = {sum(rtts)/len(rtts):.2f}ms")
    finally:
        sock.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"用法: {sys.argv[0]} <主机名或IP地址> [超时时间(秒)] [次数]")
        print(f"示例: {sys.argv[0]} lancaster.ac.uk 2 4")
        sys.exit(1)
    
    host = sys.argv[1]
    timeout = float(sys.argv[2]) if len(sys.argv) > 2 else 2
    count = int(sys.argv[3]) if len(sys.argv) > 3 else None
    
    ping(host, timeout, count)
