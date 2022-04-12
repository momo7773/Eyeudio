import time
import torch
import string
import speech_recognition as sr
#from espnet_model_zoo.downloader import ModelDownloader
#from espnet2.bin.asr_inference import Speech2Text
from kivy.clock import Clock
#import soundfile (M1)
#import pysndfile (Regular)
#import osascript
import sounddevice as sd
#import librosa
import subprocess
import threading
import queue
import pyautogui
#import keyboard
from syntax_checker import *
from scipy.io.wavfile import write



def text_normalizer(text):
    text = text.upper()
    return text.translate(str.maketrans('', '', string.punctuation))

class Audio(threading.Thread):
    def __init__(self, audio_q, command_q, audio_status_q, checker, other_arg, *args, **kwargs):
        self.audio_queue = audio_q
        self.command_queue = command_q
        self.other_arg = other_arg
        self.checker = checker
        self.audio_status_queue = audio_status_q
        self.recognizer = sr.Recognizer()

        #self.initialize_audio()

        super().__init__(*args, **kwargs)

    def run(self):
        global audio_start_flag
        global first
        global app
        while True:
            fs = 44100  # Sample rate
            seconds = 5  # Duration of recording
            audio = 'output.wav'

            print('start recording')
            with sr.Microphone() as source:
                myrecording = self.recognizer.listen(source, timeout = seconds)
            #myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
            #sd.wait()  # Wait until recording is finished

            #write(audio, fs, myrecording)  # Save as WAV file

            #speech, rate = librosa.load(audio, sr=16000)


            #pysndfile.sndio.write('output_ds.wav', speech, rate=rate, format='wav', enc='pcm16') (Regular)
            #soundfile.write('output_ds.wav', speech, rate) (M1)
            try:
                text = self.recognizer.recognize_google(myrecording, language='en-IN')
                #text, *_ = nbests[0]
                print(f"ASR hypothesis: {text}")

                self.audio_queue.put(text)
                if text == 'start':
                    audio_start_flag = True
                    self.audio_status_queue.put(True)
                    print('start, put into queue')
                elif audio_start_flag:
                    cmd = self.checker.execute_command(text)
                    if cmd is not None:
                        self.command_queue.put(cmd)
                    #audio_start_flag = False
                else:
                    print('audio flag is false, keep listening')
            except sr.UnknownValueError:
                print('Wait')


def combine_str(tokens):
    result = ''
    for t in tokens[1:]:
        result += t.lower().capitalize()
        result += ' '
    return result[:-1]

command_list = []
audio_start_flag = False
first = True
speech2text = None
