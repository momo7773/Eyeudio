#@title Choose English ASR model { run: "auto" }
lang = 'en'
fs = 16000 #@param {type:"integer"}
tag = 'Shinji Watanabe/spgispeech_asr_train_asr_conformer6_n_fft512_hop_length256_raw_en_unnorm_bpe5000_valid.acc.ave' #@param ["Shinji Watanabe/spgispeech_asr_train_asr_conformer6_n_fft512_hop_length256_raw_en_unnorm_bpe5000_valid.acc.ave", "kamo-naoyuki/librispeech_asr_train_asr_conformer6_n_fft512_hop_length256_raw_en_bpe5000_scheduler_confwarmup_steps40000_optim_conflr0.0025_sp_valid.acc.ave"] {type:"string"}

import time
import torch
import string
from espnet_model_zoo.downloader import ModelDownloader
from espnet2.bin.asr_inference import Speech2Text
import librosa
import librosa.display
import subprocess
import sounddevice as sd
from scipy.io.wavfile import write
import osascript


import warnings
warnings.filterwarnings("ignore")

print("model setup...")
d = ModelDownloader()
# It may takes a while to download and build models

# using cpu
speech2text = Speech2Text(
    **d.download_and_unpack(tag),
    minlenratio=0.0,
    maxlenratio=0.0,
    ctc_weight=0.3,
    beam_size=10,
    batch_size=0,
    nbest=1
)
# device="cuda"
print("done.")

def text_normalizer(text):
    text = text.upper()
    return text.translate(str.maketrans('', '', string.punctuation))


def is_open_command(tokens):
    return True if tokens[0] == 'OPEN' else False

def is_stop(tokens):
	return True if tokens[0] == 'STOP' else False

def open_app(directory, app):
    # TODO: find whether the app exists (using regex?)
    # TODO: multiple directories; check duplicate
    
    Proc = subprocess.Popen(['open', directory + app + '.app'])
    
def combine_str(tokens):
    result = ''
    for t in tokens[1:]:
        result += t.lower().capitalize()
        result += ' '
    return result[:-1]


###########################################3
class Node(object):
    def __init__(self, name):
        self.name = name
        self.children = dict()
    
    def add_child(self, child_name):
        if child_name not in self.children.keys():
            self.children[child_name] = Node(child_name)
        return self.children[child_name]
    
    def add_terminal_child(self, child_name, function):
        if child_name not in self.children.keys():
            self.children[child_name] = TerminalNode(child_name, function)
        return self.children[child_name]
    
    def exist_child(self, child_name):
        return child_name in self.children.keys()
    
    def get_child(self, child_name):
        return self.children[child_name]

class TerminalNode(object):
    def __init__(self, name, function):
        self.name = name
        self.function_call = function
    def call_command(self):
        globals()[self.function_call]()
    
    
class Tree(object):
    def __init__(self):
        self.root = Node('')
    
    # input command format: ["command","function_to_call"]
        # "command": "open chrome" 'str' - all command are default set to lowercases
        # "function_to_call": the function name 'str'
    # command_words: list of command
    def add_command(self, command):
        command_words = command[0].split(' ')
        function = command[1]
        temp = self.root
        for word in command_words:
            word = word.lower()
            if word == command_words[-1]:
                temp = temp.add_terminal_child(word, function)
            else:
                temp = temp.add_child(word)

    # return: Boolean, TerminalNode
    def check_command(self, tokens):
        # command_words = command.split(' ')
        temp = self.root
        for word in tokens:
            word = word.lower()
            if temp.exist_child(word):
                temp = temp.get_child(word)
            else:
                return False, None
        if not isinstance(temp, TerminalNode):
            return False, None
        else:
            return True, temp



command_list = []
command1 = ["turn up volume", "turn_up_volume"]
command2 = ["turn down volume", "turn_down_volume"]
command3 = ["what can i say", "available_commands"]
command_list.append(command1)
command_list.append(command2)
command_list.append(command3)

# Test Turn on 
def turn_up_volume():
    code, out, err = osascript.run("output volume of (get volume settings)")
    if not err:
        new_volume = int(out) + 10
        if new_volume > 100:
            new_volume = 100
        osascript.run("set volume output volume {}".format(new_volume))
    code, out, err = osascript.run("output volume of (get volume settings)")
    print("current volume: ", out)
    
def turn_down_volume():
    code, out, err = osascript.run("output volume of (get volume settings)")
    if not err:
        new_volume = int(out) - 10
        if new_volume < 0:
            new_volume = 0
        osascript.run("set volume output volume {}".format(new_volume))
    code, out, err = osascript.run("output volume of (get volume settings)")
    print("current volume: ", out)

def available_commands():
	for c in command_list:
		print(c[0])
	print("open (app)")
	print("stop")

# build up tree
test_tree = Tree()
for command in command_list:
    test_tree.add_command(command)
#########################################################################3

fs = 44100  # Sample rate
seconds = 3  # Duration of recording
audio = 'output.wav'
directory = '/Applications/'

stop = False

while not stop:
	print("please type enter and then speak...")
	x = input()
	myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
	sd.wait()  # Wait until recording is finished
	print("start analyzing command...")
	write(audio, fs, myrecording)  # Save as WAV file

	speech, rate = librosa.load(audio, sr=16000)
	librosa.display.waveplot(speech, sr=rate)

	nbests = speech2text(speech)
	text, *_ = nbests[0]

	print(f"ASR model recognizes: {text_normalizer(text)}")

	tokens = text_normalizer(text).split()

	# print("tokens", tokens)
	if is_stop(tokens):
		break

	if is_open_command(tokens):
		open_app(directory, combine_str(tokens))
	else:
		valid, terminal = test_tree.check_command(tokens)
		# print("valid", valid)
		if valid:
			terminal.call_command()



