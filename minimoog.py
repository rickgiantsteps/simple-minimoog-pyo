from pyo import *

class MiniMoog(PyoObject):

    """
    Simulation of the classic MiniMoog synth. Its main components are the three oscillators
    and the low pass resonant filter.

    It's possible to interact with each part of the instrument:
    the three oscillators have a controllable base octave and can be detuned with the respective sliders,
    you can also choose the waveform of each oscillator.

    The sound can also be modified with the pitch (of all 3 oscs) 
    and mod (controls the frequency of the modulating LFO) wheels.

    The external input slider (if overload is set at 1) controls the amplitude of the output signal of the synth that gets fed back into
    the filter to create a distortion effect (overload).

    You can control the amount and type of noise via the NoiseMaker slider (choice between
    white and pink noise).

    The filter properties can also be modified as well as the Attack, Decay, Sustain
    and Release of the sound generated.
    With the Contour Amount slider you can choose to turn on the ADSR envelope for the cutoff
    frequency and select its amount.

    :Parent: :py:class:`PyoObject`

    :Args:

        overload : float, optional
            Switches on (value 1) or off (value 0) the external input knob that controls the volume of the
            main Output signal that is sent back to the input of the mixer. This can create an overload distortion effect.
            Defaults to 0 (off)

    >>> s = Server().boot()
    >>> s.setAmp(0.1)
    >>> myminimoog = MiniMoog()
    >>> myminimoog.ctrl()
    >>> myminimoog.out()
    >>> s.gui(locals())

    """

    def __init__(self, overload=0):

        super().__init__()

        self._overload = overload

        # initialize midi keyboard
        self._notes = Notein(poly=10, scale=1, mul=1)
        self._notes.keyboard()

        # create pitch control values
        # pitch bend wheel
        self._bend = Sig(1)
        # base octave of each oscillator
        self._osc1octave = Sig(1)
        self._osc2octave = Sig(1)
        self._osc3octave = Sig(1)
        # detune signals
        self._osc2detune = Sig(1)
        self._osc3detune = Sig(1)
        # onoff volume signals
        self._onoff1 = Sig(1)
        self._onoff2 = Sig(1)
        self._onoff3 = Sig(1)

        # initialize amplitude envelope (attack, decay, sustain, release)
        self._env = MidiAdsr(self._notes['velocity'], attack=.05, decay=.1, sustain=.4, release=1)

        # envelope to control the filter cutoff frequency and its slider
        self._filterenv = MidiAdsr(self._notes['velocity'], attack=.05, decay=.1, sustain=.4, release=1)
        self._contouramount = Sig(1)

        # modulating LFO, it multiplies the output of the filters as a modulation source
        self._lfof = Sig(1)
        self._modwheel = Sig(1)
        self._LFO = LFO(freq=self._lfof*self._modwheel, type=3, add=1)

        # creates the three oscillators used in the synth
        # (pitch controlled by the midi keyboard "self._notes['pitch']", pitch bend and the base octave of the osc)
        self._osc1 = LFO(freq=self._notes['pitch']*self._bend*self._osc1octave, mul=self._env*self._onoff1)
        self._osc2 = LFO(freq=self._notes['pitch']*self._bend*self._osc2octave-self._osc2detune, mul=self._env*self._onoff2)
        self._osc3 = LFO(freq=self._notes['pitch']*self._bend*self._osc3octave-self._osc3detune, mul=self._env*self._onoff3)

        # inserts a noise generator
        self._noisegen = NoiseMaker(self._env)

        # mixes all the generators and feeds them as input into the low pass resonant filter
        self._mixed1 = Mix([self._osc1, self._osc2, self._osc3, self._noisegen])
        self._ladderfilter1noadsr = MoogLP(self._mixed1, freq=1000, res=0, mul=0.1*(1-self._contouramount), add=0)
        self._ladderfilter1withadsrenvelope = MoogLP(self._mixed1, freq=self._filterenv*2500, res=0, mul=1*self._contouramount, add=0)

        # runs only if overload is turned off
        if self._overload == 0:

            # final output without overload
            self._output = Pan((self._ladderfilter1noadsr+self._ladderfilter1withadsrenvelope)*self._LFO)
            self._base_objs = self._output.getBaseObjects()

        # runs only if overload is turned on
        elif self._overload == 1:

            # exitinput is the output of the first filter 
            # this is then fed back into another filter to simulate the external input in the synth and its overload distortion effect
            self._exitinput = Pan((self._ladderfilter1noadsr+self._ladderfilter1withadsrenvelope)*self._LFO)
            self._mixed2 = Mix([self._osc1, self._osc2, self._osc3, self._noisegen, self._exitinput])
            self._ladderfilter2withadsrenvelope = MoogLP(self._mixed2, freq=self._filterenv*2500, res=0, mul=1*self._contouramount, add=0)
            self._ladderfilter2noadsr = MoogLP(self._mixed2, freq=1000, res=0, mul=0.1*(1-self._contouramount), add=0)

            # output of the final filter
            self._output = Pan((self._ladderfilter2noadsr+self._ladderfilter2withadsrenvelope)*self._LFO)
            self._base_objs = self._output.getBaseObjects()

        else:
            raise ValueError("Overload value can only be a 0 (off, default) or a 1 (on)")


    def ctrl(self):    
        self._osc1.ctrl(title = "OSC 1")
        self._osc2.ctrl(title = "OSC 2")
        self._osc3.ctrl(title = "OSC 3")
        self._bend.ctrl([SLMap(0.1,2,"lin","value",1)], title="Pitch Bend")
        self._lfof.ctrl([SLMap(0,10,"lin","value",0)], title = "Modulating LFO")
        self._modwheel.ctrl([SLMap(0,10,"lin","value",1)], title = "Mod Wheel")

        if self._overload == 1:
            self._exitinput.ctrl([SLMap(0,3,"lin","mul",0)], title="External Input")

        self._osc1octave.ctrl([SLMap(1,16,"lin","value",1,"int")], title="OSC 1 Octaves (1, 2, 4, 8, 16)")
        self._osc2octave.ctrl([SLMap(1,16,"lin","value",1,"int")], title="OSC 2 Octaves (1, 2, 4, 8, 16)")
        self._osc3octave.ctrl([SLMap(1,16,"lin","value",1,"int")], title="OSC 3 Octaves (1, 2, 4, 8, 16)")
        self._osc2detune.ctrl([SLMap(-7,7,"lin","value",0)], title="OSC 2 Detuner")
        self._osc3detune.ctrl([SLMap(-7,7,"lin","value",0)], title="OSC 3 Detuner")
        self._onoff1.ctrl([SLMap(0,10,"lin","value",1)], title="OSC 1 Volume")
        self._onoff2.ctrl([SLMap(0,10,"lin","value",1)], title="OSC 2 Volume")
        self._onoff3.ctrl([SLMap(0,10,"lin","value",1)], title="OSC 3 Volume")
        self._noisegen.ctrl()
        self._filterenv.ctrl(title="Filter Envelope")
        self._contouramount.ctrl([SLMap(0,1,"lin","value",0)], title="Contour Amount")
        self._env.ctrl(title="Sound Envelope")

        if self._overload == 0:
            self._ladderfilter1noadsr.ctrl([SLMap(0.1, 10, "log", "res", 0.1), SLMap(0.1, 32000, "log", "freq", 2000)])
        elif self._overload == 1:    
            self._ladderfilter2noadsr.ctrl([SLMap(0.1, 10, "log", "res", 0.1), SLMap(0.1, 32000, "log", "freq", 2000)])


    def play(self, dur=0, delay=0):
        self._LFO.play(dur, delay)
        self._modwheel.play(dur, delay)
        self._lfof.play(dur, delay)
        self._notes.play(dur, delay)
        self._env.play(dur, delay)
        self._filterenv.play(dur, delay)
        self._contouramount.play(dur, delay)
        self._bend.play(dur, delay)
        self._osc1octave.play(dur, delay)
        self._osc2octave.play(dur, delay)
        self._osc3octave.play(dur, delay)
        self._osc2detune.play(dur, delay)
        self._osc3detune.play(dur, delay)
        self._onoff1.play(dur, delay)
        self._onoff2.play(dur, delay)
        self._onoff3.play(dur, delay)
        self._noisegen.play(dur, delay)
        self._osc1.play(dur, delay)
        self._osc2.play(dur, delay)
        self._osc3.play(dur, delay)
        self._mixed1.play(dur, delay)
        self._ladderfilter1noadsr.play(dur, delay)
        self._ladderfilter1withadsrenvelope.play(dur, delay)
        if self._overload == 1:
            self._exitinput.play(dur, delay)
            self._mixed2.play(dur, delay)
            self._ladderfilter2noadsr.play(dur, delay)
            self._ladderfilter2withadsrenvelope.play(dur, delay)
        return super().play(dur, delay)

    def stop(self):
        self._LFO.stop()
        self._modwheel.stop()
        self._lfof.stop()
        self._notes.stop()
        self._env.stop()
        self._filterenv.stop()
        self._contouramount.stop()
        self._bend.stop()
        self._osc1octave.stop()
        self._osc2octave.stop()
        self._osc3octave.stop()
        self._osc1octave.stop()
        self._osc2octave.stop()
        self._osc3octave.stop()
        self._osc2detune.stop()
        self._osc3detune.stop()
        self._onoff1.stop()
        self._onoff2.stop()
        self._onoff3.stop()
        self._noisegen.stop()
        self._osc1.stop()
        self._osc2.stop()
        self._osc3.stop()
        self._mixed1.stop()
        self._ladderfilter1noadsr.stop()
        self._ladderfilter1withadsrenvelope.stop()
        if self._overload == 1:
            self._exitinput.stop()
            self._mixed2.stop()
            self._ladderfilter2noadsr.stop()
            self._ladderfilter2withadsrenvelope.stop()
        return super().stop()

    def out(self, chnl=0, inc=1, dur=0, delay=0):
        self._LFO.play(dur, delay)
        self._modwheel.play(dur, delay)
        self._lfof.play(dur, delay)
        self._notes.play(dur, delay)
        self._env.play(dur, delay)
        self._filterenv.play(dur, delay)
        self._contouramount.play(dur, delay)
        self._bend.play(dur, delay)
        self._osc1octave.play(dur, delay)
        self._osc2octave.play(dur, delay)
        self._osc3octave.play(dur, delay)
        self._osc1octave.play(dur, delay)
        self._osc2octave.play(dur, delay)
        self._osc3octave.play(dur, delay)
        self._osc2detune.play(dur, delay)
        self._osc3detune.play(dur, delay)
        self._onoff1.play(dur, delay)
        self._onoff2.play(dur, delay)
        self._onoff3.play(dur, delay)
        self._noisegen.play(dur, delay)
        self._osc1.play(dur, delay)
        self._osc2.play(dur, delay)
        self._osc3.play(dur, delay)
        self._mixed1.play(dur, delay)
        self._ladderfilter1noadsr.play(dur, delay)
        self._ladderfilter1withadsrenvelope.play(dur, delay)
        if self._overload == 1:
            self._exitinput.play(dur, delay)
            self._mixed2.play(dur, delay)
            self._ladderfilter2noadsr.play(dur, delay)
            self._ladderfilter2withadsrenvelope.play(dur, delay)
        return super().out(chnl, inc, dur, delay)


class NoiseMaker(PyoObject):

    """
    Noise generator. Lets you choose between White Noise (value 0), Pink Noise (value 1) or a combination of the two.

    :Parent: :py:class:`PyoObject`

    :Args:

        mul : float or PyoObject, optional
            Multiplies the value of the signal.
            Defaults to 1
        add : float or PyoObject, optional
            Adds a value to the signal.
            Defaults to 0.


    >>> s = Server().boot()
    >>> s.setAmp(0.1)
    >>> mynoisemaker = NoiseMakerg()
    >>> mynoisemaker.ctrl()
    >>> mynoisemaker.out()
    >>> s.gui(locals())

    """

    def __init__(self, mul=1, add=0):

        super().__init__(mul, add)

        self._mul = mul
        self._add = add

        # white and pink noise generators (mul controls the amplitude of the noise)
        self._noise1 = Noise(self._mul, self._add)
        self._noise2 = PinkNoise(self._mul, self._add)

        # the selector lets you mix and choose between the two types of noise
        self._selector = Selector([self._noise1, self._noise2])
        self._base_objs = self._selector.getBaseObjects()


    def ctrl(self):
        self._selector.ctrl([SLMap(0,10,"lin","mul",0), SLMap(0,1,"lin","voice",0)], title="Noise Generator slider (0=White, 1=Pink)")

    def play(self, dur=0, delay=0):
        self._noise1.play(dur, delay)
        self._noise2.play(dur, delay)
        return super().play(dur, delay)

    def stop(self):
        self._noise1.stop()
        self._noise1.stop()
        return super().stop()

    def out(self, chnl=0, inc=1, dur=0, delay=0):
        self._noise1.play(dur, delay)
        self._noise1.play(dur, delay)
        return super().out(chnl, inc, dur, delay)


if __name__ == "__main__":
    s = Server(sr=44100, nchnls=2, buffersize=512, duplex=1).boot()
    s.setAmp(0.1)
    myminimoog = MiniMoog(1)
    myminimoog.out()
    myminimoog.ctrl()
    s.gui(locals())