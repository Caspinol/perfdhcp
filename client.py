import thread, time, threading
import Queue
from random import Random
from pydhcplib.type_hw_addr import hwmac
from pydhcplib.type_ipv4 import ipv4
from pydhcplib.type_strlist import strlist
from pydhcplib.dhcp_packet import DhcpPacket
from pydhcplib.dhcp_network import DhcpClient

# Enum for all DHCP packet types.
DHCPDiscover, DHCPOffer, DHCPRequest, DHCPDecline, DHCPAck, \
    DHCPNack, DHCPRelease, DHCPInform = range(1,9)

# Initilize the random object.
r = Random()
r.seed()
event = threading.Event()

def generate_mac():
    return [r.randint(0,255) for i in xrange(6)]


class Client(DhcpClient):
    def __init__(self, serverip):
        DhcpClient.__init__(self)

        self.serverip = serverip
        self.s_port = 67
        self.mac = None
        self.DHCP_SRV_IP = None
        self.running = True
        self.summary = {
            'discover': 0,
            'offer': 0,
            'request': 0,
            'ack': 0,
            'nack': 0,
            'release': 0,
            'timeout': 0
        }
                      
        t = threading.Thread(target=self._client_listen)
        t.daemon = True
        t.start()

    def _client_listen(self):
        print "Client ready to roll..."
        self.BindToAddress()
        while True:
            self.GetNextDhcpPacket()

    def HandleDhcpOffer(self, packet):
        event.set()
        self.summary['offer'] += 1
        yiaddr = packet.GetOption('yiaddr')
        # Get MAC addres but without the padding.
        mac = packet.GetOption('chaddr')[:6]
        srv_iden = packet.GetOption('server_identifier')
        xid = packet.GetOption('xid')
        print "Got DHCPOffer with IP: %s" % yiaddr
        self._send_request(mac, yiaddr, srv_iden, xid)
        
    def HandleDhcpAck(self, packet):
        event.set()
        self.summary['ack'] += 1
        ip = ipv4(packet.GetOption('yiaddr'))
        mac = packet.GetOption('chaddr')[:6]
        # Need to capture it to send a release.
        self.DHCP_SRV_IP = packet.GetOption('siaddr')
        print "Got DHCPAck, sending release"
        self._send_release(mac, ip)

    def HandleDhcpNack(self, packet):
        self.summary['nack'] += 1
        event.set()
        print packet.str()

    def _wait_for_response(self):
        wait = 5
        sleep = 0.5
        i = 0
        while i <= int(wait/sleep) and not event.isSet():
            event.wait(wait)
            i += 1
        # Get ready for next one.
        self.summary['timeout'] += 1
        event.clear()
    
    def _generate_xid(self):
        return [r.randint(0,255) for i in xrange(4)]
    
    def create_packet(self, mt, chaddr, ciaddr, yiaddr, xid, server):
        req = DhcpPacket()
        req.SetOption('op', [1])
        req.SetOption('htype',[1])
        req.SetOption('hlen',[6])
        req.SetOption('hops', [0])
        req.SetOption('xid', xid)
        req.SetOption('giaddr', ipv4().list())
        req.SetOption('chaddr', hwmac(chaddr).list() + [0] * 10)
        req.SetOption('ciaddr', ipv4(ciaddr).list())
            
        if mt == DHCPRequest:
            req.SetOption('yiaddr', ipv4(yiaddr).list())
            req.SetOption('request_ip_address', ipv4(yiaddr).list())

        if mt == DHCPRelease:
            req.SetOption('siaddr', server)
            req.SetOption('server_identifier', ipv4(server).list())
            
        if server == '255.255.255.255':
            req.SetOption('flags', [128, 0])
            
        req.SetOption('dhcp_message_type',[mt])
        req.SetOption("domain_name", strlist("catdamnit.com").list())
        return req

    def _send_discover(self, mac, seconds):
        print "Creating DHCPDiscover"
        pkt = self.create_packet(DHCPDiscover, mac,
                                 '0.0.0.0', '0.0.0.0', self._generate_xid(), self.serverip)
        pkt.SetOption('secs', [0, seconds])
        self.summary['discover'] += 1
        print "Sending DHCPDiscover"
        self.SendDhcpPacketTo(pkt, self.serverip, self.s_port)

    def _send_request(self, mac, offered_ip, srv_iden, xid):
        print "Creating DHCPRequest"
        pkt = self.create_packet(DHCPRequest, mac,
                                 '0.0.0.0', offered_ip, xid, self.serverip)
        pkt.SetOption('server_identifier', srv_iden)
        print "Sending DHCPRequest:"
        self.summary['request'] += 1
        self.SendDhcpPacketTo(pkt, self.serverip, self.s_port)
        self._wait_for_response()

    def _send_release(self, mac, ip):
        print "Creating DHCPRelease"
        # Different xid should be generated for DHCPRelease.
        pkt = self.create_packet(DHCPRelease, mac, ip.str(), '0.0.0.0',
                                 self._generate_xid(), self.DHCP_SRV_IP)
        self.summary['release'] += 1
        print "Sending DHCPRelease:"
        self.SendDhcpPacketTo(pkt, ipv4(self.DHCP_SRV_IP).str(), self.s_port)

    def show_summary(self):
        return self.summary

    def kill_test(self):
        self.running = False
        
    def test_dhcp(self, q):

        while self.running:
            try:
                mac = q.get(True, 2)
            except Queue.Empty:
                print "Empty queue"
                time.sleep(1)
            else:
                self._send_discover(mac, 0)
                self._wait_for_response()
                q.task_done()
            

