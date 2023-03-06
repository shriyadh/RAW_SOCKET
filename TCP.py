import socket
import struct
from random import randint

from IP import IP


def calculate_checksum(msg=b''):
    """
    :param msg: Takes in the message data
    :return: checksum
    """
    s = 0


    # if len of msg is odd
    if len(msg) % 2 != 0:
        msg += struct.pack('B', 0)

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
        self.client_ip = ''
        self.client_port = 0
        self.server_ip = ''
        self.server_port = 0
        self.sq_num = 0
        self.ack_num = 0
        self.ip_socket = IP()
        self.cwnd = 1 #max of 1000 ; set back to 1 if packet dropped

    def establish_handshake(self, server_ip, server_port):
        print("here")

        # server IP address # DNS === get Server IP Address
        self.server_ip = socket.gethostbyname(server_ip)
        # server port is 80 (web)
        self.server_port = server_port
        # get local ip address
        sock = socket.socket()
        try:
            sock.connect(("www.google.com", 80))
            ip, port = sock.getsockname()

        except Exception as err:
            raise err
        finally:
            sock.close()

        self.client_ip = ip
        # pick up any random port number which is not reserved
        self.client_port = randint(1024, 65535)

        self.ip_socket.client_ip = self.client_ip
        self.ip_socket.server_ip = self.server_ip

        # THREE WAY HANDSHAKE ------ set SEQ num (random) and ACK = 0
        self.sq_num = randint(0, 100000)
        self.ack_num = 0
        # reset packet parameters
        tcp_packet = self.get_TCP_segment()
        # send the first SYN to do the three-way handshake
        tcp_packet.syn = 1
        # pack the TCP packet
        tcp_seg = tcp_packet.pack_TCP_packet()
        print(tcp_seg)
        # pack tcp_seg into IP
        # -----------------------  Call ip function for building IP DATAGRAM
        self.ip_socket.send_message(tcp_seg) # NEED MARIAH'S CODE FOR THIS

        #  NEXT --- receive SYN ACK ------------------- HOW ARE WE HANDLING CONGESTION WINDOW??? WHAT CHECKS DO WE NEED?

        # receive TCP SEG FROM IP
        packet_recv = self.ip_socket.receive_message() # NEED MARIAH"S CODE FOR THIS
        unpack_recv = TCPPacket()
        # unpack packet
        unpack_recv.unpack_received_packet(packet_recv)

        # see if packet is correct
        if unpack_recv.ack_num == self.sq_num + 1 and packet_recv.syn == 1 and packet_recv.ack == 1:
            pass





        # SEND ACK
        tcp_packet = self.get_TCP_segment()
        tcp_packet.ack = 1
        tcp_seg = tcp_packet.pack_TCP_packet()
        self.ip_socket.send_message(tcp_seg)  # NEED MARIAH'S CODE FOR THIS

        ################ THREE WAY HANDSHAKE ESTABLISHED #################

    def get_TCP_segment(self):
        tcp_pack = TCPPacket()
        tcp_pack.server_ip = self.server_ip
        tcp_pack.client_ip = self.client_ip
        tcp_pack.client_port = self.client_port
        tcp_pack.server_port = self.server_port
        tcp_pack.seq_num = self.sq_num
        tcp_pack.ack_num = self.ack_num
        return tcp_pack


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
        print(self.client_port, self.server_port)
        tcp_offset_res = (self.offset << 4) + 0
        tcp_flags = self.fin + (self.syn << 1) + (self.rst << 2) + (self.psh << 3) + (self.ack << 4) + (self.urg << 5)

        tcp_header_without_checksum = struct.pack('!HHLLBBHHH', self.client_port, self.server_port, self.seq_num,
                                                  self.ack_num, tcp_offset_res, tcp_flags,
                                                  self.wnd_size,
                                                  self.checksum, self.urg_ptr)

        # pseudo header fields from IP header -- should have source IP, Destination IP, Protocol field
        #  TCP length, TCP header ===== needed for calculating checksum accurately
        tcp_len = len(self.data) + (self.offset * 4)

        pseudo_header = struct.pack('!4s4sBBH', socket.inet_aton(self.client_ip), socket.inet_aton(self.server_ip),
                                    0, socket.IPPROTO_TCP, tcp_len)

        final_header = pseudo_header + tcp_header_without_checksum + self.data

        self.checksum = calculate_checksum(final_header)
        print(self.checksum)

        # tcp header with checksum
        tcp_with_checksum = struct.pack('!HHLLBBHHH', self.client_port, self.server_port, self.seq_num, self.ack_num,
                                        tcp_offset_res, tcp_flags,
                                        self.wnd_size, self.checksum, self.urg_ptr)


        # final tcp packet --- header with checksum + data [[[[[[ TCP HEADER + DATA ]]]]]]]]]]]] = TCP SEGMENT
        tcp_segment = tcp_with_checksum + self.data
        print(tcp_segment)

        return tcp_segment

    def unpack_received_packet(self, recv_segment):

        tcp_header = struct.unpack('!HHLLBBHHH', recv_segment[0:20])
        self.client_port = tcp_header[0]
        self.server_port = tcp_header[1]
        self.seq_num = tcp_header[2]
        self.ack_num = tcp_header[3]
        offset = tcp_header[4]
        self.offset = (offset >> 4) * 4
        flags = tcp_header[5]
        self.wnd_size = tcp_header[6]
        self.checksum = tcp_header[7]
        self.urg = tcp_header[8]
        self.data = recv_segment[self.offset * 4:]

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

        if calculate_checksum(to_check) != 0:
            pass
            # raise error


    # # --------------  CREATE METHOD TO SET FIELDS FOR THE TCP PACKET TO SEND


def main():
    # testing
    test = TCP()
    test.establish_handshake("david.choffnes.com", 80)



if __name__ == "__main__":
    main()
