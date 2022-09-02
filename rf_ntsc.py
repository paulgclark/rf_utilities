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
            print("\nFlowgraph Properties:")
            print("  Center Frequency: {} MHz".format(center_freq/1000000.0))
            print("  Tune Frequency:   {} MHz".format(freq/1000000.0))
            print("  IQ Sample Rate (in): {} MHz".format(samp_rate/1000000.0))
            print("  BB Sample Rate (out): {} MHz".format(bb_samp_rate/1000000.0))
            print("  FM Deviation: {} MHz".format(fm_deviation/1000000.0))
            print("  Channel Width: {} MHz".format(channel_width/1000000.0))
            print("  Transition Width: {} MHz".format(transition_width/1000000.0))
            print("  BB LPF cutoff: {} MHz".format(bb_lpf_cutoff/1000000.0))
            print("  BB LPF transition: {} MHz".format(bb_lpf_transition/1000000.0))
            if hw_sel == 0:
                print("  SDR: HackRF")
            elif hw_sel == 1:
                print("  SDR: USRP")
            print("  FIFO Name: {}".format(fifo_name))
            print("  Repeat: {}".format(repeat))
            print("  IQ File Name: {}".format(iq_file_name))

        # start by dumping baseband into a file and viewing in grc

        if verbose > 0:
            print("Entering NTSC Demodulator...")

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
                print("Using SDR as input...")

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
                print("Using {} as input...".format(iq_file_name))
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




# this flowgraph uses a frequency Xlating FIR filter on the input and is
# too computationally intensive; it has been replaced by a simpler multiply
# tuner version
class ntsc_fm_demod_flowgraph_fxfir(gr.top_block):
    def __init__(self, verbose, center_freq, freq,
                 samp_rate, bb_samp_rate,
                 fm_deviation, channel_width, transition_width,
                 bb_lpf_cutoff, bb_lpf_transition,
                 tcp_str, fifo_name = "", repeat=True, iq_file_name=""):

        gr.top_block.__init__(self)

        if verbose > 0:
            print("\nFlowgraph Properties:")
            print("  Center Frequency: {} MHz".format(center_freq/1000000.0))
            print("  Tune Frequency:   {} MHz".format(freq/1000000.0))
            print("  IQ Sample Rate (in): {} MHz".format(samp_rate/1000000.0))
            print("  BB Sample Rate (out): {} MHz".format(bb_samp_rate/1000000.0))
            print("  FM Deviation: {} MHz".format(fm_deviation/1000000.0))
            print("  Channel Width: {} MHz".format(channel_width/1000000.0))
            print("  Transition Width: {} MHz".format(transition_width/1000000.0))
            print("  BB LPF cutoff: {} MHz".format(bb_lpf_cutoff/1000000.0))
            print("  BB LPF transition: {} MHz".format(bb_lpf_transition/1000000.0))
            print("  FIFO Name: {}".format(fifo_name))
            print("  Repeat: {}".format(repeat))
            print("  IQ File Name: {}".format(iq_file_name))

        # start by dumping baseband into a file and viewing in grc

        if verbose > 0:
            print("Entering NTSC Demodulator...")

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
                print("Using SDR as input...")
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
        # otherwise, use a file source with throttle
        else:
            if verbose > 0:
                print("Using {} as input...".format(iq_file_name))
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

        # channel filter
        self.freq_xlating_fir_filter_ccc_0 = filter.freq_xlating_fir_filter_ccc(
            1,
            self.tuning_taps,
            freq - center_freq,
            samp_rate)
        if iq_file_name == "":
            self.connect(
                (self.osmosdr_source_0, 0),
                (self.freq_xlating_fir_filter_ccc_0, 0)
            )
        else:
            self.connect(
                (self.blocks_throttle_0, 0),
                (self.freq_xlating_fir_filter_ccc_0, 0)
            )

        # demod block
        self.analog_quadrature_demod_cf_0_0 = analog.quadrature_demod_cf(
            (samp_rate) / (2 * math.pi * self.fm_deviation / 8.0))
        self.connect(
            (self.freq_xlating_fir_filter_ccc_0, 0),
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
        self.multiply_const = blocks.multiply_const_vff((10000, ))
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
        self.freq_xlating_fir_filter_ccc_0.set_center_freq(
            self.freq - self.center_freq)

    def update_center_freq(self, center_freq):
        self.center_freq = center_freq
        self.osmosdr_source_0.set_center_freq(center_freq, 0)
        self.freq_xlating_fir_filter_ccc_0.set_center_freq(
            self.freq - self.center_freq)

    def update_lpf_cutoff(self, lpf_cutoff):
        self.bb_lpf_cutoff = lpf_cutoff
        self.lpf_taps = firdes.low_pass(1,
                                        samp_rate,
                                        self.bb_lpf_cutoff,
                                        self.bb_lpf_transition,
                                        firdes.WIN_HAMMING,
                                        6.76)
        self.low_pass_filter_1.set_taps(self.lpf_taps)

