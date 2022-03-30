import time
import torch
import string
from espnet_model_zoo.downloader import ModelDownloader
from espnet2.bin.asr_inference import Speech2Text
import pysndfile
import osascript
import sounddevice as sd
import librosa
import subprocess
from scipy.io.wavfile import write

class Node(object):
    def __init__(self, name):
        self.name = name
        self.children = dict()

    def add_child(self, child_name):
        if child_name not in self.children.keys():
            self.children[child_name] = Node(child_name)
        return self.children[child_name]

    def add_terminal_child(self, child_name, function, has_arguments):
        if child_name not in self.children.keys():
            self.children[child_name] = TerminalNode(child_name, function, has_arguments)
        return self.children[child_name]

    def exist_child(self, child_name):
        return child_name in self.children.keys()

    def get_child(self, child_name):
        return self.children[child_name]

class TerminalNode(object):
    def __init__(self, name, function, has_arguments=False):
        self.name = name
        self.function_call = function
        self.has_arguments = has_arguments
        self.arguments = None

    def has_arguments(self):
        return self.has_arguments

    def add_arguments(self, arguments):
        self.arguments = arguments

    def call_command(self):
        if not self.has_arguments:
            globals()[self.function_call]()
        else:
            globals()[self.function_call](self.arguments)


class Tree(object):
    def __init__(self):
        self.root = Node('')
    def add_command(self, command):
        command_words = command[0].split(' ')
        function = command[1]
        has_arguments = command[2]
        temp = self.root
        for word in command_words:
            word = word.lower()
            if word == command_words[-1]:
                temp = temp.add_terminal_child(word, function, has_arguments)
            else:
                temp = temp.add_child(word)

    # return: Boolean, TerminalNode
    def check_command(self, command):
        command_words = command.split(' ')
        temp = self.root
        for i in range(len(command_words)):
            word = command_words[i]
            word = word.lower()
            if temp.exist_child(word):
                temp = temp.get_child(word)

                if isinstance(temp, TerminalNode):
                    break
            else:
                return False, None, None

        if not isinstance(temp, TerminalNode):
            return False, None, None
        else:
            if temp.has_arguments:
                return True, temp, ' '.join(command_words[i+1:])
            return True, temp, None


def turn_up_volume():
    code, out, err = osascript.run("output volume of (get volume settings)")
    if not err:
        new_volume = int(out) + 10
        if new_volume > 100:
            new_volume = 100
        osascript.run("set volume output volume {}".format(new_volume))
    code, out, err = osascript.run("output volume of (get volume settings)")
    print(out)

def turn_down_volume():
    code, out, err = osascript.run("output volume of (get volume settings)")
    if not err:
        new_volume = int(out) - 10
        if new_volume < 0:
            new_volume = 0
        osascript.run("set volume output volume {}".format(new_volume))
    code, out, err = osascript.run("output volume of (get volume settings)")
    print(out)

def turn_up_brightness(value):
    code, out, err = osascript.run("tell application \"Terminal\" \nset currentTab to do script (\"brightness {}\") \n end tell".format(value))
    if not err:
        print(out)
    else:
        print(err)

def set_volume(values):
    value = values[0]
    osascript.run("set volume output volume {}".format(value))
    code, out, err = osascript.run("output volume of (get volume settings)")
    print(out)

def text_normalizer(text):
    text = text.upper()
    return text.translate(str.maketrans('', '', string.punctuation))

def audio_process():
    global audio_start_flag
    test_tree = Tree()
    for command in command_list:
        test_tree.add_command(command)
    while True:
        fs = 44100  # Sample rate
        seconds = 5  # Duration of recording
        audio = 'output.wav'

        print('start recording')
        myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
        sd.wait()  # Wait until recording is finished
        write(audio, fs, myrecording)  # Save as WAV file
        speech, rate = librosa.load(audio, sr=16000)
        pysndfile.sndio.write('output_ds.wav', speech, rate=rate, format='wav', enc='pcm16')

        nbests = speech2text(speech)
        text, *_ = nbests[0]
        print(f"ASR hypothesis: {text_normalizer(text)}")

        tokens = text_normalizer(text)
        print(tokens)
        # valid, terminal, arguments = test_tree.check_command("TURN UP VOLUME")
        if tokens == 'START':
            audio_start_flag = True
        elif audio_start_flag:
            valid, terminal, arguments = test_tree.check_command(tokens)

            print(valid)
            print(terminal)
            print(arguments)
            if valid:
                if arguments is not None:
                    terminal.add_arguments(arguments)
                terminal.call_command()
            audio_start_flag = False
        else:
            print('audio flag is false, keep listening')


def is_open_command(tokens):
    return True if tokens[0] == 'OPEN' else False

def open_app(app):
    # TODO: find whether the app exists (using regex?)
    # TODO: multiple directories; check duplicate
    directory = '/Applications/'
    app = application_mapping[app]
    Proc = subprocess.Popen(['open', directory + app + '.app'])

def combine_str(tokens):
    result = ''
    for t in tokens[1:]:
        result += t.lower().capitalize()
        result += ' '
    return result[:-1]

def initialize_audio():
    lang = 'en'
    fs = 16000 #@param {type:"integer"}
    tag = 'Shinji Watanabe/spgispeech_asr_train_asr_conformer6_n_fft512_hop_length256_raw_en_unnorm_bpe5000_valid.acc.ave' #@param ["Shinji Watanabe/spgispeech_asr_train_asr_conformer6_n_fft512_hop_length256_raw_en_unnorm_bpe5000_valid.acc.ave", "kamo-naoyuki/librispeech_asr_train_asr_conformer6_n_fft512_hop_length256_raw_en_bpe5000_scheduler_confwarmup_steps40000_optim_conflr0.0025_sp_valid.acc.ave"] {type:"string"}
    d = ModelDownloader()
    global speech2text
    speech2text = Speech2Text(
        **d.download_and_unpack(tag),
        minlenratio=0.0,
        maxlenratio=0.0,
        ctc_weight=0.3,
        beam_size=10,
        batch_size=0,
        nbest=1
    )

    print('finish config audio model')
    command1 = ["turn up volume", "turn_up_volume", False]
    command2 = ["turn down volume", "turn_down_volume", False]
    command_list.append(command1)
    command_list.append(command2)
    command5 = ["set volume to", "set_volume", True]
    command3 = ["open", "open_app", True]
    command_list.append(command5)
    command_list.append(command3)
    print('start process')

command_list = []
audio_start_flag = False
application_mapping = {'CHROME': 'Google Chrome','MICROSOFT POWERPOINT': 'Microsoft PowerPoint', 'POWERPOINT': 'Microsoft PowerPoint', 'NOTION': 'Notion'}
speech2text = None
