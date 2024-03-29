#!/usr/bin/env python3
import fcntl
import socket
import struct
import sys
import time
from queue import PriorityQueue
from random import randint
from urllib.parse import urlparse

from IP import IP


def calculate_checksum(msg):
    """
    This method calculates the checksum of the headers
    :param msg: Takes in the message data
    :return: checksum
    """
    s = 0
    # if len of msg is odd
    if len(msg) % 2 != 0:
        msg += b'\0'

    # loop taking 2 characters at a time
    for i in range(0, len(msg), 2):
        # removed ord to work w bytes -> ord worked only for string
        w = msg[i] + (msg[i + 1] << 8)
        s = s + w
    s = (s >> 16) + (s & 0xffff)
    s = s + (s >> 16)
    # complement and mask to 4 byte short
    s = ~s & 0xffff
    return s


class TCP:
    """
       This class implements features of the TCP Layer.
    """

    def __init__(self):
        self.client_ip = ''
        self.client_port = -999
        self.server_ip = ''
        self.server_port = -999
        self.sq_num = 0
        self.ack_num = 0
        self.ip_socket = IP()
        self.cwnd = 1  # max of 1000 ; set back to 1 if packet dropped
        self.server_name = ''
        self.file_name = ''
        self.file_path = ''
        self.file_data = bytearray()

    def get_file_name(self, url):
        """
        This method parses the url to retrieve the attributes of the link for download and set parameters.
        :param url: link to download
        :return: server name
        """
        paths = urlparse(url)
        self.server_name = paths.netloc

        get_path = paths.path
        if get_path == '':
            self.file_path = "/"
        else:
            self.file_path = paths.path

        individual_path = paths.path.split("/")  # split the paths into sections
        individual_path = list(filter(None, individual_path))  # remove blanks

        if  url.endswith('/'):  # if empty, there was no filename given
            self.file_name = 'index.html'
        else:
            self.file_name = url.split('/')[-1] # take last path

    def establish_handshake(self, url, server_port):
        """
        This method establishes the three-way handshake between client and server
        :param url: link
        :param server_port: host port
        :return: None
        """
        print("======THREE WAY HANDSHAKE IN PROGRESS======")

        # get the file name from the server name by parsing
        self.get_file_name(url)
        # server IP address # DNS === get Server IP Address
        self.server_ip = socket.gethostbyname(self.server_name)
        # server port is 80 (web)
        self.server_port = server_port
        # get local ip address
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.connect(("david.choffnes.com", 80))
            ip, port = sock.getsockname()

        except Exception as err:
            raise err
        finally:
            sock.close()
        self.client_ip = ip

        self.client_port = port
        self.ip_socket.client_ip = self.client_ip
        self.ip_socket.server_ip = self.server_ip

        # THREE WAY HANDSHAKE ------ set SEQ num (random) and ACK = 0
        self.sq_num = randint(1, 65535)
        self.ack_num = 0
        # send the first SYN to do the three-way handshake
        # reset packet parameters
        tcp_packet = self.create_tcp_SYN()
        # pack the TCP packet
        tcp_seg = tcp_packet.pack_TCP_packet()

        # -----------------------  Call ip function for building IP DATAGRAM  ------------------------------
        # pack tcp segment into ip packet
        self.ip_socket.send_message(tcp_seg)
        #  NEXT --- receive SYN ACK
        send_backup = tcp_seg
        unpack_recv = None
        try:
            # receive tcp packet w/o ip headers
            cur = time.time()
            while (time.time() - cur) < 60:
                # create new tcp packet
                unpack_recv = TCPPacket()
                try:
                    packet_recv = self.ip_socket.receive_message()
                except:
                    continue

                unpack_recv.client_ip = self.server_ip
                unpack_recv.server_ip = self.client_ip
                unpack_recv.unpack_received_packet(packet_recv, self.server_ip, self.client_ip)
                # see if packet is correct
                if unpack_recv.client_port == self.server_port and unpack_recv.server_port == self.client_port:
                    break
                else:
                    continue

        except CheckSumErr as err:
            self.cwnd -= 1
            self.ip_socket.send_message(send_backup)
        except:
            self.cwnd = 1
            self.ip_socket.send_message(send_backup)

            # filter packets that belong to the client
        if unpack_recv.ack_num == self.sq_num + 1 and unpack_recv.syn == 1 and unpack_recv.ack == 1:
            self.ack_num = unpack_recv.seq_num + 1
            self.sq_num = unpack_recv.ack_num
            # setting up the congestion window
            if self.cwnd + 1 >= 1000:
                self.cwnd = 1000
            else:
                self.cwnd += 1
        else:
            self.cwnd -= 1
            self.ip_socket.send_message(send_backup)  # SEND AGAIN

        # SEND ACK
        tcp_packet = self.create_tcp_ACK()
        tcp_seg = tcp_packet.pack_TCP_packet()
        self.ip_socket.send_message(tcp_seg)

        print("======THREE WAY HANDSHAKE ESTABLISHED======")

    def begin_teardown(self):
        """
        This method deals with handling the proper connection teardown between client and server.
        :return: None
        """

        # SEND FIN ACK
        finish_packet = self.create_tcp_FIN()
        final_bye = finish_packet.pack_TCP_packet()
        self.ip_socket.send_message(final_bye)

        # Receive FIN+ACK
        recv_FIN_ACK = None
        try:
            # receive tcp packet w/o ip headers
            cur = time.time()
            while (time.time() - cur) < 60:
                # create new tcp packet
                recv_FIN_ACK = TCPPacket()
                try:
                    packet_recv_FIN = self.ip_socket.receive_message()
                except:
                    continue

                recv_FIN_ACK.client_ip = self.server_ip
                recv_FIN_ACK.server_ip = self.client_ip
                recv_FIN_ACK.unpack_received_packet(packet_recv_FIN, self.server_ip, self.client_ip)

                # Filter out packets
                if recv_FIN_ACK.client_port == self.server_port and recv_FIN_ACK.server_port == self.client_port:
                    break
                else:
                    continue
        except CheckSumErr as err:
            print("TIMEOUT")

        self.ack_num = recv_FIN_ACK.seq_num + 1
        self.sq_num = recv_FIN_ACK.ack_num

        # SEND ACK for final FIN ACK
        final_ack = self.create_tcp_ACK()
        pack_final_ack = final_ack.pack_TCP_packet()
        self.ip_socket.send_message(pack_final_ack)
        self.ip_socket.close_sockets()

    def create_tcp_FIN(self):
        """
        This method sets the appropriate parameters for the TCP FIN response.
        :return: TCP Pakcet
        """
        tcp_pack = TCPPacket()
        tcp_pack.server_ip = self.server_ip
        tcp_pack.client_ip = self.client_ip
        tcp_pack.client_port = self.client_port
        tcp_pack.server_port = self.server_port
        tcp_pack.seq_num = self.sq_num
        tcp_pack.ack_num = self.ack_num  # 0
        tcp_pack.fin = 1
        tcp_pack.psh = 1
        tcp_pack.ack = 1
        return tcp_pack

    def create_tcp_SYN(self):
        """
        This method sets the appropriate parameters for the TCP SYN response.
        :return: TCP Pakcet
        """
        tcp_pack = TCPPacket()
        tcp_pack.server_ip = self.server_ip
        tcp_pack.client_ip = self.client_ip
        tcp_pack.client_port = self.client_port
        tcp_pack.server_port = self.server_port
        tcp_pack.seq_num = self.sq_num
        tcp_pack.ack_num = self.ack_num  # 0
        tcp_pack.syn = 1
        return tcp_pack

    def create_tcp_ACK(self):
        """
        This method sets the appropriate parameters for the TCP ACK response.
        :return: TCP Pakcet
        """
        tcp_pack = TCPPacket()
        tcp_pack.server_ip = self.server_ip
        tcp_pack.client_ip = self.client_ip
        tcp_pack.client_port = self.client_port
        tcp_pack.server_port = self.server_port
        tcp_pack.seq_num = self.sq_num
        tcp_pack.ack_num = self.ack_num  # 0
        tcp_pack.ack = 1
        return tcp_pack

    def create_tcp_PSH(self, data):
        """
        This method sets the appropriate parameters for the TCP PSH ACK response.
        :return: TCP Pakcet
        """
        tcp_pack = TCPPacket()
        tcp_pack.server_ip = self.server_ip
        tcp_pack.client_ip = self.client_ip
        tcp_pack.client_port = self.client_port
        tcp_pack.server_port = self.server_port
        tcp_pack.seq_num = self.sq_num
        tcp_pack.ack_num = self.ack_num  # 0
        tcp_pack.psh = 1
        tcp_pack.ack = 1
        tcp_pack.data = data.encode()
        return tcp_pack

    def send_http_req(self):
        """
        This method creates the appropriate GET request for the server and sends it across
        :return: None
        """

        # GET request
        req = f'GET {self.file_path} HTTP/1.1\r\nHost: {self.server_name}\r\n\r\n'
        # create http packet
        h_packet = self.create_tcp_PSH(req)
        h_seg = h_packet.pack_TCP_packet()
        self.ip_socket.send_message(h_seg)

        # receive the response
        self.download_http()

    def download_http(self):
        """
        This function downloads the file over HTTP by sending and receiving acks.
        Once a fin flag is received, all data has been received
        :return: None
        """
        print("======DOWNLOAD BEGINNING======")

        packets = PriorityQueue()
        sequence_num_expect = self.ack_num
        fin_flag = 0
        seq_set = set()
        # keep track of ack numbers
        prev_sq_num = self.sq_num
        prev_ack_num = self.ack_num
        self.ip_socket.recv_socket.settimeout(180)  # set socket timeout to 3 minutes

        # first response ack
        unpack_recv = TCPPacket()
        packet_recv = self.ip_socket.receive_message()
        unpack_recv.client_ip = self.server_ip
        unpack_recv.server_ip = self.client_ip
        unpack_recv.unpack_received_packet(packet_recv, self.server_ip, self.client_ip)

        if unpack_recv.seq_num == sequence_num_expect:
            print("\n ======RECEIVING PACKETS======\n")
            # receive the incoming packets in a loop until all http data received
            while not fin_flag:
                self.ip_socket.recv_socket.settimeout(180)  # give socket 3 minutes to receive data
                try:
                    current_time = time.time()
                    while True:
                        unpack_recv = TCPPacket()
                        try:
                            packet_recv = self.ip_socket.receive_message()
                        except self.ip_socket.recv_socket.timeout:  # 3 minutes has passed
                            print("Sorry the connection has failed.")
                            self.ip_socket.close_sockets()
                            sys.exit()
                        # retrieve fields from packet
                        unpack_recv.client_ip = self.server_ip
                        unpack_recv.server_ip = self.client_ip
                        unpack_recv.unpack_received_packet(packet_recv, self.server_ip, self.client_ip)

                        # Filter out
                        if unpack_recv.client_port == self.server_port and unpack_recv.server_port == self.client_port:
                            break

                        response_time = time.time() - current_time  # get how much time has passed since ack

                        if response_time >= 60:  # one minute passes
                            # resend ack
                            self.cwnd = 1

                            # retrieve preciously sent ack num and sequence nums
                            self.sq_num = prev_sq_num
                            self.ack_num = prev_ack_num

                            # create and send backup ack
                            resp_ack = self.create_tcp_ACK()
                            resp_packet = resp_ack.pack_TCP_packet()
                            self.ip_socket.send_message(resp_packet)
                            current_time = time.time()
                            continue

                except CheckSumErr as err:
                    self.cwnd -= 1

                # get the sequence number, ack num, and http data of the packet
                sequence_num = unpack_recv.seq_num
                aknow_num = unpack_recv.ack_num
                http_data = unpack_recv.data
                fin_flag = unpack_recv.fin

                # add the sequence number and data to the queue
                # check if seq number is already in the set === DROP DUPLICATES
                if sequence_num not in seq_set:
                    packets.put((sequence_num, http_data))
                    seq_set.add(sequence_num)
                else:
                    # do nothing --- do not add to queue cause DUPLICATE
                    pass

                # while we have the expected sequence number
                while not packets.empty() and packets.queue[0][0] == sequence_num_expect:
                    d = packets.get()  # pop the first packet
                    sequence_num = d[0]
                    http_data = d[1]
                    self.file_data += http_data  # add to bytearray

                    length = len(http_data)
                    self.sq_num = aknow_num  # updated ack and seq number
                    self.ack_num = sequence_num + length

                    # update the stored acknowledgement number and sequence number
                    prev_sq_num = self.sq_num
                    prev_ack_num = self.ack_num

                    # congestion window
                    if self.cwnd + 1 >= 1000:
                        self.cwnd = 1000
                    else:
                        self.cwnd += 1

                    if fin_flag == 0:  # more data to come
                        # send ack
                        resp_ack = self.create_tcp_ACK()
                        resp_packet = resp_ack.pack_TCP_packet()
                        self.ip_socket.send_message(resp_packet)

                        # update the expected num
                        sequence_num_expect = self.ack_num

                    if fin_flag == 1:  # all data received
                        # send fin
                        self.ack_num = sequence_num + 1
                        self.begin_teardown()

        self.write_to_file()

    def chunked_encoding(self, data_received):
        """
        This method deals with chunk encoded data and parses it for the same.
        return: parsed data
        """

        print("This file is Chunked!")

        data = data_received.split(b"\r\n")
        chunked_data = b''
        for i in range(len(data)):
            if i % 2 ==1:
                chunked_data += data[i]
            elif data[i] == b"0":
                return chunked_data

        return chunked_data

    def write_to_file(self):
        """
        This function writes the stored bytearray to file in the current directory
        :return: None
        """
        splitter = bytearray("\r\n\r\n", "utf-8")  # split header from content
        file = self.file_data.split(splitter)  # split header into fields
        header = file[0]
        self.file_data = file[1]  # only store the body

        status = bytearray("HTTP/1.1", "utf-8")
        if status in header:
            header = header.split()
            idx = header.index(status)
            status_code = header[idx + 1]
            # check status code
            if status_code != b'200':  # only acceptable status code
                sys.exit("Sorry, there was an error downloading the file.")

        if b"chunked" in header:
            contents = self.chunked_encoding(self.file_data)
            with open(self.file_name, "wb") as output:
                output.write(contents)

            print("======FILE DOWNLOAD COMPLETE======")
        else:
            self.write_to_file_non_chunk( self.file_data)
    def write_to_file_non_chunk(self,  file_data):

        print("This file is not chunked")
        self.file_data = file_data

        with open(self.file_name, "wb") as output:
            output.write(self.file_data)
        print("======FILE DOWNLOAD COMPLETE======")


class TCPPacket:
    """
    This class represents the TCP header as seen in datagrams.
    All fields within the TCP header are given as instance variables.
    This class contains two methods for packing and unpacking a TCP packet
    """

    def __init__(self, data=b'', src_port=0, dest_port=80, src_ip='', dest_ip=''):
        self.client_ip = src_ip
        self.client_port = src_port
        self.server_ip = dest_ip
        self.server_port = dest_port
        self.seq_num = 0
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

    def pack_TCP_packet(self):
        """
        This method creates a packet with a TCP header and correctly computes the checksum
        :return: TCP Segment
        """

        tcp_offset_res = (self.offset << 4) + 0
        tcp_flags = self.fin + (self.syn << 1) + (self.rst << 2) + (self.psh << 3) + (self.ack << 4) + (self.urg << 5)

        tcp_header_without_checksum = struct.pack('!HHLLBBH', self.client_port, self.server_port, self.seq_num,
                                                  self.ack_num, tcp_offset_res, tcp_flags,
                                                  self.wnd_size) + struct.pack('H', self.checksum) \
                                      + struct.pack('!H', self.urg_ptr)
        # pseudo header fields from IP header -- should have source IP, Destination IP, Protocol field
        # TCP length, TCP header ===== needed for calculating checksum accurately

        tcp_len = len(self.data) + (self.offset * 4)
        pseudo_header = struct.pack('!4s4sBBH', socket.inet_aton(self.client_ip), socket.inet_aton(self.server_ip),
                                    0, socket.IPPROTO_TCP, tcp_len)
        final_header = pseudo_header + tcp_header_without_checksum + self.data
        self.checksum = calculate_checksum(final_header)

        # tcp header with checksum
        tcp_with_checksum = struct.pack('!HHLLBBH', self.client_port, self.server_port, self.seq_num,
                                        self.ack_num, tcp_offset_res, tcp_flags,
                                        self.wnd_size) + struct.pack('H', self.checksum) \
                            + struct.pack('!H', self.urg_ptr)

        # final tcp packet --- header with checksum + data [[[[[[ TCP HEADER + DATA ]]]]]]]]]]]] = TCP SEGMENT
        tcp_segment = tcp_with_checksum + self.data

        return tcp_segment

    def unpack_received_packet(self, recv_segment, client, server):
        """
        This method unpacks a packet after it has been received from the IP class.
        It accurately computes the checksum to ensure the data has not been corrupted.
        :return:
        """
        tcp_header = struct.unpack('!HHLLBBH', recv_segment[0:16])
        self.client_ip = client
        self.server_ip = server
        self.client_port = tcp_header[0]
        self.server_port = tcp_header[1]
        self.seq_num = tcp_header[2]
        self.ack_num = tcp_header[3]
        offset = tcp_header[4]
        self.offset = (offset >> 4) * 4
        flags = tcp_header[5]
        self.wnd_size = tcp_header[6]
        self.checksum = struct.unpack('H', recv_segment[16:18])
        self.urg = struct.unpack('!H', recv_segment[18:20])
        self.data = recv_segment[self.offset:]

        # flags in segment
        self.fin = flags & 0x01
        self.syn = (flags & 0x02) >> 1
        self.rst = (flags & 0x04) >> 2
        self.psh = (flags & 0x08) >> 3
        self.ack = (flags & 0x10) >> 4
        self.urg = (flags & 0x20) >> 5

        # pseudo header fields from IP header -- should have source IP, Destination IP, Protocol field
        # TCP length, TCP header ===== needed for calculating checksum accurately
        tcp_len = len(self.data) + self.offset

        pseudo_header = struct.pack('!4s4sBBH',
                                    socket.inet_aton(self.client_ip),
                                    socket.inet_aton(self.server_ip),
                                    0, socket.IPPROTO_TCP, tcp_len)

        to_check = pseudo_header + recv_segment

        if calculate_checksum(to_check) != 0:  # error in packet
            raise CheckSumErr("TCP PACKET")
        else:  # packet is fine
            pass


class CheckSumErr(Exception):
    """
    This class deals with creating the checksum error exception.
    """
    def __init__(self, type):
        self.type = type

    def __str__(self):
        return self.type + "Checksum Error"
