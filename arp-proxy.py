#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from logging.handlers import TimedRotatingFileHandler

logger = logging.getLogger(__name__)
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

from scapy.all import sniff, ls, Ether, ARP, get_if_hwaddr, sendp
from ipaddress import ip_address, ip_network, IPv4Address, IPv4Network
import sys
import os
import argparse


class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """

    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        pass


def logs():
    log_file = str(os.path.dirname(os.path.abspath(__file__))) + '/arp-proxy.log'
    handler = TimedRotatingFileHandler(log_file, when='midnight', interval=1, backupCount=7)
    logging.basicConfig(format=u'%(asctime)s %(levelname)s %(name)s: %(message)s',
                        level=logging.INFO, handlers=[handler])

    stdout_logger = logging.getLogger('STDOUT')
    sl = StreamToLogger(stdout_logger, logging.INFO)
    sys.stdout = sl

    stderr_logger = logging.getLogger('STDERR')
    sl = StreamToLogger(stderr_logger, logging.ERROR)
    sys.stderr = sl


def cli_args():
    global iface, gw_mac
    parser = argparse.ArgumentParser(add_help=True, description='arp-proxy-scapy for overlapped networks')
    parser.add_argument('iface', action="store", type=str, help='interface name (eth0, enp0s0 etc)')
    parser.add_argument('gwmac', action="store", type=str, help='gateway MAC')
    args = parser.parse_args()
    iface = args.iface
    gw_mac = args.gwmac


def get_iface_mac_address():
    global iface_mac
    mac = get_if_hwaddr(iface)
    if mac != "00:00:00:00:00:00":
        iface_mac = mac


# global variables for func arp_proxy()
iface = ''
iface_mac = ''
gw_mac = ''

# table: net | subnet
nets_overlap = (
    (ip_network('10.0.0.0/8'), ip_network('10.0.1.0/24')),
    (ip_network('10.0.0.0/8'), ip_network('10.0.2.0/24'))
)


def arp_proxy(pkt):
    for net in nets_overlap:
        if ip_address(pkt.psrc) in net[0] and ip_address(pkt.pdst) in net[1] and \
                        pkt.hwsrc != gw_mac and pkt.hwsrc != iface_mac and \
                        pkt.pdst != str(net[1].network_address) and \
                        pkt.pdst != str(net[1].broadcast_address):
            # create arp reply paket
            arp_reply = Ether(src=iface_mac, dst=pkt.hwsrc) / \
                        ARP(op=2, hwsrc=gw_mac, psrc=pkt.pdst, hwdst=pkt.hwsrc, pdst=pkt.psrc)

            sendp(arp_reply, iface=iface, verbose=0)
            print('-----------------------------------\n')
            print('IN: ARP request \n')
            print('-----------------------------------\n')
            pkt.show()
            print('-----------------------------------\n')
            print('-----------------------------------\n')
            print('OUT: ARP reply \n')
            print('-----------------------------------\n')
            arp_reply.show()
            print('-----------------------------------\n')


def main():
    cli_args()
    get_iface_mac_address()
    logs()
    # sniff all arp requests with opcode = 1 (who-has)
    sniff(iface=iface, prn=arp_proxy, filter='arp[6:2]=1', store=0)


if __name__ == '__main__':
    main()
