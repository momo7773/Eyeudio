import string
import speech_recognition as sr
import threading
from fuzzywuzzy import fuzz
# from gui import STATUS


def text_normalizer(text):
    text = text.upper()
    return text.translate(str.maketrans('', '', string.punctuation))

class Audio(threading.Thread):

    audio_start_flag = False

    def __init__(self, audio_q, command_q, audio_status_q, checker, *args, **kwargs):
        self.audio_queue = audio_q
        self.command_queue = command_q
        self.checker = checker
        self.audio_status_queue = audio_status_q
        self.recognizer = sr.Recognizer()
        # schedule.every(1).seconds.do(interact_module, job)

        #self.initialize_audio()

        super().__init__(*args, **kwargs)

    # def interact_module():
    #     audio_start_flag = STATUS['audio_on']

    def run(self):
        global first
        global app
        while True:
            fs = 44100  # Sample rate
            seconds = 5  # Duration of recording
            audio = 'output.wav'

            print('start recording')
            with sr.Microphone() as source:
                myrecording = self.recognizer.listen(source, phrase_time_limit = seconds)

            try:
                text = self.recognizer.recognize_google(myrecording, language='en-IN')
                #text, *_ = nbests[0]
                print(f"ASR hypothesis: {text}")

                self.audio_queue.put(text)
                if  fuzz.partial_ratio('start speech recognition', text) >= 80:
                    Audio.audio_start_flag = True
                    self.audio_status_queue.put({'audio': True})
                    print('start, put into queue')
                elif fuzz.partial_ratio('start lip reading', text) >= 80:
                    self.audio_status_queue.put({'lip_reading': True})
                elif fuzz.partial_ratio('start eye tracking', text) >= 80:
                    self.audio_status_queue.put({'eye_tracking': True})
                elif fuzz.partial_ratio('stop speech recognition', text) >= 80:
                    Audio.audio_start_flag = False
                    self.audio_status_queue.put({'audio': False})
                    print('stop putting text into queue')
                elif fuzz.partial_ratio('stop lip reading', text) >= 80:
                    self.audio_status_queue.put({'lip_reading': False})
                elif fuzz.partial_ratio('stop eye tracking', text) >= 80:
                    self.audio_status_queue.put({'eye_tracking': False})
                elif Audio.audio_start_flag:
                    cmd = self.checker.execute_command(text)
                    if cmd is not None:
                        self.command_queue.put(cmd)
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
first = True
speech2text = None
