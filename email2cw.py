# -*- coding: cp1252 -*-
import math
import wave
import struct
import winsound
import StringIO
import imaplib
import re
from getpass import getpass

morsecode = {
    '!': '..--.',
    '"': '.-..-.',
    '$': '...-..-',
    '&': '.-...',
    "'": '.----.',
    '(': '-.--.',
    ')': '-.--.-',
    '+': '.-.-.',
    ',': '--..--',
    '-': '-....-',
    '.': '.-.-.-',
    '/': '-..-.',
    '0': '-----',
    '1': '.----',
    '2': '..---',
    '3': '...--',
    '4': '....-',
    '5': '.....',
    '6': '-....',
    '7': '--...',
    '8': '---..',
    '9': '----.',
    ':': '---...',
    ';': '-.-.-.',
    '=': '-...-',
    '?': '..--..',
    '@': '.--.-.',
    'A': '.-',
    'B': '-...',
    'C': '-.-.',
    'D': '-..',
    'E': '.',
    'F': '..-.',
    'G': '--.',
    'H': '....',
    'I': '..',
    'J': '.---',
    'K': '-.-',
    'L': '.-..',
    'M': '--',
    'N': '-.',
    'O': '---',
    'P': '.--.',
    'Q': '--.-',
    'R': '.-.',
    'S': '...',
    'T': '-',
    'U': '..-',
    'V': '...-',
    'W': '.--',
    'X': '-..-',
    'Y': '-.--',
    'Z': '--..',
    '\\': '-..-.',
    '`': '.----.',
    'a': '.-',
    'b': '-...',
    'c': '-.-.',
    'd': '-..',
    'e': '.',
    'f': '..-.',
    'g': '--.',
    'h': '....',
    'i': '..',
    'j': '.---',
    'k': '-.-',
    'l': '.-..',
    'm': '--',
    'n': '-.',
    'o': '---',
    'p': '.--.',
    'q': '--.-',
    'r': '.-.',
    's': '...',
    't': '-',
    'u': '..-',
    'v': '...-',
    'w': '.--',
    'x': '-..-',
    'y': '-.--',
    'z': '--..',
    '�': '.--.-',
    '�': '.--.-',
    '�': '.-',
    '�': '.-',
    '�': '.-.-',
    '�': '.--.-',
    '�': '.-.-',
    '�': '-.-..',
    '�': '..-..',
    '�': '..-..',
    '�': '.',
    '�': '.',
    '�': '..',
    '�': '..',
    '�': '..',
    '�': '..',
    '�': '..--.',
    '�': '--.--',
    '�': '---',
    '�': '---',
    '�': '---',
    '�': '---',
    '�': '---.',
    '�': '---.',
    '�': '..-',
    '�': '..-',
    '�': '..-',
    '�': '..--',
    '�': '-.--',
    '�': '.--..',
    '�': '...--..',
    '�': '.--.-',
    '�': '.--.-',
    '�': '.-',
    '�': '.-',
    '�': '.-.-',
    '�': '.--.-',
    '�': '.-.-',
    '�': '-.-..',
    '�': '..-..',
    '�': '..-..',
    '�': '.',
    '�': '.',
    '�': '..',
    '�': '..',
    '�': '..',
    '�': '..',
    '�': '..--.',
    '�': '--.--',
    '�': '---',
    '�': '---',
    '�': '---',
    '�': '---',
    '�': '---.',
    '�': '---.',
    '�': '..-',
    '�': '..-',
    '�': '..-',
    '�': '..--',
    '�': '-.--',
    '�': '.--..',
    '�': '-.--',
    }


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
            self.cache['dit'] = self.pack(cw_signal)
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
            self.cache['dah'] = self.pack(cw_signal)
        return self.cache['dah']

    def char_space(self):
        """Create a keyed signal for:
           silence for 2 dit durations
           (it's actually 3, but we remove the
           one duration included in each dit/dah)"""

        if 'char_space' not in self.cache:
            self.cache['char_space'] = self.pack([0] * 2 * self.dit_duration)
        return self.cache['char_space']

    def word_space(self):
        """Create a keyed signal for:
           silence for 6 dit durations
           (it's actually 7, but we remove the
           one duration included in each dit/dah)"""

        if 'word_space' not in self.cache:
            self.cache['word_space'] = self.pack([0] * 6 * self.dit_duration)
        return self.cache['word_space']

    def encode(self, text):
        """Encode text to cw signal"""
        signal = ''
        for word in text.split():
            for char in word:
                for d in morsecode[char]:
                    if d == '.':
                        signal += self.dit()
                    elif d == '-':
                        signal += self.dah()
                # End character with char_space:
                signal += self.char_space()
            # End word with word_space:
            signal += self.word_space()
        return signal
            
    def pack(self, signal):
        """Pack signal values into binary string"""
        packed_signal = ''
        for smpl in signal:
            packed_signal += struct.pack('h',smpl) # transform to binary
        return packed_signal

    def play(self, signal):
        """Save signal as a wave object and play it"""
        wavobj = StringIO.StringIO()
        wavfile = wave.open(wavobj, 'wb')
        wavfile.setparams((1, 2, self.samplerate, len(signal), 'NONE', 'noncompressed'))

        wavfile.writeframes(signal)
        wavfile.close()
        winsound.PlaySound(wavobj.getvalue(), winsound.SND_MEMORY)
        wavobj.close()

class EmailChecker:
    """Checks an e-mail account for new emails and retreives the headers"""

    def __init__(self, imapserver, user, pwd):
        """Initialize the connection to the IMAP server"""
        self.conn = imaplib.IMAP4_SSL(imapserver)
        self.conn.login(user, pwd)
        self.messages = {}

    def check(self, mailbox='INBOX'):
        """Checks for new messages in the mailbox, returns the headers"""
        
        newmessages = {}
        header_regexes = (re.compile(r'From:\s*(?P<name>.*?)\s*<(?P<email>.*?)>\s*$', re.M),
                          re.compile(r'Subject:\s*(?P<subject>.*?)\s*$', re.M),
                          re.compile(r'Date:\s*(?P<date>.*?)\s*$', re.M),
                          )

        self.conn.select(mailbox, readonly=True)
        try:
            res, data = self.conn.search(None, 'UNSEEN')
            msg_ids = data[0]
            for id in msg_ids.split():
                # Have we processed this message already?
                if id not in self.messages:
                    res, data = self.conn.fetch(id, '(BODY[HEADER.FIELDS (SUBJECT FROM DATE)])')
                    headerstr = data[0][1]
                    header = {}
                    for regex in header_regexes:
                        res = regex.search(headerstr)
                        if res:
                            header.update(res.groupdict())
                    newmessages[id] = header
        finally:
            self.conn.close()

        self.messages.update(newmessages)
        return newmessages

    def __del__(self):
        # Logout from the IMAP server:
        self.conn.logout()

if __name__ == '__main__':
    """
    cw = CW_Generator(samplerate=441000, wpm=25)
    signal = cw.encode('hello world')
    cw.play(signal)
    """
    imapserver = 'imap.gmail.com'
    user = raw_input('User name: ')
    pwd = getpass('Password: ')
    ec = EmailChecker(imapserver, user, pwd)
    print ec.check()
    print '----------------'
    # This should be empty (unless you got an e-mail just now):
    print ec.check()
