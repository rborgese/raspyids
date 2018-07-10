from scapy.all import *
import logging
logger = logging.getLogger('app.'+__name__)

"""
=== Run information ===

Scheme:weka.classifiers.trees.J48 -C 0.25 -M 2
Relation:     outReduced-weka.filters.unsupervised.attribute.Remove-R14,16-18,22-23,28,30-32,39-41,43-44,46-48,66,69-72-weka.filters.unsupervised.attribute.Remove-R20-weka.filters.unsupervised.attribute.Remove-R27-weka.filters.unsupervised.attribute.Remove-R48-50-weka.filters.unsupervised.attribute.Remove-R8,12
Instances:    185679
Attributes:   50
              eth.eth.type
              ip.ip.proto
              ip.ip.flags
              ip.ip.flags_tree.ip.flags.df
              tcp.tcp.window_size_value
              ip.ip.len
              tcp.tcp.hdr_len
              tcp.tcp.seq
              tcp.tcp.window_size
              tcp.tcp.stream
              tcp.tcp.flags
              ip.ip.dst
              tcp.tcp.port
              tcp.tcp.dstport
              ip.ip.src
              tcp.tcp.srcport
              ipv6.ipv6.nxt
              tcp.tcp.options_tree.tcp.options.mss_tree.tcp.options.mss_val
              tcp.tcp.ack
              ipv6.ipv6.plen
              tcp.tcp.len
              ip.ip.dsfield
              ip.ip.dsfield_tree.ip.dsfield.dscp
              tcp.tcp.flags_tree.tcp.flags.push
              ipv6.ipv6.dst
              tcp.tcp.flags_tree.tcp.flags.reset
              udp.udp.length
              udp.udp.stream
              udp.udp.srcport
              tcp.tcp.flags_tree.tcp.flags.ack
              udp.udp.dstport
              udp.udp.port
              dns.dns.count.queries
              dns.dns.flags_tree.dns.flags.opcode
              dns.dns.count.add_rr
              dns.dns.count.answers
              dns.dns.count.auth_rr
              dns.dns.flags_tree.dns.flags.truncated
              ipv6.ipv6.hlim
              dns.dns.flags_tree.dns.flags.response
              dns.dns.flags
              tcp.tcp.options
              ipv6.ipv6.flow
              tcp.tcp.flags_tree.tcp.flags.fin
              ip.ip.ttl
              eapol.wlan_rsna_eapol.keydes.nonce
              mqtt.mqtt.msg
              eapol.wlan_rsna_eapol.keydes.mic
              ip.ip.checksum.status
              class
Test mode:evaluate on training data

=== Classifier model (full training set) ===

J48 pruned tree
------------------

eth.eth.type = 0x00000800
|   ip.ip.proto <= 6
|   |   ip.ip.len <= 44
|   |   |   tcp.tcp.seq <= 0: flood_tcp4 (6766.0)
|   |   |   tcp.tcp.seq > 0: normal (28396.0)
|   |   ip.ip.len > 44: normal (121561.0)
|   ip.ip.proto > 6
|   |   ip.ip.flags = 0x00000000: flood_udp4 (10000.0)
|   |   ip.ip.flags = 0x00000002: normal (160.0)
eth.eth.type = 0x000086dd
|   ipv6.ipv6.plen <= 325
|   |   ipv6.ipv6.plen <= 24
|   |   |   ipv6.ipv6.nxt <= 17: flood_tcp6 (8120.0)
|   |   |   ipv6.ipv6.nxt > 17: normal (35.0)
|   |   ipv6.ipv6.plen > 24: normal (547.0)
|   ipv6.ipv6.plen > 325: flood_udp6 (10000.0)
eth.eth.type = 0x00000806: normal (88.0)
eth.eth.type = 0x0000888e: normal (6.0)

Number of Leaves  : 11

Size of the tree : 19


Time taken to build model: 17.9 seconds

=== Evaluation on training set ===
=== Summary ===

Correctly Classified Instances      185679              100      %
Incorrectly Classified Instances         0                0      %
Kappa statistic                          1
Mean absolute error                      0
Root mean squared error                  0
Relative absolute error                  0      %
Root relative squared error              0      %
Total Number of Instances           185679

=== Detailed Accuracy By Class ===

               TP Rate   FP Rate   Precision   Recall  F-Measure   ROC Area  Class
                 1         0          1         1         1          1        flood_tcp4
                 1         0          1         1         1          1        flood_tcp6
                 1         0          1         1         1          1        flood_udp4
                 1         0          1         1         1          1        flood_udp6
                 1         0          1         1         1          1        normal
Weighted Avg.    1         0          1         1         1          1

=== Confusion Matrix ===

      a      b      c      d      e   <-- classified as
   6766      0      0      0      0 |      a = flood_tcp4
      0   8120      0      0      0 |      b = flood_tcp6
      0      0  10000      0      0 |      c = flood_udp4
      0      0      0  10000      0 |      d = flood_udp6
      0      0      0      0 150793 |      e = normal


"""

class PacketType(object):
    def __init__(self,n):
        self._name = n
        self._count = 0
    def add(self):
        self._count += 1
        return self
    def count(self):
        return self._count
    def __pos__(self):
        return self.add()
    def __str__(self):
        return self._name
    def __int__(self):
        return self._count

PACKET_LIST = {
  'NORMAL'   :PacketType('NORMAL'),
  'MALICIOUS':{
    'TCP4'      :PacketType('TCP4 FLOOD'),
    'TCP6'      :PacketType('TCP6 FLOOD'),
    'UDP4'      :PacketType('UDP4 FLOOD'),
    'UDP6'      :PacketType('UDP6 FLOOD'),
    'UNDETECTED':PacketType('UNDETECTED')
  }
}

def detect(pkt, blocker=None, unblocker=None, output=None):
    global PACKET_LIST
    detected = PACKET_LIST['MALICIOUS']['UNDETECTED']

    if getattr(pkt[Ether], 'type') == int(b'0x00000800',16):
        if getattr(pkt[IP], 'proto') <= 6:
            if getattr(pkt[IP], 'len') <= 44:
                if getattr(pkt[TCP], 'seq') <= 0:
                    detected = +PACKET_LIST['MALICIOUS']['TCP4']
                    logger.warning(detected)
                elif getattr(pkt[TCP], 'seq') > 0:
                    detected = +PACKET_LIST['NORMAL']
            elif getattr(pkt[IP], 'len') > 44:
                detected = +PACKET_LIST['NORMAL']
        elif getattr(pkt[IP], 'proto') > 6:
            if getattr(pkt[IP], 'flags') == int('0x00000000',16):
                detected = +PACKET_LIST['MALICIOUS']['UDP4']
                logger.warning(detected)
            elif getattr(pkt[IP], 'flags') == int('0x00000002',16):
                detected = +PACKET_LIST['NORMAL']
    elif getattr(pkt[Ether], 'type') == int(b'0x000086dd',16):
        if getattr(pkt[IPv6], 'plen') <= 325:
            if getattr(pkt[IPv6], 'plen') <= 24:
                if getattr(pkt[IPv6], 'nh') <= 17:
                    detected = +PACKET_LIST['MALICIOUS']['TCP6']
                    logger.warning(detected)
                elif getattr(pkt[IPv6], 'nh') > 17:
                    detected = +PACKET_LIST['NORMAL']
            elif getattr(pkt[IPv6], 'plen') > 24:
                detected = +PACKET_LIST['NORMAL']
        elif getattr(pkt[IPv6], 'plen') > 325:
            detected = +PACKET_LIST['MALICIOUS']['UDP6']
            logger.warning(detected)
    elif getattr(pkt[Ether], 'type') == int(b'0x00000806',16):
        detected = +PACKET_LIST['NORMAL']
    elif getattr(pkt[Ether], 'type') == int(b'0x0000888e',16):
        detected = +PACKET_LIST['NORMAL']

    if detected != PACKET_LIST['NORMAL']:
        if detected == PACKET_LIST['MALICIOUS']['UNDETECTED']:
            +PACKET_LIST['MALICIOUS']['UNDETECTED']
            logger.warning(detected)
    return PACKET_LIST
if __name__ == '__main__':
    from scapy.all import *
    sniff(prn=detect)
