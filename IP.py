import socket
import struct
from random import randint

# from TCP import calculate_checksum

def calculate_checksum(msg):
    s = 0

    # if len of msg is odd
    if len(msg) % 2 != 0:
        msg += struct.pack('B', 0)

    # loop taking 2 characters at a time
    for i in range(0, len(msg), 2):
        w = msg[i] + msg[i + 1] << 8
        s = s + w

    s = (s >> 16) + (s & 0xffff)
    s = s + (s >> 16)

    # complement and mask to 4 byte short
    s = ~s & 0xffff

    return s


class IP:

    def __init__(self, src_ip='', dest_ip='', client_port=''):
        self.client_ip = src_ip
        self.server_ip = dest_ip
        self.client_port = client_port
        self.recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)

    def bind_socket(self):
        self.recv_socket.bind((self.client_ip, 0))
        self.client_port = self.recv_socket.getsockname()[1]

        return self.client_port
    def receive_message(self, client_address):
        # print("RECEIVING...")
        # receive the packet from the raw socket
        #socket.socket(('localhost',0))

        try:

            while True:
                recv_pack = IP_Packet()
                print("in here ")
                unpack_this = self.recv_socket.recv(2048)
                print("RECEIVED: ", unpack_this)

                recv_pack.unpack_packet(unpack_this)
                print("CLIENT: ", recv_pack.client_ip)
                print("SERVER: ", recv_pack.server_ip)

                # unpack ip_packet and retrieve tcp part
                if recv_pack.client_ip == self.server_ip and recv_pack.server_ip == self.client_ip and recv_pack.protocol == socket.IPPROTO_TCP:
                    print("true")
                    return recv_pack
        except:
            print("TIMEOUT")

    def send_message(self, tcp_seg):

        # create packet
        ip_packet = IP_Packet()

        # add tcp seg
        ip_packet.data = tcp_seg

        ip_packet.client_ip = self.client_ip
        print(ip_packet.client_ip , "&&&&&&&&&&&&&&&&&&&&&&&&")
        ip_packet.server_ip = self.server_ip
        print("CLIENT", self.client_ip)
        print("SERVER", self.server_ip)

        # pack the packet
        packet_to_send = ip_packet.pack_ip_packet()
        print(packet_to_send)


        # send to server
        # self.send_socket.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        self.send_socket.sendto(packet_to_send, (self.server_ip, 80))

        print("******sent packet******")


class IP_Packet:

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

        self.id = randint(1, 65535)
        self.length = len(self.data) + 20
        print("server:", self.server_ip)
        ip_header_wo_check = struct.pack('!BBHHHBBH4s4s', self.ip_ihl_ver, self.type_service, self.length, self.id,
                                         (((self.df << 1) +self.mf) << 13) +
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

        print("SEND HEADER", struct.unpack('!BBHHHBBH4s4s', ip_header))

        print(ip_header)
        # return fully complete packet
        ip_packet = ip_header + self.data
        print("Length", self.length)
        print("IP PACK ", ip_packet)

        return ip_packet

    def unpack_packet(self, received_packet, client_address='', server_address=''):
        print("UNPACKING")

        # grab ip header from first bytes of the packet in a tuple
        ip_header = struct.unpack('!BBHHHBB', received_packet[:10])
        print("header", ip_header)
        # ===== parse the fields =====
        self.version = (ip_header[0] & 0xf0) >> 4  # first byte contains version and ihl
        print(self.version)
        self.ihl = ip_header[0] & 0x0F
        print(self.ihl)
        self.type_service = ip_header[1]
        print(self.type_service)
        self.length = ip_header[2]
        print(self.length)
        self.id = ip_header[3]
        print(self.id)
        offset = ip_header[4] # extract lower 4 bits of first byte and multiply by 4
        print(self.offset)
        self.time_to_live = ip_header[5]
        self.protocol = ip_header[6]
        self.df = (offset & 0x40) >> 14
        self.mf = (offset & 0x20) >> 13
        self.offset = self.offset & 0x1f
        print(self.offset)
        self.checksum = struct.unpack('H', received_packet[10:12])
        print(self.checksum)
        [src, dest] = struct.unpack('!4s4s', received_packet[12:20])
        self.server_ip = socket.inet_ntoa(src)  # src (server in this case) binary -> human readable format
        self.client_ip = socket.inet_ntoa(dest)  # dst (client, us)
        print("CLIENT***",self.client_ip)
        print("SERVER**",self.server_ip)
        # tcp header and data is after ip header
        self.data = received_packet[self.ihl * 4: self.length]
        print("DATAT" ,self.data)
        # ======= validate checksum ======
        header = received_packet[:self.ihl *4]
        print("hello")
        print(calculate_checksum(header))
       # if calculate_checksum(header) != 0:
           # print("error")

        print("end")

        # ====== validate correct addresses and protocol =======
        if self.client_ip == client_address:
            # if self.server_ip == server_address:
            if self.protocol == 6:
                flag = True  # wrong address'

        print("end of unpacking ip")

        # pass to tcp using offset value
        return self.data, flag
