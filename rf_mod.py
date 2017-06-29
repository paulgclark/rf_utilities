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
from math import pi
import osmosdr
import time

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
        
