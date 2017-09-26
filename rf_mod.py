#!/usr/bin/env python
# This module contains the functions used to demodulate raw RF files
# in I-Q format. These functions use the gnuradio libraries to tune
# to the signal, then filter and demodulate it. 
#
# Each class below with the suffix "_flowgraph" contains all of the
# gnuradio blocks required to process the I-Q data to a digital baseband
# waveform. This baseband waveform is output to a file

from gnuradio import analog
from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser
from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import filter
from gnuradio.filter import firdes
from gnuradio import uhd
import pmt
import math
import osmosdr
import time
import sys
import numpy

# global constants
MOD_OOK = 0
MOD_FSK = 1
MOD_DPSK = 2



def modulator(verbose, modulation, center_freq, frequency, samp_rate,
              ook_gain, fsk_deviation_hz, channel_width, 
              basebandFileName, basebandSampleRate, repeat, timeBetweenTx):
    if verbose:
        print "Entering modulator function"

    # select between the major modulation types
    if modulation == MOD_OOK:
        if verbose:
            print "Instantiating OOK flowgraph..."
        flowgraphObject = ook_tx_flowgraph(center_freq = center_freq,
                                           freq = frequency,
                                           samp_rate = samp_rate,
                                           gain = ook_gain,
                                           basebandFileName = basebandFileName,
                                           basebandSampleRate = basebandSampleRate,
                                           repeat = repeat
                                          )
        flowgraphObject.run()
    elif modulation == MOD_FSK:
        if verbose:
            print "Instantiating FSK flowgraph..."
        flowgraphObject = fsk_tx_flowgraph(center_freq = center_freq,
                                           freq = frequency,
                                           samp_rate = samp_rate,
                                           fsk_deviation_hz = fsk_deviation_hz,
                                           basebandFileName = basebandFileName,
                                           basebandSampleRate = basebandSampleRate,
                                           repeat = repeat
                                          )
        flowgraphObject.run()
    elif modulation == MOD_DPSK:
        if verbose:
            print "Instantiating DPSK flowgraph..."
        flowgraphObject = dpsk_tx_flowgraph()
        flowgraphObject.run()


#### TESTING FLOWGRAPH ONLY
class top_block_simple(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Top Block")

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 1e3

        ##################################################
        # Message Queues
        ##################################################
        #blocks_message_sink_0_msgq_out = blocks_message_source_0_msgq_in = gr.msg_queue(2)
        self.blocks_message_source_0_msgq_in = gr.msg_queue()

        ##################################################
        # Blocks
        ##################################################
        self.blocks_vector_to_streams_0 = blocks.vector_to_streams(gr.sizeof_char*1, 4)
        #self.blocks_vector_source_x_0 = blocks.vector_source_b((1, 0, 0, 1), True, 4, [])
        self.blocks_uchar_to_float_0_2 = blocks.uchar_to_float()
        self.blocks_uchar_to_float_0_1 = blocks.uchar_to_float()
        self.blocks_uchar_to_float_0_0 = blocks.uchar_to_float()
        self.blocks_uchar_to_float_0 = blocks.uchar_to_float()
        self.blocks_throttle_0 = blocks.throttle(gr.sizeof_float*1, samp_rate,True)
        self.blocks_message_source_0 = blocks.message_source(gr.sizeof_char*4, self.blocks_message_source_0_msgq_in)
        #self.blocks_message_source_0.message_port_register_in(pmt.pmt_intern("input_port"))
        #self.blocks_message_sink_0 = blocks.message_sink(gr.sizeof_char*4, blocks_message_sink_0_msgq_out, False)
        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_float*1, "simple.float", False)
        self.blocks_file_sink_0.set_unbuffered(False)
        self.blocks_add_xx_0 = blocks.add_vff(1)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_add_xx_0, 0), (self.blocks_throttle_0, 0))
        self.connect((self.blocks_message_source_0, 0), (self.blocks_vector_to_streams_0, 0))
        self.connect((self.blocks_throttle_0, 0), (self.blocks_file_sink_0, 0))
        self.connect((self.blocks_uchar_to_float_0, 0), (self.blocks_add_xx_0, 3))
        self.connect((self.blocks_uchar_to_float_0_0, 0), (self.blocks_add_xx_0, 2))
        self.connect((self.blocks_uchar_to_float_0_1, 0), (self.blocks_add_xx_0, 1))
        self.connect((self.blocks_uchar_to_float_0_2, 0), (self.blocks_add_xx_0, 0))
        #self.connect((self.blocks_vector_source_x_0, 0), (self.blocks_message_sink_0, 0))
        self.connect((self.blocks_vector_to_streams_0, 3), (self.blocks_uchar_to_float_0, 0))
        self.connect((self.blocks_vector_to_streams_0, 2), (self.blocks_uchar_to_float_0_0, 0))
        self.connect((self.blocks_vector_to_streams_0, 1), (self.blocks_uchar_to_float_0_1, 0))
        self.connect((self.blocks_vector_to_streams_0, 0), (self.blocks_uchar_to_float_0_2, 0))

    # this method transfers data from a python list to the
    # flowgraph's message queue for transmission
    def fill_queue_vector(self, bb_list, hop_select_list):

        # baseband and select values must be the same
        if len(bb_list) != len(hop_select_list):
            print "Fatal Error: hop select list must be same length as baseband list"
            exit(1)
        # create a vector entry of the bb bits and corresponding enables
        # vector_sample = numpy.array([b'\x00', 0, 0, 0])
        vector_sample = [b'\x00', b'\x00', b'\x00', b'\x00']
        # now we make a u8 vector out of this
        vector_pmt = pmt.make_u8vector(4, 95)

        for i in xrange(len(bb_list)):
            # assign first vector element to bb value
            vector_sample[0] = b'\x01' if bb_list[i] == 1 else b'\x00'
            if hop_select_list[i] == 0:
                vector_sample[1] = b'\x01'
                vector_sample[2] = b'\x00'
                vector_sample[3] = b'\x00'
            elif hop_select_list[i] == 1:
                vector_sample[1] = b'\x00'
                vector_sample[2] = b'\x01'
                vector_sample[3] = b'\x00'
            elif hop_select_list[i] == 2:
                vector_sample[1] = b'\x00'
                vector_sample[2] = b'\x00'
                vector_sample[3] = b'\x01'
            else:
                print "Fatal Error: hop select out of range; must be 0-2"
                exit(1)

            # vector_pmt = pmt.to_pmt(vector_sample)
            vector_str = ""
            for uchar in vector_sample:
                vector_str += uchar
            message = gr.message_from_string(vector_str)
            self.blocks_message_source_0_msgq_in.insert_tail(message)

            # THIS STUFF IS THE PMT APPROACH
            #port = pmt.intern("input_port")
            #self.blocks_message_source_0.to_basic_block()._post(port, vector_pmt)
            #message = pmt.cons(pmt.PMT_NIL, vector_pmt)
            #self.blocks_message_source_0_msgq_in.insert_tail(message)

            # THIS STUFF IS THE MESSAGE QUEUE APPROACH
            # vector_str = gr.message_from_string(vector_sample)
            #self.source_queue_v.insert_tail(vector_str)
            #vector_string = pmt.write_string(vector_pmt)
            #print vector_string
            #message = gr.message_from_string(vector_string)
            #self.blocks_message_source_0_msgq_in.insert_tail(message)




######### TESTING 2
class top_block(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self, "Top Block")

        ##################################################
        # Variables
        ##################################################
        self.fsk_deviation_hz = fsk_deviation_hz = 15e3
        self.channel_width = channel_width = fsk_deviation_hz * 1.3
        self.t_width = t_width = channel_width / 10
        self.samp_rate = samp_rate = 8e6
        self.freq2 = freq2 = 433.777e6
        self.freq1 = freq1 = 434.138e6
        self.freq0 = freq0 = 433.178e6
        self.channel_filter_taps = channel_filter_taps = firdes.low_pass(1, samp_rate, channel_width, t_width)
        self.center_freq = center_freq = 435e6
        self.baseband_samp_rate = baseband_samp_rate = 16e3

        ##################################################
        # Message Queues
        ##################################################
        #blocks_message_sink_0_msgq_out = blocks_message_source_0_msgq_in = gr.msg_queue(2)
        self.blocks_message_source_0_msgq_in = gr.msg_queue()
        ##################################################
        # Blocks
        ##################################################

        self.digital_gfsk_mod_0 = digital.gfsk_mod(
            samples_per_symbol=int(samp_rate / baseband_samp_rate),
            sensitivity=(2 * math.pi * (fsk_deviation_hz / 2)) / samp_rate,
            bt=0.35,
            verbose=False,
            log=False,
        )
        self.blocks_vector_to_streams_0 = blocks.vector_to_streams(gr.sizeof_char * 1, 4)
        self.blocks_vector_source_x_0 = blocks.vector_source_b((1, 0, 0, 1), True, 4, [])
        self.blocks_unpacked_to_packed_xx_0 = blocks.unpacked_to_packed_bb(1, gr.GR_MSB_FIRST)
        self.blocks_uchar_to_float_1_0_0 = blocks.uchar_to_float()
        self.blocks_uchar_to_float_1_0 = blocks.uchar_to_float()
        self.blocks_uchar_to_float_1 = blocks.uchar_to_float()
        self.blocks_throttle_0 = blocks.throttle(gr.sizeof_gr_complex * 1, samp_rate, True)
        self.blocks_null_sink_0 = blocks.null_sink(gr.sizeof_gr_complex * 1)
        self.blocks_multiply_xx_0_0_0_1 = blocks.multiply_vcc(1)
        self.blocks_multiply_xx_0_0_0 = blocks.multiply_vcc(1)
        self.blocks_multiply_xx_0_0 = blocks.multiply_vcc(1)
        self.blocks_multiply_xx_0 = blocks.multiply_vcc(1)
        self.blocks_message_source_0 = blocks.message_source(gr.sizeof_char * 4, self.blocks_message_source_0_msgq_in)
        #self.blocks_message_sink_0 = blocks.message_sink(gr.sizeof_char * 4, blocks_message_sink_0_msgq_out, False)
        self.blocks_float_to_complex_0_1 = blocks.float_to_complex(1)
        self.blocks_float_to_complex_0_0 = blocks.float_to_complex(1)
        self.blocks_float_to_complex_0 = blocks.float_to_complex(1)
        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_gr_complex * 1,
                                                   "test.iq",
                                                   False)
        self.blocks_file_sink_0.set_unbuffered(False)
        self.blocks_add_xx_0 = blocks.add_vcc(1)
        self.analog_sig_source_x_0_0_0_1 = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, freq2 - center_freq, 1, 0)
        self.analog_sig_source_x_0_0_0 = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, freq1 - center_freq, 1, 0)
        self.analog_sig_source_x_0_0 = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, freq0 - center_freq, 1, 0)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_sig_source_x_0_0, 0), (self.blocks_multiply_xx_0_0, 0))
        self.connect((self.analog_sig_source_x_0_0_0, 0), (self.blocks_multiply_xx_0_0_0, 0))
        self.connect((self.analog_sig_source_x_0_0_0_1, 0), (self.blocks_multiply_xx_0_0_0_1, 0))
        self.connect((self.blocks_add_xx_0, 0), (self.blocks_multiply_xx_0, 0))
        self.connect((self.blocks_float_to_complex_0, 0), (self.blocks_multiply_xx_0_0, 1))
        self.connect((self.blocks_float_to_complex_0_0, 0), (self.blocks_multiply_xx_0_0_0, 1))
        self.connect((self.blocks_float_to_complex_0_1, 0), (self.blocks_multiply_xx_0_0_0_1, 1))
        self.connect((self.blocks_message_source_0, 0), (self.blocks_vector_to_streams_0, 0))
        self.connect((self.blocks_multiply_xx_0, 0), (self.blocks_throttle_0, 0))
        self.connect((self.blocks_multiply_xx_0_0, 0), (self.blocks_add_xx_0, 0))
        self.connect((self.blocks_multiply_xx_0_0_0, 0), (self.blocks_add_xx_0, 1))
        self.connect((self.blocks_multiply_xx_0_0_0_1, 0), (self.blocks_add_xx_0, 2))
        self.connect((self.blocks_throttle_0, 0), (self.blocks_file_sink_0, 0))
        self.connect((self.blocks_throttle_0, 0), (self.blocks_null_sink_0, 0))
        self.connect((self.blocks_uchar_to_float_1, 0), (self.blocks_float_to_complex_0, 0))
        self.connect((self.blocks_uchar_to_float_1, 0), (self.blocks_float_to_complex_0, 1))
        self.connect((self.blocks_uchar_to_float_1_0, 0), (self.blocks_float_to_complex_0_0, 0))
        self.connect((self.blocks_uchar_to_float_1_0, 0), (self.blocks_float_to_complex_0_0, 1))
        self.connect((self.blocks_uchar_to_float_1_0_0, 0), (self.blocks_float_to_complex_0_1, 0))
        self.connect((self.blocks_uchar_to_float_1_0_0, 0), (self.blocks_float_to_complex_0_1, 1))
        self.connect((self.blocks_unpacked_to_packed_xx_0, 0), (self.digital_gfsk_mod_0, 0))
        #self.connect((self.blocks_vector_source_x_0, 0), (self.blocks_message_sink_0, 0))
        self.connect((self.blocks_vector_to_streams_0, 1), (self.blocks_uchar_to_float_1, 0))
        self.connect((self.blocks_vector_to_streams_0, 2), (self.blocks_uchar_to_float_1_0, 0))
        self.connect((self.blocks_vector_to_streams_0, 3), (self.blocks_uchar_to_float_1_0_0, 0))
        self.connect((self.blocks_vector_to_streams_0, 0), (self.blocks_unpacked_to_packed_xx_0, 0))
        self.connect((self.digital_gfsk_mod_0, 0), (self.blocks_multiply_xx_0, 1))

    # this method transfers data from a python list to the
    # flowgraph's message queue for transmission
    def fill_queue_vector(self, bb_list, hop_select_list):

        # baseband and select values must be the same
        if len(bb_list) != len(hop_select_list):
            print "Fatal Error: hop select list must be same length as baseband list"
            exit(1)
        # create a vector entry of the bb bits and corresponding enables
        # vector_sample = numpy.array([b'\x00', 0, 0, 0])
        vector_sample = [b'\x00', 0, 0, 0]
        # now we make a u8 vector out of this
        # vector_pmt = pmt.make_u8vector(4, b'\x00')

        for i in xrange(len(bb_list)):
            # assign first vector element to bb value
            vector_sample[0] = b'\x01' if bb_list[i] == 1 else b'\x00'
            if hop_select_list[i] == 0:
                vector_sample[1] = b'\x01'
                vector_sample[2] = b'\x00'
                vector_sample[3] = b'\x00'
            elif hop_select_list[i] == 1:
                vector_sample[1] = b'\x00'
                vector_sample[2] = b'\x01'
                vector_sample[3] = b'\x00'
            elif hop_select_list[i] == 2:
                vector_sample[1] = b'\x00'
                vector_sample[2] = b'\x00'
                vector_sample[3] = b'\x01'
            else:
                print "Fatal Error: hop select out of range; must be 0-2"
                exit(1)

            # vector_pmt = pmt.to_pmt(vector_sample)
            vector_str = ""
            for uchar in vector_sample:
                vector_str += uchar
            message = gr.message_from_string(vector_str)
            self.blocks_message_source_0_msgq_in.insert_tail(message)

            # vector_str = gr.message_from_string(vector_sample)
            # self.source_queue_v.insert_tail(vector_str)


    ##############################################################
class fsk_hop_tx_flowgraph(gr.top_block):
    def __init__(self, center_freq, samp_rate, gain, fsk_deviation_hz,
                 baseband_file_name, baseband_samp_rate,
                 freq_hop_list, verbose = False,
                 hardware_transmit_enable = True, hw_sel = 0, hw_gain = 0,
                 iq_file_out = False):
        gr.top_block.__init__(self)

        # display the parameters used for transmit
        if True: #verbose:
            print "Baseband File Name: {}".format(baseband_file_name)
            print "Baseband Sample Rate: {}".format(baseband_samp_rate)
            print "SDR Center Freq: {}".format(center_freq)
            print "SDR Sample Rate: {}".format(samp_rate)
            print "Flowgraph Gain: {}".format(gain)
            print "GFSK deviation: {}".format(fsk_deviation_hz)
            print "Freq 0-2: {}".format(freq_hop_list)
            print "Verbose: {}".format(verbose)
            print "Hardware TX Enable: {}".format(hardware_transmit_enable)
            print "IQ to File: {}".format(iq_file_out)

        ##################################################
        # Variables
        ##################################################
        self.center_freq = center_freq
        self.samp_rate = samp_rate
        self.gain = gain
        self.fsk_deviation_hz = fsk_deviation_hz
        self.baseband_file_name = baseband_file_name
        self.baseband_samp_rate = baseband_samp_rate
        self.freq_hop_list = freq_hop_list
        self.hw_sel = hw_sel
        self.hw_gain = hw_gain

        """
        r = gr.enable_realtime_scheduling()
        if r == gr.RT_OK:
            print "Note: Realtime scheduling enabled"
        """
        # self.cutoff_freq = channel_width/2
        ##################################################
        # Blocks
        ##################################################
        # replace this with a message source
        #self.blocks_file_source_0 = blocks.file_source(
        #    gr.sizeof_char * 1,
        #    baseband_file_name,
        #    repeat)
        # message sink is primary method of getting baseband data into
        # the flowgraph
        #self.source_queue = gr.msg_queue()
        #self.blocks_message_source_0 = blocks.message_source(
        #    gr.sizeof_char*1,
        #    self.source_queue)
        #self.blocks_message_source_0.set_max_output_buffer(1)

        # TESTING FLOWGRAPH ONLY (DELETE WHEN DONE)
        #blocks_message_sink_0_msgq_out = blocks_message_source_0_msgq_in = gr.msg_queue(2)
        #self.blocks_vector_source_x_0 = blocks.vector_source_b((1, 0, 0, 1), True, 4, [])
        #self.blocks_message_sink_0 = blocks.message_sink(gr.sizeof_char * 4, blocks_message_sink_0_msgq_out, False)
        #self.connect((self.blocks_vector_source_x_0, 0), (self.blocks_message_sink_0, 0))

        self.source_queue_v = gr.msg_queue()
        #self.source_queue_v = gr.msg_queue(2048) # smaller values cause hang
        self.blocks_message_source_0 = blocks.message_source(
            gr.sizeof_char*4,
            self.source_queue_v)
        self.blocks_vector_to_streams = blocks.vector_to_streams(gr.sizeof_char * 1, 4)
        self.connect(
            (self.blocks_message_source_0, 0),
            (self.blocks_vector_to_streams, 0))

        # blocks and connections for carrier for first hop frequency
        self.analog_sig_source_0 = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, freq_hop_list[0] - center_freq, 1, 0)
        self.repeat_0 = blocks.repeat(gr.sizeof_char * 1, int(samp_rate / baseband_samp_rate))
        self.blocks_uchar_to_float_0 = blocks.uchar_to_float()
        self.blocks_float_to_complex_0 = blocks.float_to_complex(1)
        self.blocks_multiply_0 = blocks.multiply_vcc(1)
        self.connect((self.blocks_vector_to_streams, 1), (self.repeat_0, 0))
        self.connect((self.repeat_0, 0), (self.blocks_uchar_to_float_0, 0))
        self.connect((self.blocks_uchar_to_float_0, 0), (self.blocks_float_to_complex_0, 0))
        self.connect((self.blocks_uchar_to_float_0, 0), (self.blocks_float_to_complex_0, 1))
        self.connect((self.blocks_float_to_complex_0, 0), (self.blocks_multiply_0, 1))
        self.connect((self.analog_sig_source_0, 0), (self.blocks_multiply_0, 0))

        # blocks and connections for carrier for second hop frequency
        self.analog_sig_source_1 = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, freq_hop_list[1] - center_freq, 1, 0)
        self.repeat_1 = blocks.repeat(gr.sizeof_char*1, int(samp_rate/baseband_samp_rate))
        self.blocks_uchar_to_float_1 = blocks.uchar_to_float()
        self.blocks_float_to_complex_1 = blocks.float_to_complex(1)
        self.blocks_multiply_1 = blocks.multiply_vcc(1)
        self.connect((self.blocks_vector_to_streams, 2), (self.repeat_1, 0))
        self.connect((self.repeat_1, 0), (self.blocks_uchar_to_float_1, 0))
        self.connect((self.blocks_uchar_to_float_1, 0), (self.blocks_float_to_complex_1, 0))
        self.connect((self.blocks_uchar_to_float_1, 0), (self.blocks_float_to_complex_1, 1))
        self.connect((self.blocks_float_to_complex_1, 0), (self.blocks_multiply_1, 1))
        self.connect((self.analog_sig_source_1, 0), (self.blocks_multiply_1, 0))

        # blocks and connections for carrier for third hop frequency
        self.analog_sig_source_2 = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, freq_hop_list[2] - center_freq, 1, 0)
        self.repeat_2 = blocks.repeat(gr.sizeof_char * 1, int(samp_rate / baseband_samp_rate))
        self.blocks_uchar_to_float_2 = blocks.uchar_to_float()
        self.blocks_float_to_complex_2 = blocks.float_to_complex(1)
        self.blocks_multiply_2 = blocks.multiply_vcc(1)
        self.connect((self.blocks_vector_to_streams, 3), (self.repeat_2, 0))
        self.connect((self.repeat_2, 0), (self.blocks_uchar_to_float_2, 0))
        self.connect((self.blocks_uchar_to_float_2, 0), (self.blocks_float_to_complex_2, 0))
        self.connect((self.blocks_uchar_to_float_2, 0), (self.blocks_float_to_complex_2, 1))
        self.connect((self.blocks_float_to_complex_2, 0), (self.blocks_multiply_2, 1))
        self.connect((self.analog_sig_source_2, 0), (self.blocks_multiply_2, 0))

        # now add the three gated carrier together; the selected
        # one will pass through
        self.blocks_add = blocks.add_vcc(1)
        self.connect((self.blocks_multiply_0, 0), (self.blocks_add, 0))
        self.connect((self.blocks_multiply_1, 0), (self.blocks_add, 1))
        self.connect((self.blocks_multiply_2, 0), (self.blocks_add, 2))

        # all of the baseband data goes to the modulation chain
        self.blocks_unpacked_to_packed = blocks.unpacked_to_packed_bb(
            1,
            gr.GR_MSB_FIRST)
        self.digital_gfsk_mod = digital.gfsk_mod(
            samples_per_symbol=int(samp_rate/baseband_samp_rate),
            sensitivity=(2 * math.pi * (fsk_deviation_hz / 2)) / samp_rate,
            bt=0.35,
            verbose=False,
            log=False,
        )
        self.connect(
            (self.blocks_vector_to_streams, 0),
            (self.blocks_unpacked_to_packed, 0))
        self.connect(
            (self.blocks_unpacked_to_packed, 0),
            (self.digital_gfsk_mod, 0))

        # use the passed-through carrier to tune/modulate the gfsk output
        self.blocks_multiply_tune = blocks.multiply_vcc(1)
        self.connect(
            (self.digital_gfsk_mod, 0),
            (self.blocks_multiply_tune, 0))
        self.connect(
            (self.blocks_add, 0),
            (self.blocks_multiply_tune, 1))


        # setup osmocom block for HackRF control
        # NEED: add control switch for USRP models
        if hardware_transmit_enable:
            if self.hw_sel == 0:
                self.osmosdr_sink = osmosdr.sink(
                    args="numchan=" + str(1) + " " + "")
                self.osmosdr_sink.set_sample_rate(samp_rate)
                self.osmosdr_sink.set_center_freq(center_freq, 0)
                self.osmosdr_sink.set_freq_corr(0, 0)
                self.osmosdr_sink.set_gain(hw_gain, 0)
                self.osmosdr_sink.set_if_gain(20, 0)
                self.osmosdr_sink.set_bb_gain(20, 0)
                self.osmosdr_sink.set_antenna("", 0)
                self.osmosdr_sink.set_bandwidth(0, 0)
                self.connect(
                    (self.blocks_multiply_tune, 0),
                    (self.osmosdr_sink, 0))
            elif self.hw_sel == 1:
                self.uhd_usrp_sink_0 = uhd.usrp_sink(
                    ",".join(("", "")),
                    uhd.stream_args(
                        cpu_format="fc32",
                        channels=range(1),
                    ),
                )
                self.uhd_usrp_sink_0.set_samp_rate(samp_rate)
                self.uhd_usrp_sink_0.set_center_freq(center_freq, 0)
                self.uhd_usrp_sink_0.set_gain(hw_gain, 0)
                self.uhd_usrp_sink_0.set_antenna('TX/RX', 0)
                self.connect(
                    (self.blocks_multiply_tune, 0),
                    (self.uhd_usrp_sink_0, 0))

        # this file sink provides an IQ capture of the RF
        # being transmitted by this app; the resulting file
        # is used for debugging only and should be disabled
        # under normal use
        if iq_file_out:
            self.blocks_file_sink_iq = blocks.file_sink(
                gr.sizeof_gr_complex*1,
                "takeover_output_c435M_s8M.iq",
                False)
            self.blocks_file_sink_iq.set_unbuffered(False)

            self.connect(
                (self.blocks_multiply_tune, 0),
                (self.blocks_file_sink_iq, 0)
            )

        # attempts to decrease latency
        #self.blocks_message_source_0.set_max_noutput_items(128)
        #self.blocks_multiply_tune.set_max_noutput_items(512)
        buffer_size = 1
        self.blocks_message_source_0.set_max_output_buffer(buffer_size)
        self.blocks_vector_to_streams.set_max_output_buffer(buffer_size)


    def retune(self, new_freq):
        self.frequency = new_freq
        self.analog_sig_source_x_0.set_frequency(
            self.frequency - self.center_freq)

    # this method transfers data from a python list to the
    # flowgraph's message queue for transmission
    def fill_queue(self, txDataList):
        message_str = ""
        for bit in txDataList:
            if bit == 1:
                message_str += b'\x01'
            elif bit == 0:
                message_str += b'\x00'
            else:
                print "Error passing data to flowgraph. Exiting..."
                exit(1)
            self.source_queue.handle(gr.message_from_string(message_str))
            message_str = ""
        #self.source_queue.insert_tail(gr.message_from_string(message_str))


    # this method transfers data from a python list to the
    # flowgraph's message queue for transmission
    def fill_queue_vector(self, bb_list, hop_select_list):

        # baseband and select values must be the same
        if len(bb_list) != len(hop_select_list):
            print "Fatal Error: hop select list must be same length as baseband list"
            exit(1)
        # create a vector entry of the bb bits and corresponding enables
        #vector_sample = numpy.array([b'\x00', 0, 0, 0])
        vector_sample = [b'\x00', b'\x00', b'\x00', b'\x00']
        # now we make a u8 vector out of this
        #vector_pmt = pmt.make_u8vector(4, b'\x00')

        for i in xrange(len(bb_list)):
            # assign first vector element to bb value
            vector_sample[0] = b'\x01' if bb_list[i] == 1 else b'\x00'
            if hop_select_list[i] == 0:
                vector_sample[1] = b'\x01'
                vector_sample[2] = b'\x00'
                vector_sample[3] = b'\x00'
            elif hop_select_list[i] == 1:
                vector_sample[1] = b'\x00'
                vector_sample[2] = b'\x01'
                vector_sample[3] = b'\x00'
            elif hop_select_list[i] == 2:
                vector_sample[1] = b'\x00'
                vector_sample[2] = b'\x00'
                vector_sample[3] = b'\x01'
            else:
                print "Fatal Error: hop select out of range; must be 0-2"
                exit(1)

            #vector_pmt = pmt.to_pmt(vector_sample)
            vector_str = ""
            for uchar in vector_sample:
                vector_str += uchar
            message = gr.message_from_string(vector_str)
            self.source_queue_v.insert_tail(message)

    # this flowgraph flushes the buffers of all blocks
    def flush_all(self):
        return 0


        ##############################################################
class ook_tx_flowgraph(gr.top_block):
    def __init__(self, center_freq, freq, samp_rate, gain, 
                 basebandFileName, basebandSampleRate, repeat):
        gr.top_block.__init__(self)
        
        ##################################################
        # Variables
        ##################################################
        #self.cutoff_freq = channel_width/2
        
        ##################################################
        # Blocks
        ##################################################
        self.blocks_file_source_0 = blocks.file_source(gr.sizeof_char*1, basebandFileName, repeat)
        self.blocks_repeat_0 = blocks.repeat(gr.sizeof_char*1, int(samp_rate/basebandSampleRate))

        # setup osmocom block for HackRF control
        self.osmosdr_sink_0 = osmosdr.sink( args="numchan=" + str(1) + " " + "" )
        self.osmosdr_sink_0.set_sample_rate(samp_rate)
        self.osmosdr_sink_0.set_center_freq(center_freq, 0)
        self.osmosdr_sink_0.set_freq_corr(0, 0)
        #self.osmosdr_sink_0.set_gain(14, 0)
        #self.osmosdr_sink_0.set_if_gain(20, 0)
        #self.osmosdr_sink_0.set_bb_gain(20, 0)
        self.osmosdr_sink_0.set_gain(0, 0)
        self.osmosdr_sink_0.set_if_gain(0, 0)
        self.osmosdr_sink_0.set_bb_gain(0, 0)
        self.osmosdr_sink_0.set_antenna("", 0)
        self.osmosdr_sink_0.set_bandwidth(0, 0)
          
        self.blocks_multiply_xx_0 = blocks.multiply_vcc(1)
        self.blocks_float_to_complex_0 = blocks.float_to_complex(1)
        self.blocks_char_to_float_0 = blocks.char_to_float(1, 1)
        self.analog_sig_source_x_0 = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, freq-center_freq, gain, 0)
        self.analog_const_source_x_0 = analog.sig_source_f(0, analog.GR_CONST_WAVE, 0, 0, 0)
        # message sink is primary method of getting baseband data into waveconverter        
        #self.sink_queue = gr.msg_queue()
        #self.blocks_message_sink_0 = blocks.message_sink(gr.sizeof_char*1, self.sink_queue, False)
        
        # if directed, we also dump the output IQ data into a file
        #if len(dig_out_filename) > 0:
            #print "Outputing IQ to waveform to " + dig_out_filename
            #self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_char*1, dig_out_filename, False)
            #self.blocks_file_sink_0.set_unbuffered(False)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_const_source_x_0, 0), (self.blocks_float_to_complex_0, 1))    
        self.connect((self.analog_sig_source_x_0, 0), (self.blocks_multiply_xx_0, 1))    
        self.connect((self.blocks_char_to_float_0, 0), (self.blocks_float_to_complex_0, 0))    
        self.connect((self.blocks_file_source_0, 0), (self.blocks_repeat_0, 0))    
        self.connect((self.blocks_float_to_complex_0, 0), (self.blocks_multiply_xx_0, 0))    
        self.connect((self.blocks_multiply_xx_0, 0), (self.osmosdr_sink_0, 0))    
        self.connect((self.blocks_repeat_0, 0), (self.blocks_char_to_float_0, 0))    

##############################################################
class fsk_tx_flowgraph(gr.top_block):
    def __init__(self, center_freq, freq, samp_rate, fsk_deviation_hz, 
                 basebandFileName, basebandSampleRate, repeat):
        gr.top_block.__init__(self)
        
        ##################################################
        # Variables
        ##################################################
        #self.cutoff_freq = channel_width/2
        
        ##################################################
        # Blocks
        ##################################################
        self.blocks_file_source_0 = blocks.file_source(gr.sizeof_char*1, basebandFileName, repeat)
        self.blocks_repeat_0 = blocks.repeat(gr.sizeof_char*1, int(samp_rate/basebandSampleRate))

        # setup osmocom block for HackRF control
        self.osmosdr_sink_0 = osmosdr.sink( args="numchan=" + str(1) + " " + "" )
        self.osmosdr_sink_0.set_sample_rate(samp_rate)
        self.osmosdr_sink_0.set_center_freq(center_freq, 0)
        self.osmosdr_sink_0.set_freq_corr(0, 0)
        #self.osmosdr_sink_0.set_gain(14, 0)
        #self.osmosdr_sink_0.set_if_gain(20, 0)
        #self.osmosdr_sink_0.set_bb_gain(20, 0)
        self.osmosdr_sink_0.set_gain(0, 0)
        self.osmosdr_sink_0.set_if_gain(0, 0)
        self.osmosdr_sink_0.set_bb_gain(0, 0)
        self.osmosdr_sink_0.set_antenna("", 0)
        self.osmosdr_sink_0.set_bandwidth(0, 0)
          
        self.blocks_multiply_xx_0 = blocks.multiply_vcc(1)
        self.blocks_float_to_complex_0 = blocks.float_to_complex(1)
        self.blocks_char_to_float_0 = blocks.char_to_float(1, 1)
        self.analog_sig_source_x_0 = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, freq-center_freq, gain, 0)
        self.analog_const_source_x_0 = analog.sig_source_f(0, analog.GR_CONST_WAVE, 0, 0, 0)
        # message sink is primary method of getting baseband data into waveconverter        
        #self.sink_queue = gr.msg_queue()
        #self.blocks_message_sink_0 = blocks.message_sink(gr.sizeof_char*1, self.sink_queue, False)
        
        # if directed, we also dump the output IQ data into a file
        #if len(dig_out_filename) > 0:
            #print "Outputing IQ to waveform to " + dig_out_filename
            #self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_char*1, dig_out_filename, False)
            #self.blocks_file_sink_0.set_unbuffered(False)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_const_source_x_0, 0), (self.blocks_float_to_complex_0, 1))    
        self.connect((self.analog_sig_source_x_0, 0), (self.blocks_multiply_xx_0, 1))    
        self.connect((self.blocks_char_to_float_0, 0), (self.blocks_float_to_complex_0, 0))    
        self.connect((self.blocks_file_source_0, 0), (self.blocks_repeat_0, 0))    
        self.connect((self.blocks_float_to_complex_0, 0), (self.blocks_multiply_xx_0, 0))    
        self.connect((self.blocks_multiply_xx_0, 0), (self.osmosdr_sink_0, 0))    
        self.connect((self.blocks_repeat_0, 0), (self.blocks_char_to_float_0, 0))    




##############################################################
# This flowgraph consists of the following blocks:
# - a File Source that 
# - a Frequency Translating FIR filter that tunes to the target signal
# - a quadrature demod block that demodules the FSK signal
# - an Add Const block that shifts the demodulated signal downwards, centering
#   it around zero on the y-axis
# - a Binary Slicer that converts centered signal from floating point to binary
# - a File Sink that outputs 

class fsk_flowgraph(gr.top_block):
    def __init__(self, samp_rate_in, samp_rate_out, center_freq, 
                 tune_freq, channel_width, transition_width, threshold, fsk_deviation, fskSquelch,
                 iq_filename, dig_out_filename):
        gr.top_block.__init__(self)
        
        ##################################################
        # Variables
        ##################################################
        self.cutoff_freq = channel_width/2
        self.firdes_taps = firdes.low_pass(1, samp_rate_in, 
                                           self.cutoff_freq, 
                                           transition_width)
        
        ##################################################
        # Blocks
        ##################################################
        self.blocks_file_source_0 = blocks.file_source(gr.sizeof_gr_complex*1, iq_filename, False)
        self.blocks_tuning_filter_0 = filter.freq_xlating_fir_filter_ccc(int(samp_rate_in/samp_rate_out), 
                                                                         (self.firdes_taps), 
                                                                         tune_freq-center_freq, 
                                                                         samp_rate_in)
        self.analog_pwr_squelch_xx_0 = analog.pwr_squelch_cc(fskSquelch, 1, 1, False)
        self.blocks_quadrature_demod_0 = analog.quadrature_demod_cf(samp_rate_out/(2*pi*fsk_deviation/2))
        self.blocks_add_const_vxx_0 = blocks.add_const_vff((-1*threshold, ))
        self.blocks_digital_binary_slicer_fb_0 = digital.binary_slicer_fb()
        
        # swapped message sink for file sink
        #self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_char*1, dig_out_filename, False)
        #self.blocks_file_sink_0.set_unbuffered(False)
        self.sink_queue = gr.msg_queue()
        self.blocks_message_sink_0 = blocks.message_sink(gr.sizeof_char*1, self.sink_queue, False)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_file_source_0, 0), (self.blocks_tuning_filter_0, 0))
        self.connect((self.blocks_tuning_filter_0, 0), (self.analog_pwr_squelch_xx_0, 0))
        self.connect((self.analog_pwr_squelch_xx_0, 0), (self.blocks_quadrature_demod_0, 0))
        self.connect((self.blocks_quadrature_demod_0, 0), (self.blocks_add_const_vxx_0, 0))
        self.connect((self.blocks_add_const_vxx_0, 0), (self.blocks_digital_binary_slicer_fb_0, 0))
        
        #self.connect((self.digital_binary_slicer_fb_0, 0), (self.blocks_file_sink_0, 0))
        self.connect((self.blocks_digital_binary_slicer_fb_0, 0), (self.blocks_message_sink_0, 0))
        
