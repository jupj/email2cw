import math
import wave
import struct
import winsound

class CW_Generator:
    def __init__(self, samplerate=44100, wpm=25, frequency=600):
        self.samplerate = samplerate
        self.frequency = frequency # Hz
        self.wpm = wpm
        self.cpm = 5 * wpm
        self.unitduration = 1.2 / float(wpm) # dit duration in s
        self.dit_duration = int(self.samplerate*self.unitduration) # in sample points

        self.cache = {}

    def lowpassfilter(self, in_signal):
        """Low pass filter used to remove clicks from the cw signal.

        Digital low pass filter (RC filter):
        y[n+1] = y[n] + k(x[n] - y[n])
        x[n] is the input series
        y[n] is the output series

        k = 800/samplerate gives a rise time of about 4ms
                            which is suitable for cw
        """

        k = 800/float(self.samplerate)
        out_signal = []
        y = 0
        for x in in_signal:
            y = y + k*(x - y)
            out_signal.append(y)
        return out_signal

    def continouswave(self, keyed_signal):
        """ Multiply the keyed signal with a sine wave (BFO)"""
        amplitude = 16384
        period = self.samplerate / float(self.frequency) # in sample points
        omega = math.pi * 2 / period

        cw_signal = []
        for i in range(len(keyed_signal)):
            x = omega*i
            cw_signal.append(keyed_signal[i] * amplitude * math.sin(x))
        return cw_signal

    def dit(self):
        """Create a signal for:
           one dit duration
           silence for one dit duration"""

        # check cache first:
        if 'dit' not in self.cache:
            # create the signal
            key_signal = [1] * self.dit_duration
            key_signal.extend([0]*self.dit_duration)
            cw_signal = self.continouswave(self.lowpassfilter(key_signal))
            self.cache['dit'] = cw_signal
        return self.cache['dit']

    def dah(self):
        """Create a signal for:
           one dah duration (= 3 dits)
           silence for one dit duration"""

        # check cache first:
        if 'dah' not in self.cache:
            # create the signal
            key_signal = [1] * 3 * self.dit_duration
            key_signal.extend([0]*self.dit_duration)
            cw_signal = self.continouswave(self.lowpassfilter(key_signal))
            self.cache['dah'] = cw_signal
        return self.cache['dah']

    def char_space(self):
        """Create a keyed signal for:
           silence for 2 dit durations
           (it's actually 3, but we remove the
           one duration included in each dit/dah)"""
        return [0] * 2 * self.dit_duration

    def word_space(self):
        """Create a keyed signal for:
           silence for 6 dit durations
           (it's actually 7, but we remove the
           one duration included in each dit/dah)"""
        return [0] * 6 * self.dit_duration

    def play(self, signal):
        """Save signal as a wave file and play it"""
        # TODO: use StringIO instead of file, and play it from memory
        file = wave.open('test.wav', 'wb')
        file.setparams((1, 2, self.samplerate, len(signal), 'NONE', 'noncompressed'))
        ssignal = ''
        for smpl in signal:
            ssignal += struct.pack('h',smpl) # transform to binary

        file.writeframes(ssignal)
        file.close()
        winsound.PlaySound('test.wav', winsound.SND_FILENAME)

if __name__ == '__main__':
    cw = CW_Generator(samplerate=441000, wpm=25)
    signal = []
    signal.extend(cw.dit())
    signal.extend(cw.dit())
    signal.extend(cw.dah())
    cw.play(signal)
