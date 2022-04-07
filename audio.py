# import time
# import torch
# import string
# from espnet_model_zoo.downloader import ModelDownloader
# from espnet2.bin.asr_inference import Speech2Text
# from kivy.clock import Clock
# import pysndfile
# import osascript
# import sounddevice as sd
# import librosa
# import subprocess
# import threading
# import queue
# import pyautogui
# import keyboard
# from syntax_checker import *
# from scipy.io.wavfile import write



# def text_normalizer(text):
#     text = text.upper()
#     return text.translate(str.maketrans('', '', string.punctuation))

# class Audio(threading.Thread):
#     def __init__(self, q, checker, other_arg, *args, **kwargs):
#         self.queue = q
#         self.other_arg = other_arg
#         self.checker = checker
#         self.initialize_audio()
#         super().__init__(*args, **kwargs)

#     def initialize_audio(self):
#         lang = 'en'
#         fs = 16000 #@param {type:"integer"}
#         tag = 'Shinji Watanabe/librispeech_asr_train_asr_transformer_e18_raw_bpe_sp_valid.acc.best' #@param ["Shinji Watanabe/spgispeech_asr_train_asr_conformer6_n_fft512_hop_length256_raw_en_unnorm_bpe5000_valid.acc.ave", "kamo-naoyuki/librispeech_asr_train_asr_conformer6_n_fft512_hop_length256_raw_en_bpe5000_scheduler_confwarmup_steps40000_optim_conflr0.0025_sp_valid.acc.ave"] {type:"string"}
#         add_new_tab()
#         print('downloading')
#         d = ModelDownloader()
#         global speech2text
#         speech2text = Speech2Text(
#             **d.download_and_unpack(tag),
#             minlenratio=0.0,
#             maxlenratio=0.0,
#             ctc_weight=0.3,
#             beam_size=10,
#             batch_size=0,
#             nbest=1
#         )

#         print('finish config audio model')

#     def run(self):
#         global audio_start_flag
#         global first
#         global app
#         while True:
#             fs = 44100  # Sample rate
#             seconds = 5  # Duration of recording
#             audio = 'output.wav'

#             print('start recording')
#             myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
#             sd.wait()  # Wait until recording is finished
#             write(audio, fs, myrecording)  # Save as WAV file
#             speech, rate = librosa.load(audio, sr=16000)
#             pysndfile.sndio.write('output_ds.wav', speech, rate=rate, format='wav', enc='pcm16')

#             nbests = speech2text(speech)
#             text, *_ = nbests[0]
#             print(f"ASR hypothesis: {text_normalizer(text)}")

#             tokens = text_normalizer(text)
#             self.queue.put(tokens)
#             if tokens == 'START':
#                 audio_start_flag = True
#             elif audio_start_flag:
#                 self.checker.execute_command(tokens)
#                 audio_start_flag = False
#             else:
#                 print('audio flag is false, keep listening')


# def combine_str(tokens):
#     result = ''
#     for t in tokens[1:]:
#         result += t.lower().capitalize()
#         result += ' '
#     return result[:-1]

# command_list = []
# audio_start_flag = False
# first = True
# speech2text = None
