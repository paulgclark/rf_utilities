from gnuradio import analog
from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import filter
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from gnuradio import zeromq
from gnuradio import digital
from gnuradio import uhd
import pmt
import math
import osmosdr
import numpy
import rf_mod
from rf_const import HW_SEL_FILE, HW_SEL_HACKRF, HW_SEL_USRP, HW_SEL_LIME



# global constants
class ntsc_fm_demod_flowgraph(gr.top_block):
    def __init__(self, verbose, center_freq, freq,
                 samp_rate, bb_samp_rate,
                 fm_deviation, channel_width, transition_width,
                 bb_lpf_cutoff, bb_lpf_transition,
                 tcp_str,
                 hw_sel,
                 fifo_name = "", repeat=True, iq_file_name=""):

        gr.top_block.__init__(self)

        if verbose > 0:
            print "\nFlowgraph Properties:"
            print "  Center Frequency: {} MHz".format(center_freq/1000000.0)
            print "  Tune Frequency:   {} MHz".format(freq/1000000.0)
            print "  IQ Sample Rate (in): {} MHz".format(samp_rate/1000000.0)
            print "  BB Sample Rate (out): {} MHz".format(bb_samp_rate/1000000.0)
            print "  FM Deviation: {} MHz".format(fm_deviation/1000000.0)
            print "  Channel Width: {} MHz".format(channel_width/1000000.0)
            print "  Transition Width: {} MHz".format(transition_width/1000000.0)
            print "  BB LPF cutoff: {} MHz".format(bb_lpf_cutoff/1000000.0)
            print "  BB LPF transition: {} MHz".format(bb_lpf_transition/1000000.0)
            if hw_sel == 0:
                print "  SDR: HackRF"
            elif hw_sel == 1:
                print "  SDR: USRP"
            print "  FIFO Name: {}".format(fifo_name)
            print "  Repeat: {}".format(repeat)
            print "  IQ File Name: {}".format(iq_file_name)

        # start by dumping baseband into a file and viewing in grc

        if verbose > 0:
            print "Entering NTSC Demodulator..."

        # variables
        self.center_freq = center_freq
        self.freq = freq
        self.samp_rate = samp_rate
        self.bb_samp_rate = bb_samp_rate
        self.fm_deviation = fm_deviation
        self.channel_width = channel_width
        self.transition_width = transition_width
        self.bb_lpf_cutoff = bb_lpf_cutoff
        self.bb_lpf_transition = bb_lpf_transition
        self.repeat = repeat
        self.iq_file_name = iq_file_name
        self.fifo_name = fifo_name
        self.hw_sel = hw_sel

        self.tuning_taps = firdes.low_pass(1,
                                           self.samp_rate,
                                           self.channel_width/2,
                                           self.channel_width/16)
        self.lpf_taps = firdes.low_pass(1,
                                        samp_rate,
                                        self.bb_lpf_cutoff,
                                        self.bb_lpf_transition,
                                        firdes.WIN_HAMMING,
                                        6.76)

        # blocks

        # if we were not passed a file name, use the osmocom source
        if self.iq_file_name == "":
            if verbose > 0:
                print "Using SDR as input..."

            if self.hw_sel == 0:
                self.osmosdr_source_0 = osmosdr.source(
                    args="numchan=" + str(1) + " " + '')
                self.osmosdr_source_0.set_sample_rate(samp_rate)
                self.osmosdr_source_0.set_center_freq(center_freq, 0)
                self.osmosdr_source_0.set_freq_corr(0, 0)
                self.osmosdr_source_0.set_dc_offset_mode(0, 0)
                self.osmosdr_source_0.set_iq_balance_mode(0, 0)
                self.osmosdr_source_0.set_gain_mode(False, 0)
                self.osmosdr_source_0.set_gain(10, 0)
                self.osmosdr_source_0.set_if_gain(20, 0)
                self.osmosdr_source_0.set_bb_gain(20, 0)
                self.osmosdr_source_0.set_antenna('', 0)
                self.osmosdr_source_0.set_bandwidth(0, 0)
            elif self.hw_sel == 1:
                self.uhd_usrp_source_0 = uhd.usrp_source(
                    ",".join(("", "")),
                    uhd.stream_args(
                        cpu_format="fc32",
                        channels=range(1),
                    ),
                )
                self.uhd_usrp_source_0.set_samp_rate(samp_rate)
                self.uhd_usrp_source_0.set_center_freq(center_freq, 0)
                self.uhd_usrp_source_0.set_gain(20, 0)
                self.uhd_usrp_source_0.set_antenna('RX2', 0)

        # otherwise, use a file source with throttle
        else:
            if verbose > 0:
                print "Using {} as input...".format(iq_file_name)
            self.blocks_file_source_0 = blocks.file_source(
                gr.sizeof_gr_complex * 1,
                iq_file_name,
                repeat=repeat)
            self.blocks_throttle_0 = blocks.throttle(
                gr.sizeof_gr_complex * 1, samp_rate, True)
            self.connect(
                (self.blocks_file_source_0, 0),
                (self.blocks_throttle_0, 0)
            )

        # simple tuner
        self.analog_sig_source_x_0 = analog.sig_source_c(
            samp_rate,
            analog.GR_COS_WAVE,
            center_freq - freq,
            1,
            0)
        self.blocks_multiply_xx_0 = blocks.multiply_vcc(1)
        if iq_file_name == "":
            if self.hw_sel == 0:
                self.connect(
                    (self.osmosdr_source_0, 0),
                    (self.blocks_multiply_xx_0, 0)
                )
            elif self.hw_sel == 1:
                self.connect(
                    (self.uhd_usrp_source_0, 0),
                    (self.blocks_multiply_xx_0, 0)
                )
        else:
            self.connect(
                (self.blocks_throttle_0, 0),
                (self.blocks_multiply_xx_0, 0)
            )
        self.connect(
            (self.analog_sig_source_x_0, 0),
            (self.blocks_multiply_xx_0, 1)
        )

        """
        # simple decimator
        self.keep = blocks.keep_one_in_n(gr.sizeof_gr_complex*1, 4)
        self.connect(
            (self.blocks_multiply_xx_0, 0),
            (self.keep, 0)
        )
        """

        # demod block
        self.analog_quadrature_demod_cf_0_0 = analog.quadrature_demod_cf(
            (samp_rate) / (2 * math.pi * self.fm_deviation / 8.0))
        self.connect(
            (self.blocks_multiply_xx_0, 0),
            #(self.keep, 0),
            (self.analog_quadrature_demod_cf_0_0, 0)
        )

        # low pass filter the demod output
        self.low_pass_filter_1 = filter.filter.fir_filter_fff(
            int(samp_rate/bb_samp_rate),
            self.lpf_taps
        )
        self.connect(
            (self.analog_quadrature_demod_cf_0_0, 0),
            (self.low_pass_filter_1, 0)
        )

        # output the baseband to a fifo
        if False:
            self.blocks_file_sink_0 = blocks.file_sink(
                gr.sizeof_float * 1,
                fifo_name,
                False)
            self.blocks_file_sink_0.set_unbuffered(False)
            self.connect(
                (self.low_pass_filter_1, 0),
                (self.blocks_file_sink_0, 0)
            )

        """
        # multiply by a constant and then convert to a short to reduce data
        self.multiply_const = blocks.multiply_const_vff((10000, )) # how to scale?
        self.float_to_short = blocks.float_to_short(1, 1)
        self.connect(
            (self.low_pass_filter_1, 0),
            (self.multiply_const, 0)
        )
        self.connect(
            (self.multiply_const, 0),
            (self.float_to_short, 0)
        )
        self.connect(
            (self.float_to_short, 0),
            (self.zeromq_push_sink_0, 0)
        )
        """

        # now add the ZMQ block for output to the main program
        self.zeromq_push_sink_0 = zeromq.push_sink(gr.sizeof_float, # gr.sizeof_short,
                                                   1,
                                                   tcp_str,
                                                   100,
                                                   False,
                                                   32768*8)#-1)

        self.connect(
            (self.low_pass_filter_1, 0),
            (self.zeromq_push_sink_0, 0)
        )

    def update_freq(self, freq):
        self.freq = freq
        self.analog_sig_source_x_0.set_frequency(
            self.center_freq - self.freq)

    def update_center_freq(self, center_freq):
        self.center_freq = center_freq
        self.analog_sig_source_x_0.set_frequency(
            self.center_freq - self.freq)
        # can't adjust center frequency of hardware if we're running
        # with an IQ file
        if self.iq_file_name == "":
            if self.hw_sel == 0:
                self.osmosdr_source_0.set_center_freq(center_freq, 0)
            elif self.hw_sel == 1:
                self.uhd_usrp_source_0.set_center_freq(center_freq, 0)


    def update_lpf_cutoff(self, lpf_cutoff):
        self.bb_lpf_cutoff = lpf_cutoff
        self.lpf_taps = firdes.low_pass(1,
                                        samp_rate,
                                        self.bb_lpf_cutoff,
                                        self.bb_lpf_transition,
                                        firdes.WIN_HAMMING,
                                        6.76)
        self.low_pass_filter_1.set_taps(self.lpf_taps)



# this flowgraph
class ook_rx_zmq(gr.top_block):
    def __init__(self, verbose,
                 center_freq,
                 freq,
                 samp_rate,
                 threshold,
                 channel_width,
                 tcp_str,
                 hw_sel,
                 payload_len,
                 transition_width = 0,
                 iq_file_name=""):

        gr.top_block.__init__(self)

        if verbose > 0:
            print "\nFlowgraph Properties:"
            print "  Center Frequency: {} MHz".format(center_freq/1000000.0)
            print "  Tune Frequency:   {} MHz".format(freq/1000000.0)
            print "  IQ Sample Rate (in): {} MHz".format(samp_rate/1000000.0)
            print "  Channel Width: {} MHz".format(channel_width/1000000.0)
            print "  Transition Width: {} MHz".format(transition_width/1000000.0)
            print "  Threshold: {}".format(threshold)
            print "  IQ File Name: {}".format(iq_file_name)
            print "  ZMQ TCP ADDR: {}".format(tcp_str)
            print "  HW Sel: {}".format(hw_sel)

        # start by dumping baseband into a file and viewing in grc

        if verbose > 0:
            print "Entering OOK Demodulator..."

        # variables
        self.center_freq = center_freq
        self.freq = freq
        self.threshold = threshold
        self.channel_width = channel_width
        self.samp_rate = samp_rate
        if transition_width == 0:
            self.transition_width = channel_width/10
        else:
            self.transition_width = transition_width
        self.taps = firdes.low_pass(
            1,
            self.samp_rate,
            self.channel_width/2,
            self.transition_width)
        self.symbol_rate = 10e3
        self.samples_per_symbol = \
            int(self.samp_rate/self.symbol_rate)
        self.payload_len = payload_len

        # blocks, starting from the input channel filter
        self.freq_xlating_fir_filter_xxx_0 = \
            filter.freq_xlating_fir_filter_ccc(
                1,
                self.taps,
                freq - center_freq,
                samp_rate)
        if hw_sel == HW_SEL_FILE:
            self.blocks_file_source_0 = blocks.file_source(
                gr.sizeof_gr_complex * 1,
                iq_file_name,
                True)
            # skip the throttle block, we just want to get done
            self.connect(
                (self.blocks_file_source_0, 0),
                (self.freq_xlating_fir_filter_xxx_0, 0))
        elif hw_sel == HW_SEL_HACKRF:
            self.osmosdr_source_0 = osmosdr.source(
                args="numchan=" + str(1) + " " + '')
            self.osmosdr_source_0.set_sample_rate(samp_rate)
            self.osmosdr_source_0.set_center_freq(center_freq, 0)
            self.osmosdr_source_0.set_freq_corr(0, 0)
            self.osmosdr_source_0.set_dc_offset_mode(0, 0)
            self.osmosdr_source_0.set_iq_balance_mode(0, 0)
            self.osmosdr_source_0.set_gain_mode(False, 0)
            self.osmosdr_source_0.set_gain(10, 0)
            self.osmosdr_source_0.set_if_gain(20, 0)
            self.osmosdr_source_0.set_bb_gain(20, 0)
            self.osmosdr_source_0.set_antenna('', 0)
            self.osmosdr_source_0.set_bandwidth(0, 0)
            self.connect(
                (self.osmosdr_source_0, 0),
                (self.freq_xlating_fir_filter_xxx_0, 0))

        elif self.hw_sel == HW_SEL_USRP:
            self.uhd_usrp_source_0 = uhd.usrp_source(
                ",".join(("", "")),
                uhd.stream_args(
                    cpu_format="fc32",
                    channels=range(1),
                ),
            )
            self.uhd_usrp_source_0.set_samp_rate(samp_rate)
            self.uhd_usrp_source_0.set_center_freq(center_freq, 0)
            self.uhd_usrp_source_0.set_gain(20, 0)
            self.uhd_usrp_source_0.set_antenna('RX2', 0)
            self.connect(
                (self.osmosdr_source_0, 0),
                (self.uhd_usrp_source_0, 0))

        # add limeSDR using osmocom
        #elif self.hw_sel == HW_SEL_LIME:

        # demodulation
        self.blocks_complex_to_mag_0 = blocks.complex_to_mag(1)
        self.blocks_add_const_vxx_0 = blocks.add_const_vff(
            (-1 * threshold,))
        self.connect(
            (self.freq_xlating_fir_filter_xxx_0, 0),
            (self.blocks_complex_to_mag_0, 0))
        self.connect(
            (self.blocks_complex_to_mag_0, 0),
            (self.blocks_add_const_vxx_0, 0))

        # binary slicer is next major thing, but there
        # may be a pfb block in between
        self.digital_binary_slicer_fb_0 = digital.binary_slicer_fb()

        # polyphase clock sync (optional)
        if False:
            nfilts = 32
            self.rrc_taps = rrc_taps = \
                firdes.root_raised_cosine(
                    nfilts,
                    samp_rate,
                    self.symbol_rate,
                    0.35,
                    nfilts)
            self.digital_pfb_clock_sync_xxx_0_0 = \
                digital.pfb_clock_sync_fff(
                    self.samples_per_symbol,
                    62.8e-3,
                    (rrc_taps),
                    32,
                    16,
                    1.5,
                    self.samples_per_symbol)
            self.connect(
                (self.blocks_add_const_vxx_0, 0),
                (self.digital_pfb_clock_sync_xxx_0_0, 0))
            self.connect(
                (self.blocks_add_const_vxx_0, 0),
                (self.digital_binary_slicer_fb_0, 0)
            )
        else:
            self.connect(
                (self.blocks_add_const_vxx_0, 0),
                (self.digital_binary_slicer_fb_0, 0))

        # decimate down to the symbol rate
        self.blocks_keep_one_in_n_0 = blocks.keep_one_in_n(
            gr.sizeof_char * 1,
            int(self.samp_rate / self.symbol_rate))
        self.connect(
            (self.digital_binary_slicer_fb_0, 0),
            (self.blocks_keep_one_in_n_0, 0))

        # find preamble and apply tag
        self.digital_correlate_access_code_xx_ts_0 = \
            digital.correlate_access_code_bb_ts(
                "01010101010101010101",
                0,
                "packet_len")
        self.connect(
            (self.blocks_keep_one_in_n_0, 0),
            (self.digital_correlate_access_code_xx_ts_0, 0))

        # pack bitstream into bytes
        self.blocks_repack_bits_bb_0_0_0 = blocks.repack_bits_bb(
            1,
            8,
            'packet_len',
            False,
            gr.GR_MSB_FIRST)
        self.connect(
            (self.digital_correlate_access_code_xx_ts_0, 0),
            (self.blocks_repack_bits_bb_0_0_0, 0)
        )

        # generate PDU
        self.blocks_tagged_stream_to_pdu_0 = \
            blocks.tagged_stream_to_pdu(
                blocks.byte_t,
                'packet_len')
        self.connect(
            (self.blocks_repack_bits_bb_0_0_0, 0),
            (self.blocks_tagged_stream_to_pdu_0, 0))

        # add ZeroMQ sink to get data out of flowgraph
        self.zeromq_push_msg_sink_0 = zeromq.push_msg_sink(
            tcp_str, 100)
        self.msg_connect(
            (self.blocks_tagged_stream_to_pdu_0, 'pdus'),
            (self.zeromq_push_msg_sink_0, 'in'))

        # debug only
        if False:
            self.blocks_random_pdu_0 = blocks.random_pdu(
                50, 128, chr(0xFF), 2)
            self.msg_connect(
                (self.blocks_random_pdu_0, 'pdus'),
                (self.zeromq_push_msg_sink_0, 'in'))


  