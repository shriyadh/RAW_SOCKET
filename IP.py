import socket
import struct


# from TCP import calculate_checksum

def calculate_checksum(msg):
    s = 0

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

    def __init__(self, src_ip='', dest_ip=''):
        self.client_ip = src_ip
        self.server_ip = dest_ip
        self.recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)

    def receive_message(self, client_address):
        # receive the packet from the raw socket
        received_packet, server_add = self.recv_socket.recvfrom(2048)

        # create ip packet
        ip_packet = IP_Packet()

        # unpack ip_packet and retrieve tcp part
        tcp_seg = ip_packet.unpack_packet(received_packet, self.client_ip)

        return tcp_seg

    def send_message(self, tcp_seg, dest_ip, dest_port):
        # create packet
        ip_packet = IP_Packet()

        # add tcp seg
        ip_packet.data = tcp_seg
        ip_packet.client_ip = self.client_ip
        ip_packet.server_ip = self.server_ip
        print("here",self.client_ip)

        # pack the packet
        packet_to_send = ip_packet.pack_ip_packet()

        # send to server
        self.send_socket.sendto(packet_to_send, (dest_ip, dest_port))


class IP_Packet:

    def __init__(self, src_ip='', dest_ip='', tcp_seg=b''):
        self.version = 4
        self.ihl = 5
        self.type_service = 0
        self.id = 0
        self.offset = 0
        self.time_to_live = 0
        self.protocol = socket.IPPROTO_TCP
        self.checksum = 0
        self.client_ip = src_ip
        self.server_ip = dest_ip
        self.data = tcp_seg
        self.length = 20 + len(self.data)  # header is 20 bytes and add on tcp seg
        self.ip_ihl_ver = (self.version << 4) + self.ihl

    def pack_ip_packet(self):
        print(self.client_ip)
        print("server:",self.server_ip)
        ip_header_wo_check = struct.pack('!BBHHHBBH4s4s', self.ip_ihl_ver, self.type_service, self.length, self.id,
                                         self.offset, self.time_to_live, self.protocol, self.checksum,
                                         socket.inet_aton(self.client_ip), socket.inet_aton(self.server_ip))
        # calc checksum
        self.checksum = calculate_checksum(ip_header_wo_check)

        # update checksum
        ip_header = struct.pack('!BBHHHBBH4s4s', self.ip_ihl_ver, self.type_service, self.length, self.id,
                                self.offset, self.time_to_live, self.protocol, self.checksum, socket.inet_aton(self.client_ip),
                                socket.inet_aton(self.server_ip))

        # return fully complete packet
        ip_packet = ip_header + self.data

        return ip_packet

    def unpack_packet(self, received_packet, client_address):
        # grab ip header from first bytes of the packet in a tuple
        ip_header = struct.unpack('!BBHHHBBH4s4s', received_packet[:20])

        # ===== parse the fields =====
        self.version = ip_header[0] >> 4  # first byte contains version and ihl
        self.ihl = ip_header[0] & 0xF
        self.type_service = ip_header[1]
        self.length = ip_header[2]
        self.id = ip_header[3]
        self.offset = self.ihl * 4  # extract lower 4 bits of first byte and multiply by 4
        self.time_to_live = ip_header[5]
        self.protocol = ip_header[6]
        self.checksum = ip_header[7]
        self.server_ip = socket.inet_ntoa(ip_header[8])  # src (server in this case) binary -> human readable format
        self.client_ip = socket.inet_ntoa(ip_header[9])  # dst (client, us)
        # tcp header and data is after ip header
        self.data = received_packet[self.offset:]

        # ======= validate checksum ======

        # set checksum to zero
        validate = struct.pack('!BBHHHBBH4s4s', self.ip_ihl_ver, self.type_service, self.length, self.id,
                               self.offset, self.time_to_live, self.protocol, 0, self.client_ip,
                               self.server_ip)

        if calculate_checksum(validate) == self.checksum:  # checksum is valid
            pass
        else:
            return None  # data corrupted

        # dest ip (client in receiving packet) should match this ip
        if self.client_ip != client_address:
            return  # wrong address

        # pass to tcp using offset value
        return self.data
