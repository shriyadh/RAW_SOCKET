import socket
import struct
from random import randint


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


class IP:
    """
    This class implements features of the IP Layer.
    It has two sockets -- one for receiving and one for sending.
    It receives TCP segment from TCP class, adds the IP headers to the TCP Segment (IP DATAGRAM)
    and sends it to the server.
    It receives responses from the server, unpacks the IP Header and passes on the TCP segment to the TCP class.
    """
    def __init__(self, src_ip='', dest_ip='', client_port=''):
        self.client_ip = src_ip
        self.server_ip = dest_ip
        self.client_port = client_port
        self.recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)

    def close_sockets(self):
        """
        Once the data exchange is complete, close both receiving and sending sockets.
        :return: None
        """
        self.recv_socket.close()
        self.send_socket.close()

    def receive_message(self, client_address):
        """
        It receives responses from the server, unpacks the IP Header and passes on the TCP segment to the TCP class.
        :param client_address: Local IP address
        :return: TCP segment
        """

        try:
            while True:
                recv_pack = IP_Packet()
                unpack_this = self.recv_socket.recv(2048)
                recv_pack.unpack_packet(unpack_this)
                if recv_pack.client_ip == self.server_ip and recv_pack.server_ip == self.client_ip and recv_pack.protocol == socket.IPPROTO_TCP:
                    return recv_pack.data
        except:
            print("TIMEOUT")

    def send_message(self, tcp_seg):
        """
         This method receives TCP segment from TCP class, adds the IP headers to the TCP Segment (IP DATAGRAM)
         and sends it to the server.
        :param tcp_seg: TCP header
        :return: sender socket
        """
        # create packet
        ip_packet = IP_Packet()
        # add tcp seg
        ip_packet.data = tcp_seg
        ip_packet.client_ip = self.client_ip
        ip_packet.server_ip = self.server_ip
        # pack the packet
        packet_to_send = ip_packet.pack_ip_packet()
        # send to server
        self.send_socket.sendto(packet_to_send, (self.server_ip, 80))
        return self.send_socket


class IP_Packet:
    """
    This class represents the IP header as we see it in IP datagrams. It contains all the required fields for the
    header and contains methods for packing and unpacking IP headers.
    """
    def __init__(self, src_ip='', dest_ip='', tcp_seg=b''):
        self.version = 4
        self.ihl = 5
        self.type_service = 0
        self.id = randint(1, 65535)
        self.offset = 0
        self.df = 1
        self.mf = 0
        self.time_to_live = 255
        self.protocol = socket.IPPROTO_TCP
        self.checksum = 0
        self.client_ip = src_ip
        self.server_ip = dest_ip
        self.data = tcp_seg
        self.length = 20  # header is 20 bytes and add on tcp seg
        self.ip_ihl_ver = (self.version << 4) + self.ihl

    def pack_ip_packet(self):
        """
        This method creates an IP datagram by adding on IP header fields to the received TCP segment.
        :return: IP Datagram
        """
        self.id = randint(1, 65535)
        self.length = len(self.data) + 20
        ip_header_wo_check = struct.pack('!BBHHHBBH4s4s', self.ip_ihl_ver, self.type_service, self.length, self.id,
                                         (((self.df << 1) + self.mf) << 13) +
                                         self.offset, self.time_to_live, self.protocol, self.checksum,
                                         socket.inet_aton(self.client_ip), socket.inet_aton(self.server_ip))
        # calc checksum
        self.checksum = calculate_checksum(ip_header_wo_check)

        # update checksum
        ip_header = struct.pack('!BBHHHBBH4s4s', self.ip_ihl_ver, self.type_service, self.length, self.id,
                                (((self.df << 1) + self.mf) << 13) +
                                self.offset, self.time_to_live, self.protocol, self.checksum,
                                socket.inet_aton(self.client_ip),
                                socket.inet_aton(self.server_ip))

        # return fully complete packet
        ip_packet = ip_header + self.data

        return ip_packet

    def unpack_packet(self, received_packet, client_address='', server_address=''):
        """
        This method unpacks the received datagram from the server to remove the IP header and pass on the TCP segment
        :param received_packet: data from server
        :param client_address: Local IP address
        :param server_address: Server IP address
        :return: TCP segment
        """

        # grab ip header from first bytes of the packet in a tuple
        ip_header = struct.unpack('!BBHHHBB', received_packet[:10])
        # ===== parse the fields =====
        self.version = (ip_header[0] & 0xf0) >> 4  # first byte contains version and ihl
        self.ihl = ip_header[0] & 0x0F
        self.type_service = ip_header[1]
        self.length = ip_header[2]
        self.id = ip_header[3]
        offset = ip_header[4]  # extract lower 4 bits of first byte and multiply by 4
        self.time_to_live = ip_header[5]
        self.protocol = ip_header[6]
        self.df = (offset & 0x40) >> 14
        self.mf = (offset & 0x20) >> 13
        self.offset = self.offset & 0x1f
        self.checksum = struct.unpack('H', received_packet[10:12])
        [src, dest] = struct.unpack('!4s4s', received_packet[12:20])
        self.server_ip = socket.inet_ntoa(dest)  # src (server in this case) binary -> human readable format
        self.client_ip = socket.inet_ntoa(src)  # dst (client, us)

        # tcp header and data is after ip header
        self.data = received_packet[self.ihl * 4: self.length]
        # ======= validate checksum ======
        header = received_packet[:self.ihl * 4]
        if calculate_checksum(header) != 0:
            print(calculate_checksum(header))
            print("ERROR IN IP CHECKSUM")
        else:
            #print(calculate_checksum(header))
            print("NO IP CHECKSUM ERROR")

        # pass to tcp using offset value
        return self.data