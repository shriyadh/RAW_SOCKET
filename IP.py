
import socket
class IP:




    def __init__(self, src_ip='', dest_ip=''):
        self.client_ip = src_ip
        self.server_ip = dest_ip



class IP_Packet:

    def __init__(self, src_ip='', dest_ip='', tcp_seg=''):
        self.version = 4
        self.ihl = 5
        self.type_service = 0
        self.length = 0
        self.id = 0
        self.offset = 0
        self.time_to_live = 0
        self.protocol = socket.IPPROTO_TCP
        self.chechsum = 0
        self.client_ip = src_ip
        self.server_ip = dest_ip
        self.data = tcp_seg

        def create_IP_packet(self):



            pass
