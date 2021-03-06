[![Build Status](https://travis-ci.org/mike01/pypacker.svg?branch=master)](https://travis-ci.org/mike01/pypacker)
[![Code Health](https://landscape.io/github/mike01/pypacker/master/landscape.svg?style=flat)](https://landscape.io/github/mike01/pypacker/master)
[![version](http://img.shields.io/pypi/v/pypacker.svg)](https://pypi.python.org/pypi/pypacker)
[![supported-versions](https://img.shields.io/pypi/pyversions/pypacker.svg)](https://pypi.python.org/pypi/pypacker)
[![supported-implementations](https://img.shields.io/pypi/implementation/pypacker.svg)](https://pypi.python.org/pypi/pypacker)

### General information
This is Pypacker: The fastest and simplest packet manipulation lib for Python.
It lets you create packets manually by defining every aspect of all header data,
dissect packets by parsing raw packet bytes, sending/receiving packets on different layers and intercepting packets.

#### What you can do with Pypacker
Create Packets giving specific values or take the defaults:

```python
from pypacker.layer3.ip import IP
from pypacker.layer3.icmp import ICMP

ip = IP(src_s="127.0.0.1", dst_s="192.168.0.1", p=1) +\
	ICMP(type=8) +\
	ICMP.Echo(id=123, seq=1, body_bytes=b"foobar")
```

Read packets from file (pcap/tcpdump format) and analyze all aspects of it:

```python
from pypacker import ppcap
from pypacker.layer12 import ethernet
from pypacker.layer3 import ip
from pypacker.layer4 import tcp

pcap = ppcap.Reader(filename="packets_ether.pcap")

for ts, buf in pcap:
	eth = ethernet.Ethernet(buf)

	if eth[tcp.TCP] is not None:
		print("%d: %s:%s -> %s:%s" % (ts, eth[ip.IP].src_s, eth[tcp.TCP].sport,
			eth[ip.IP].dst_s, eth[tcp.TCP].dport))
```

Intercept (and modificate) Packets eg for MITM:

```python
# Add iptables rule:
# iptables -I INPUT 1 -p icmp -j NFQUEUE --queue-balance 0:2
import time

from pypacker import interceptor
from pypacker.layer3 import ip, icmp

# ICMP Echo request intercepting
def verdict_cb(ll_data, ll_proto_id, data, ctx):
	ip1 = ip.IP(data)
	icmp1 = ip1[icmp.ICMP]

	if icmp1 is None or icmp1.type != icmp.ICMP_TYPE_ECHO_REQ:
		return data, interceptor.NF_ACCEPT

	echo1 = icmp1[icmp.ICMP.Echo]

	if echo1 is None:
		return data, interceptor.NF_ACCEPT

	pp_bts = b"PYPACKER"
	print("changing ICMP echo request packet")
	echo1.body_bytes = echo1.body_bytes[:-len(pp_bts)] + pp_bts
	return ip1.bin(), interceptor.NF_ACCEPT

ictor = interceptor.Interceptor()
ictor.start(verdict_cb, queue_ids=[0, 1, 2])
time.sleep(999)
ictor.stop()
```

Send and receive packets:

```python
# send/receive raw bytes
from pypacker import psocket
from pypacker.layer12 import ethernet
from pypacker.layer3 import ip

psock = psocket.SocketHndl(mode=psocket.SocketHndl.MODE_LAYER_2, timeout=10)

for raw_bytes in psock:
	eth = ethernet.Ethernet(raw_bytes)
	print("Got packet: %r" % eth)
	eth.reverse_address()
	eth.ip.reverse_address()
	psock.send(eth.bin())
	# stop on first packet
	break

psock.close()
```

```python
# send/receive using filter
from pypacker import psocket
from pypacker.layer3 import ip
from pypacker.layer4 import tcp

packet_ip = ip.IP(src_s="127.0.0.1", dst_s="127.0.0.1") + tcp.TCP(dport=80)
psock = psocket.SocketHndl(mode=psocket.SocketHndl.MODE_LAYER_3, timeout=10)

def filter_pkt(pkt):
	return pkt.ip.tcp.sport == 80

psock.send(packet_ip.bin(), dst=packet_ip.dst_s)
pkts = psock.recvp(filter_match_recv=filter_pkt)

for pkt in pkts:
	print("got answer: %r" % pkt)

psock.close()

```

```python
# Send/receive based on source/destination data
from pypacker import psocket
from pypacker.layer3 import ip
from pypacker.layer4 import tcp

packet_ip = ip.IP(src_s="127.0.0.1", dst_s="127.0.0.1") + tcp.TCP(dport=80)
psock = psocket.SocketHndl(mode=psocket.SocketHndl.MODE_LAYER_3, timeout=10)
packets = psock.sr(packet_ip, max_packets_recv=1)

for p in packets:
    print("got layer 3 packet: %s" % p)
psock.close()
```

##### Key features

- Create network packets on different OSI layers using keywords like MyPacket(value=123) or raw bytes MyPacket(b"value")
- Concatination of layers via "+" like packet = layer1 + layer2
- Fast access to layers via packet[tcp.TCP] or packet.sublayerXYZ.tcp notation
- Readable packet structure using print(packet) or similar statements
- Read/store packets via Pcap/tcpdump file reader/writer
- Live packet reading/writing using a wrapped socket API
- Auto Checksum calculation capabilities
- Intercept Packets using NFQUEUE targets
- Easily Create new protocols (see FAQ below and HACKING file)


### Prerequisites
- Python 3.x (CPython, Pypy, Jython or whatever Interpreter)
- Optional (for interceptor):
  - CPython
  - Unix like system
  - iptables
  - NFQUEUE target support in kernel for packet intercepting

### Installation
Some examples:
- python setup.py install
- pip install pypacker

### Usage examples
See examples/ and tests/test_pypacker.py.

### Testing
Tests are executed as follows:

1) Optional: Add Pypacker directory to the PYTHONPATH. This is only needed if tests are executed without installing Pypacker

- cd pypacker
- export PYTHONPATH=$PYTHONPATH:$(pwd)

2) execute tests

- python tests/test_pypacker.py

### FAQ

**Q**:	Where should I start learn to use Pypacker?

**A**:	If you allready know Scapy starting by reading the examples should be OK. Otherwise there
	is a general introduction to pypacker included at the doc's which shows the usage and concepts
	of pypacker.

**Q**:	How fast is pypacker?

**A**:	For detailed results see performance tests in test directory. As a rule of thumb compared
	to scapy packet parsing from raw bytes is more than 50 times faster.

**Q**:	Is there any documentation?

**A**:	Pypacker is based on code of dpkt, which in turn didn't have any official and very little
	internal code documentation. This made understanding of the internal behaviour tricky.
	After all the code documentation was pretty much extended for Pypacker. Documentation can
	be found in these directories and files:
- examples/ (many examples showing the usage of Pypacker)
- doc (auto generated documentations showing general header field definitions + general intro into pypacker)
- pypacker.py (general Packet structure)

Protocols itself (see layerXYZ) generally don't have much documentation because those are documented
by their respective RFCs/official standards.

**Q**:	Which protocols are supported?

**A**:	Currently minimum supported protocols are:
	Ethernet, Radiotap, IEEE80211, ARP, DNS, STP, PPP, OSPF, VRRP, DTP, IP, ICMP, PIM, IGMP, IPX,
	TCP, UDP, SCTP, HTTP, NTP, RTP, DHCP, RIP, SIP, Telnet, HSRP, Diameter, SSL, TPKT, Pmap, Radius, BGP

**Q**:	How are protocols added?

**A**:  Short answer: Extend Packet class and add the class variable `__hdr__` to define header fields.
        Long answer: See examples/examples_new_protocol.py for a complete example.

**Q**: How can I contribute to this project?

**A**: Please use the Github bug-tracker for bugs/feature request. Pease read the bugtracker for
     already known bugs before filing a new one. Patches can be send via pull request.

**Q**:	Under which license Pypacker is issued?

**A**:	It's the BSD License. See LICENCE and http://opensource.org/licenses/bsd-license.php
	for more information. I'm willing to change to GPLv2 but this collides with the previous
	license of dpkt (which is BSD).

**Q**:	Are there any plans to support [protocol xyz]?

**A**:	Support for particular protocols is added to Pypacker as a result of people contributing
	that support - no formal plans for adding support for particular protocols in particular
	future releases exist. 

**Q**:	There is problem xyz with Pypacker using Windows 3.11/XP/7/8/mobile etc. Can you fix that?

**A**:	The basic features should work with any OS. Optional ones may make trouble (eg interceptor)
        and there will be no support for that. Why? Because quality matters and I won't give support for
	inferior systems. Think twice before chosing an operating system and deal with the consequences;
	don't blame others for your decision. Alternatively: give me monetary compensation and I'll see
	what I can do (;
