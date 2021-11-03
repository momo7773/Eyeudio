import sounddevice as sd
import numpy
from scipy.io.wavfile import write
import scipy.io.wavfile as wav

# Sampling frequency
freq = 44100

# Recording duration
duration = 5

class Voice_Input(Input):
    def __init__(self):
        pass
    def get_audio(self):
        # initialize portaudio
        print('start recording')
        recording = sd.rec(int(duration * freq),
                   samplerate=freq, channels=1)

        # Record audio for the given number of seconds
        sd.wait()
        print('end recording')
        write("recording0.wav", freq, recording)
        print(recording.shape)
        return recording

input = Voice_Input()
input.get_audio()
