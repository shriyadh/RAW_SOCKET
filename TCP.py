import socket
import struct
from random import randint


class TCP:

    def __init__(self):
        self.client_ip = ''
        self.client_port = 0
        self.server_ip = ''
        self.server_port = 0
        self.sq_num = 0
        self.ack_num = 0
        # ip socket
        # cwnd

    def connect(self, server_ip, server_port):
        # destination IP address
        self.server_ip = socket.gethostbyname(server_ip)

        # server port is 80 (web)
        self.server_port = server_port

        # get local ip address
        # self.client_ip =

        # pick up any random port number which is not reserved
        self.client_port = randint(1024, 65353)


class TCPPacket:

    def __init__(self, data, src_port=0, dest_port=80, src_ip='', dest_ip=''):
        self.client_ip = src_ip
        self.client_port = src_port
        self.server_ip = dest_ip
        self.server_port = dest_port
        self.seq_num = randint(0, 100000)
        self.ack_num = 0
        self.offset = 5
        self.wnd_size = 2048
        self.checksum = 0
        self.urg_ptr = 0
        # flags
        self.fin = 0
        self.syn = 0
        self.rst = 0
        self.psh = 0
        self.ack = 0
        self.urg = 0

        self.data = data

    def create_TCP_packet(self):

        tcp_offset_res = (self.offset << 4) + 0
        tcp_flags = self.fin + (self.syn << 1) + (self.rst << 2) + (self.psh << 3) + (self.ack << 4) + (self.urg << 5)

        tcp_header_without_checksum = struct.pack('!HHLLBBHHH', self.client_port, self.server_port, self.seq_num,
                                                  self.ack_num, tcp_offset_res, tcp_flags,
                                                  self.wnd_size,
                                                  self.checksum, self.urg_ptr)

        # pseudo header fields from IP header -- should have source IP, Destination IP, Protocol field
        #  TCP length, TCP header ===== needed for calculating checksum accurately
        tcp_len = len(self.data) + len(tcp_header_without_checksum)


        pseudo_header = struct.pack('!4s4sBBH', socket.inet_aton(self.client_ip), socket.inet_aton(self.server_ip),
                                    0, socket.IPPROTO_TCP, tcp_len)

        final_header = pseudo_header + tcp_header_without_checksum + self.data
        self.checksum = calculate_checksum(final_header)

        # tcp header with checksum
        tcp_with_checksum = struct.pack('!HHLLBBHHH', self.client_port, self.server_port, self.seq_num, self.ack_num,
                                        tcp_offset_res, tcp_flags,
                                        self.wnd_size, self.checksum, self.urg_ptr)

        # final tcp packet --- header with checksum + data [[[[[[ TCP HEADER + DATA ]]]]]]]]]]]]
        tcp_segment = tcp_with_checksum + self.data

