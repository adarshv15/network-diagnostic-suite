import socket
import struct
import time
import os

ICMP_ECHO_REQUEST = 8


def checksum(source):
    sum = 0
    count_to = (len(source) // 2) * 2
    count = 0

    while count < count_to:
        this_val = source[count + 1] * 256 + source[count]
        sum = sum + this_val
        sum = sum & 0xffffffff
        count += 2

    if count_to < len(source):
        sum += source[len(source) - 1]
        sum = sum & 0xffffffff

    sum = (sum >> 16) + (sum & 0xffff)
    sum += (sum >> 16)

    answer = ~sum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)

    return answer


def create_packet(id):
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, 0, id, 1)
    data = struct.pack("d", time.time())

    chksum = checksum(header + data)

    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0,
                         socket.htons(chksum), id, 1)

    return header + data


def ping(host, count=4):

    dest = socket.gethostbyname(host)

    output = f"\nPinging {host} [{dest}] with 32 bytes of data:\n\n"

    rtts = []

    for i in range(count):

        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)

        packet_id = os.getpid() & 0xFFFF
        packet = create_packet(packet_id)

        start = time.time()

        sock.sendto(packet, (dest, 1))
        sock.settimeout(2)

        try:
            sock.recvfrom(1024)
            end = time.time()

            rtt = (end - start) * 1000
            rtts.append(rtt)

            output += f"Reply from {dest}: time={round(rtt)}ms\n"

        except socket.timeout:
            output += "Request timed out\n"

        sock.close()

    sent = count
    received = len(rtts)
    lost = sent - received
    loss = (lost / sent) * 100

    if received > 0:
        minimum = min(rtts)
        maximum = max(rtts)
        avg = sum(rtts) / len(rtts)
    else:
        minimum = maximum = avg = 0

    output += f"\nPing statistics for {dest}:\n"
    output += f"    Packets: Sent = {sent}, Received = {received}, Lost = {lost} ({loss}% loss)\n"

    output += "\nApproximate round trip times in milli-seconds:\n"
    output += f"    Minimum = {round(minimum)}ms, Maximum = {round(maximum)}ms, Average = {round(avg)}ms\n"

    return output