# $Id: dtp.py 23 2006-11-08 15:45:33Z dugsong $

"""Dynamic Trunking Protocol."""

import pypacker as pypacker
import struct

class DTP(pypacker.Packet):
	__hdr__ = (
		("v", "B", 0),
		) # rest is TLVs

	def unpack(self, buf):
		pypacker.Packet.unpack(self, buf)
		buf = self.data
		tvs = []
		while buf:
			t, l = struct.unpack('>HH', buf[:4])
			v, buf = buf[4:4+l], buf[4+l:]
			tvs.append((t, v))
		self.data = tvs

TRUNK_NAME = 0x01
MAC_ADDR = 0x04
