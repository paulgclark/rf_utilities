import zmq
import array
import time
import struct
import numpy as np
import pmt
import sys

class zmq_pull_socket():
    def __init__(self, tcp_str, verbose=0):
        self.context = zmq.Context()
        self.receiver = self.context.socket(zmq.PULL)
        self.receiver.connect(tcp_str)


    def poll(self, type_str='f', verbose=0):
        raw_data = self.receiver.recv()
        a = array.array(type_str, raw_data)
        return a
    
    def poll_message(self):
        msg = self.receiver.recv()
        # this is a binary string, convert it to a list of ints
        byte_list = []
        for byte in msg:
            byte_list.append(ord(byte))
        return byte_list

    # incomplete attempt to optimize data flow by
    # sending bytes instead of floats; flowgraph
    # changes needed to support this, as well
    # as all downstream code reworked to use
    # bytes
    def poll_short(self, type_str='h', verbose=0):
        raw_data = self.receiver.recv()
        a = array.array(type_str, raw_data)
        npa_s = np.asarray(a)
        npa_f = npa_s.astype(float)
        npa_f *= (1.0/10000.0)

        #fmt = "<%dI" % (len(raw_data) //4)
        #a = list(struct.unpack(fmt, raw_data))
        return list(npa_f)
