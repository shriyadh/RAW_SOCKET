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

    def __init__(self):
        print("In Constructor for TCP")
        self.client_ip = ''
        self.client_port = -999
        self.server_ip = ''
        self.server_port = -999
        self.sq_num = 0
        self.ack_num = 0
        self.ip_socket = IP()
        self.cwnd = 1  # max of 1000 ; set back to 1 if packet dropped
        self.file_name = ''
        self.file_path = ''
        self.file_data = b''

    def get_file_name(self, url):
        paths = urlparse(url)
        server_name = paths.netloc

        get_path = paths.path
        if get_path is '':
            self.file_path = "/"
        else:
            self.file_path = paths.path

        individual_path = paths.path.split("/")  # split the paths into sections
        individual_path = list(filter(None, individual_path))  # remove blanks

        if not individual_path:  # if empty, there was no filename given
            self.file_name = 'index.html'
        else:
            self.file_name = 'test-MINE.log'  # take last path
            print("made")

        return server_name

    def establish_handshake(self, url, server_port):
        # get the file name from the server name by parsing
        # set it to self.file_name
        server_ip = self.get_file_name(url)
        print(server_ip)
        print("\n\n*****ESTABLISHING handshake****\n\n")

        # server IP address # DNS === get Server IP Address
        self.server_ip = socket.gethostbyname(server_ip)
        print("SERVER IP IS___ " + self.server_ip)
        # server port is 80 (web)
        self.server_port = server_port
        print("SERVER PORT IS___ ", self.server_port)

        # get local ip address
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            sock.connect(("david.choffnes.com", 80))
            ip, port = sock.getsockname()
            print("))IP*****************************************", ip)

        except Exception as err:
            raise err
        finally:
            sock.close()

        self.client_ip = ip
        print("CLIENT IP IS___ " + self.client_ip)

        # pick up any random port number which is not reserved
        self.client_port = port #randint(1024, 65535)  # self.ip_socket.bind_socket()
        # self.ip_socket.recv_socket.bind((self.client_ip,0))
        # self.client_port = self.ip_socket.recv_socket.getsockname()[1]
        # print("CLIENT PORT IS___ ", self.client_port)

        self.ip_socket.client_ip = self.client_ip
        self.ip_socket.server_ip = self.server_ip
        # self.ip_socket.client_port = self.client_port

        # THREE WAY HANDSHAKE ------ set SEQ num (random) and ACK = 0
        self.sq_num = randint(1, 65535)
        self.ack_num = 0
        # send the first SYN to do the three-way handshake
        # reset packet parameters
        tcp_packet = self.create_tcp_SYN()

        # pack the TCP packet
        tcp_seg = tcp_packet.pack_TCP_packet()

        # -----------------------  Call ip function for building IP DATAGRAM

        # pack tcp segment into ip packet
        self.ip_socket.send_message(tcp_seg)  # NEED MARIAH'S CODE FOR THIS

        #  NEXT --- receive SYN ACK ------------------- HOW ARE WE HANDLING CONGESTION WINDOW??? WHAT CHECKS DO WE NEED?
        send_backup = tcp_seg
        print("FIRST SYNNN", tcp_packet.seq_num)
        print("FIRST ACKKK", tcp_packet.ack_num)

        unpack_recv = None

        try:
            # receive tcp packet w/o ip headers
            cur = time.time()
            while (time.time() - cur) < 60:
                # create new tcp packet
                unpack_recv = TCPPacket()
                try:
                    packet_recv = self.ip_socket.receive_message(self.client_ip)  # NEED MARIAH"S CODE FOR THIS
                except:
                    continue

                print("in here")
                unpack_recv.client_ip = self.server_ip
                unpack_recv.server_ip = self.client_ip
                unpack_recv.unpack_received_packet(packet_recv, self.server_ip, self.client_ip)
                print("UNPACKED")

                # see if packet is correct
                if unpack_recv.client_port == self.server_port and unpack_recv.server_port == self.client_port:
                    print("############################FOUND")
                    break
                else:
                    continue

        except:
            print("EXCEPTION")
            self.cwnd = 1
            self.ip_socket.send_message(send_backup)  # NEED MARIAH'S CODE FOR THIS

        if unpack_recv.ack_num == self.sq_num + 1 and unpack_recv.syn == 1 and unpack_recv.ack == 1:
            self.ack_num = unpack_recv.seq_num + 1
            self.sq_num = unpack_recv.ack_num
            print("RECEIVED ACK: ", unpack_recv.seq_num)
            print("RECEIVED SEQ --->> REPLY BACK W THIS", unpack_recv.ack_num)
            if self.cwnd + 1 >= 1000:
                self.cwnd = 1000
            else:
                self.cwnd += 1
        else:
            self.cwnd -= 1
            self.ip_socket.send_message(send_backup)  # SEND AGAIN

            # use unpack function to unpack the received tcp packet
        print("RECEIVED %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")

        # SEND ACK
        tcp_packet = self.create_tcp_ACK()
        tcp_seg = tcp_packet.pack_TCP_packet()
        self.ip_socket.send_message(tcp_seg)  # NEED MARIAH'S CODE FOR THIS
        # print("SECOND SEQQQQ", tcp_packet.seq_num)
        # print("SECOND ACKKKK", tcp_packet.ack_num)
        print("################### THREE WAY HANDSHAKE #####################")
        ################ THREE WAY HANDSHAKE ESTABLISHED #################

    def begin_teardown(self):

        # SEND FIN ACK
        finish_packet = self.create_tcp_FIN()
        final_bye = finish_packet.pack_TCP_packet()
        self.ip_socket.send_message(final_bye)

        # print("SENT BYE+++++++++++++++++++++++++++++++ ")
        # print("SEND SEQ:", finish_packet.seq_num)
        # print("ACK NUM", finish_packet.ack_num)
        # Receive FIN+ACK
        recv_FIN_ACK = None
        try:
            # receive tcp packet w/o ip headers
            cur = time.time()
            while (time.time() - cur) < 60:
                # create new tcp packet
                recv_FIN_ACK = TCPPacket()
                try:
                    # print("OOOOOOOOOOOOOOOOOOOO", self.client_ip, self.server_ip)
                    packet_recv_FIN = self.ip_socket.receive_message(self.client_ip)
                except:
                    continue

                # print("in here")
                recv_FIN_ACK.client_ip = self.server_ip
                recv_FIN_ACK.server_ip = self.client_ip
                recv_FIN_ACK.unpack_received_packet(packet_recv_FIN, self.server_ip, self.client_ip)
                print("UNPACKED")

                # see if packet is correct
                if recv_FIN_ACK.client_port == self.server_port and recv_FIN_ACK.server_port == self.client_port:
                    print("############################FOUND")
                    break
                else:
                    continue
        except:
            print("TIMEOUT")

        self.ack_num = recv_FIN_ACK.seq_num + 1
        self.sq_num = recv_FIN_ACK.ack_num
        # print("SEQ", self.sq_num)
        # print("ACk", self.ack_num)

        print("RECEIVED BYE ACKKK+++++++++++++++++++++++++++++++ ")

        # SEND ACK for final FIN ACK
        final_ack = self.create_tcp_ACK()
        pack_final_ack = final_ack.pack_TCP_packet()
        # print(final_ack.server_ip)
        # print(final_ack.client_ip)
        print("SEQ", final_ack.seq_num)
        print("ACk", final_ack.ack_num)
        print(pack_final_ack)

        self.ip_socket.send_message(pack_final_ack)

        self.ip_socket.close_sockets()

        print("********************* CONNECTION TEARDOWN **************")
        # self.ip_socket.close_sockets()

    def create_tcp_FIN(self):
        print("CREATING SYN PACKET ********************")
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
        # add ack flag once start sending packets to acknowldge last packet
        return tcp_pack

    def create_tcp_SYN(self):
        print("CREATING SYN PACKET ********************")
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
        print("CREATING ACK PACKET ********************")
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
        print("creating psh packet")
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

        req = f'GET {self.file_path} HTTP/1.1\r\nHost: david.choffnes.com\r\n' \
              'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8\r\n' \
              'Accept-Language: en-US,en;q=0.5\r\n' \
              'Accept-Encoding: gzip, deflate\r\n' \
              'Connection: keep-alive\r\n' \
              'Upgrade-Insecure-Requests: 1\r\n' \
              'Cache-Control: max-age=0\r\n\r\n'
        # print(req)

        # seg_size = 1460

        # create http packet
        h_packet = self.create_tcp_PSH(req)
        h_seg = h_packet.pack_TCP_packet()
        # print("#################################",h_seg)
        self.ip_socket.send_message(h_seg)

    def receive_http(self):
        # using a priority queue to keep track of in order packets
        # put in the queue
        # send acks for the first packet it is expected and add to the data fiel string
        # remove from queue
        # create priority queue
        packets = PriorityQueue()
        sequence_num_expect = self.ack_num
        fin_flag = 0
        seq_set = set()

        # first response ack
        unpack_recv = TCPPacket()
        packet_recv = self.ip_socket.receive_message(self.client_ip)
        unpack_recv.client_ip = self.server_ip
        unpack_recv.server_ip = self.client_ip
        unpack_recv.unpack_received_packet(packet_recv, self.server_ip, self.client_ip)

        if unpack_recv.seq_num == sequence_num_expect:
            print("yes!!!!!!")

            # receive the incoming packets in a loop until all http data received

            while not fin_flag:
                print("not complete")
                print("expected", sequence_num_expect)

                try:
                    cur = time.time()
                    while (time.time() - cur) < 60:
                        unpack_recv = TCPPacket()
                        try:
                            packet_recv = self.ip_socket.receive_message(self.client_ip)
                        except:
                            continue
                        unpack_recv.client_ip = self.server_ip
                        unpack_recv.server_ip = self.client_ip
                        unpack_recv.unpack_received_packet(packet_recv, self.server_ip, self.client_ip)

                        # Filter out
                        if unpack_recv.client_port == self.server_port and unpack_recv.server_port == self.client_port:
                            break
                        else:
                            continue
                except:
                    print("timeout")
                    self.cwnd = 1
                    # SEND BACK UP ACKKKKK ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

                # get the sequence number and length of the packet
                sequence_num = unpack_recv.seq_num
                aknow_num = unpack_recv.ack_num
                http_data = unpack_recv.data
                fin_flag = unpack_recv.fin
                length = len(http_data)
                # print("LENGTTTTTHHHHHH", length)
                # print("~~~~~~~~~~~~~~~~~~~~~server sequence", sequence_num)
                # # print("~~~~~~~~~~~~~~~~~~expected", sequence_num_expect)
                # print("~~~~~~~~~~~~~~~~~~~~~~server ack num", aknow_num)
                # print("~~~~~~~~~~~~~~~~~~expected seq num", sequence_num_expect)

                # add the sequence number and data to the queue
                # check if seq number is already in the set
                if sequence_num not in seq_set:
                    packets.put((sequence_num, http_data))
                    seq_set.add(sequence_num)
                else:
                    # do nothing --- do not add to queue cause DUPLICATE
                    pass

                # check to see if buffer is ordered
                # will need to account for case that seq. no not received
                # will need to send multiple acks


                while not packets.empty() and packets.queue[0][0] == sequence_num_expect:  # while we have the expected seq num

                    print("matches")
                    d = packets.get()
                    sequence_num = d[0]
                    http_data = d[1]  # get associated http data
                    self.file_data += http_data  # add to byte string

                    # updated ack and seq number
                    length = len(http_data)
                    self.sq_num = aknow_num
                    self.ack_num = sequence_num + length
                    print("my sent seq", self.sq_num)
                    print("my sent ack", self.ack_num)
                    # print("ack in second", self.ack_num)
                    # print("seq num of pac",self.sq_num)
                    if self.cwnd +1 >= 1000:
                        self.cwnd = 1000
                    else:
                        self.cwnd += 1

                    if fin_flag == 0:
                        # send ack
                        resp_ack = self.create_tcp_ACK()
                        resp_packet = resp_ack.pack_TCP_packet()
                        self.ip_socket.send_message(resp_packet)
                        print("sent acks http")

                        # update the expected num
                        print("not updated seq expect", sequence_num_expect)
                        sequence_num_expect = self.ack_num
                        print("updated seq expect", sequence_num_expect)

                    if fin_flag == 1:
                        # send fin
                        # resp_fin = self.create_tcp_FIN()
                        # resp_packet = resp_fin.pack_TCP_packet()
                        self.ack_num = sequence_num + 1
                        self.begin_teardown()

                        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

                    # print("UPDATE!")
                # print(packets.queue)
                print("outside of queue loop !!!!!!!!!!!!!!!!!!!!!!!!!---length of q", len(packets.queue))

        print("ENDDDDDD OFFFF FILEEEE")
        self.write_to_file()

    def chunked_encoding(self, recv_data):

        data = recv_data.split(b"\r\n")

        data_total = b''

        for i in range(len(data)):
            if i % 2 == 1:
                data_total += data[i]
            elif data[i] == b"0":
                return data_total

        return  data_total

    def write_to_file(self):
        splitter = bytearray("\r\n\r\n", "utf-8")  # split header from content
        file = self.file_data.split(splitter)  # split header into fields

        header = file[0]
        self.file_data = file[1]  # only store the body
        print("######################################", file[0])

        # check status code
        status = bytearray("HTTP/1.1", "utf-8")
        if status in header:
            print("IN HEADERRRRR CORECT STATUS")
            header = header.split()
            idx = header.index(status)
            status_code = header[idx + 1]
            print(status_code)
            if status_code != b'200':
                sys.exit("Sorry, there was an error downloading the file.")

        with open(self.file_name, "wb") as output:
            # print("DATTTTTTTAAAAAAAAAAAAA", self.file_data)
            output.write(self.file_data)


class TCPPacket:

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
        # print(self.client_port, self.server_port)

        tcp_offset_res = (self.offset << 4) + 0
        tcp_flags = self.fin + (self.syn << 1) + (self.rst << 2) + (self.psh << 3) + (self.ack << 4) + (self.urg << 5)

        # mss_option = struct.pack('!HH', 2, 1460)
        # nop_option = b"\x01\x01"
        # sack_perm_option = b"\x04\x02\x00\x00"
        # options = mss_option + nop_option + sack_perm_option
        tcp_header_without_checksum = struct.pack('!HHLLBBH', self.client_port, self.server_port, self.seq_num,
                                                  self.ack_num, tcp_offset_res, tcp_flags,
                                                  self.wnd_size) + struct.pack('H', self.checksum) + struct.pack('!H',
                                                                                                                 self.urg_ptr)

        # self.options = b'\x02\x04\x05\xb4\x01\x01\x04\x02'

        # tcp_header_without_checksum += options

        # pseudo header fields from IP header -- should have source IP, Destination IP, Protocol field
        #  TCP length, TCP header ===== needed for calculating checksum accurately

        tcp_len = len(self.data) + (self.offset * 4)

        pseudo_header = struct.pack('!4s4sBBH', socket.inet_aton(self.client_ip), socket.inet_aton(self.server_ip),
                                    0, socket.IPPROTO_TCP, tcp_len)

        final_header = pseudo_header + tcp_header_without_checksum + self.data

        self.checksum = calculate_checksum(final_header)
        # print(self.checksum)

        # tcp header with checksum
        tcp_with_checksum = struct.pack('!HHLLBBH', self.client_port, self.server_port, self.seq_num,
                                        self.ack_num, tcp_offset_res, tcp_flags,
                                        self.wnd_size) + struct.pack('H', self.checksum) \
                            + struct.pack('!H', self.urg_ptr)

        # final tcp packet --- header with checksum + data [[[[[[ TCP HEADER + DATA ]]]]]]]]]]]] = TCP SEGMENT
        tcp_segment = tcp_with_checksum + self.data
        # print(tcp_segment)

        return tcp_segment

    def unpack_received_packet(self, recv_segment, client, server):
        # print("UNPACKING TCP%%%%%%%%%%%%%%%%%%%%%")
        # print(recv_segment)
        tcp_header = struct.unpack('!HHLLBBH', recv_segment[0:16])
        # print("LMAOOOOOO")
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
        self.data = recv_segment[20:]  ## changed the data segment
        # ("LMAOOOOOO")

        # flags in segment
        self.fin = flags & 0x01
        self.syn = (flags & 0x02) >> 1
        self.rst = (flags & 0x04) >> 2
        self.psh = (flags & 0x08) >> 3
        self.ack = (flags & 0x10) >> 4
        self.urg = (flags & 0x20) >> 5

        # pseudo header fields from IP header -- should have source IP, Destination IP, Protocol field
        # TCP length, TCP header ===== needed for calculating checksum accurately
        tcp_len = len(self.data) + (self.offset * 4)

        pseudo_header = struct.pack('!4s4sBBH',
                                    socket.inet_aton(self.client_ip),
                                    socket.inet_aton(self.server_ip),
                                    0, socket.IPPROTO_TCP, tcp_len)

        to_check = pseudo_header + recv_segment
        # print("********")
        if calculate_checksum(to_check) != 0:
            # print("Error in Checksum")
            pass
            # raise error
        else:
            # print("no error in unpacking")
            return to_check

    # # --------------  CREATE METHOD TO SET FIELDS FOR THE TCP PACKET TO SEND

