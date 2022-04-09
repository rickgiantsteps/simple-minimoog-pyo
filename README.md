# simple-minimoog-pyo
Simple MiniMoog synth emulator made with python's Pyo library (http://ajaxsoundstudio.com/software/pyo/).
Its main components are the three oscillators and the low pass resonant filter.

It's possible to interact with each part of the instrument: the three oscillators have a controllable base octave and can be detuned with the respective sliders, you can also choose the waveform of each oscillator.
The sound can also be modified with the pitch (of all 3 oscs) and mod (controls the frequency of the modulating LFO) wheels.

The external input slider (if overload is set at 1) controls the amplitude of the output signal of the synth that gets fed back intothe filter to create a distortion effect (overload).
You can control the amount and type of noise via the NoiseMaker slider (choice between white and pink noise).

The filter properties can also be modified as well as the Attack, Decay, Sustain and Release of the sound generated.
With the Contour Amount slider you can choose to turn on the ADSR envelope for the cutoff frequency and select its amount.

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
