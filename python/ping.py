#!/usr/bin/python
# TODO: Get the address info to extract the IP address of the host

import argparse
import atexit

import math

from os import getpid

from socket import AF_INET, IP_MULTICAST_TTL, IPPROTO_ICMP, IPPROTO_IP, IP_TTL, SOCK_RAW
from socket import socket

import struct
import time

ICMP_TYPE = 8
ICMP_CODE = 0

IPV4_BYTES_LENGTH = 20

CHECK_SUM_UPPER_POS = 2
CHECK_SUM_LOWER_POS = 3

DEFAULT_TIMEOUT = 4.0

SEQ_BYTE_POS = 7

parser = argparse.ArgumentParser(description='ping - send ICMP ECHO_REQUEST to network hosts', prog='ping')
parser.add_argument('destination', help='The host address to ping; either a fully qualified domain name or an IP address.')
# TODO: ensure that count is an integer
parser.add_argument('-c', default=None, dest='count', metavar='count', help='')
parser.add_argument('-t', default=56, dest='ttl', metavar='ttl', help='The time-to-live value for outgoing packets.')

args = parser.parse_args()

# Given an number represented by an array of bytes from most significant number to least
# significant, calculate a checksum.
def calc_checksum(bytes):
    total = 0
    # Add each 16 bit segment of the ICMP message. To form the 16 bit segment, each
    # even byte is shifted 8 bits to the left. The following byte is added (without
    # any bit shifting).
    for idx, val in enumerate(bytes):
        if idx == 0 or idx % 2 == 0:
            total += val << 8
        else:
            total += val

    # If the value of the total exceeds the 2 octects, add the overflowing bits to the
    # 16 bit portion of total. Iterate through this process until there are no  more
    # overflowing bits left.
    while (total >> 16) > 0: total = (total & 0xFFFF) + (total >> 16)

    # Return the 16 bit one's complement, as an array of bytes
    return bytearray(struct.pack('!H', total ^ 0xFFFF))


# Callback function used with 'atexit'.
def close_socket(socket_connection):
    socket_connection.close()

def main():
    # The process ID of the process is used as the identifier. It's possible that the PID exceeds
    # the maximum possible value of an octet (65535), in which case the value is the bitwise 'and'
    # of the lower 4 bytes.
    pid_bytes = bytearray(struct.pack('!H', getpid() & 0xFFFF))

    # This list represents the initial values of the ICMP header. Each value in the list represents
    # a byte. Some values like the checksum, the identifier, and the sequence is represented by an
    # octet.
    header_values = [ICMP_TYPE, ICMP_CODE, 0, 0, pid_bytes[0], pid_bytes[1], 0, 0]

    s = socket(AF_INET, SOCK_RAW, IPPROTO_ICMP)

    # Set the time-to-live, specified either by the user or using the default value of 56.
    s.setsockopt(IPPROTO_IP, IP_TTL, args.ttl)
    s.settimeout(DEFAULT_TIMEOUT)

    s.connect((args.destination, 0))

    atexit.register(close_socket, socket_connection=s)

    while True:
        if args.count == 0:
            break
        # Reset the checksum so that it can be recalculated on the next interation
        header_values[CHECK_SUM_UPPER_POS], header_values[CHECK_SUM_LOWER_POS] = 0, 0

        # Get the current time represented as a float
        timestamp_before = time.time()

        # The timestamp in the ICMP message is represented by the significant followed
        # by the
        timestamp_bytes = bytearray(struct.pack(
            '!II',
            int(timestamp_before),
            int((timestamp_before - int(timestamp_before)) * 10 ** 6)
        ))

        # Set the payload of the packet to be an incremental range of bytes starting from
        if header_values[SEQ_BYTE_POS] == 0:
            payload_bytes = bytearray(range(len(timestamp_bytes), 56))
            print('PING (%s): %d data bytes' % (args.destination, len(timestamp_bytes) + len(payload_bytes)))

        header_values[CHECK_SUM_UPPER_POS], header_values[CHECK_SUM_LOWER_POS] = calc_checksum(
            header_values +
            list(timestamp_bytes) +
            list(payload_bytes)
        )

        header_bytes = bytearray(struct.pack(*(['!' + 'B' * len(header_values)] + header_values)))

        try:
            s.send(header_bytes + timestamp_bytes + payload_bytes)

            data = s.recv(256)
        except socket.timestamp as err:
            print(err)

        timestamp_after = time.time()

        timestamp_delta = round((timestamp_after - timestamp_before) * 1000, 3)

        print('%d bytes from %s: icmp_seq=%d ttl=%d time=%.3f ms' %
              (len(data) - IPV4_BYTES_LENGTH, args.destination, header_values[SEQ_BYTE_POS], args.ttl, timestamp_delta))

        header_values[SEQ_BYTE_POS] += 1

        time.sleep(1)

        if args.count is not None:
            args.count -= 1

if __name__ == "__main__":
    main()
