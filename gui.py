from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy import utils
from multiprocessing import Process, Queue
from threading import Thread, Lock
from time import sleep
from audio import *
from syntax_checker import *
# from lip_reading.start_lip_reading import start_lip_reading

# Load template file
Builder.load_file('template_gui.kv')

# Kivy system variables
Window.size = (800, 500) # Window size (x, y)


class WrappedLabel(Label):
    '''
        Kivy's Label with automatic word wrap
    '''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            width=lambda *x:
            self.setter('text_size')(self, (self.width, None)),
            texture_size=lambda *x: self.setter('height')(self, self.texture_size[1]))


class EyeudioGUI(Widget):
    '''
        Graphic User Interface screen for Eyeudio
    '''
    def __init__(self, **kwargs):
        super(EyeudioGUI, self).__init__(**kwargs)
        Clock.schedule_interval(self.update_lip_log, 1)

    def _open_popup(self):
        '''
            Open a popup when a user click on the "More Info" button
        '''
        pop = Popup(title='Eyeudio Project',
                    content=WrappedLabel(text='Authors: Hoang Nguyen, Yiqing Tao, Kanglan Tang, Jordan Wong, Yaowei Ma, Frank Cai, Vincent Wang, Ananth Goyal\n\nBy 2040, over 78 million people in the US are projected to experience hand mobility limitations such as Arthritis or Repetitive Strain Injury (RSI), which affect their ability to perform computer-related tasks. The Assistive Eyeudio Control Team is developing an affordable hands-free alternative for interacting with a computer. Eyeudio makes use of the camera and microphone on any common computer (i.e. laptop) to control the mouse cursor with eye-tracking while carrying out specific commands with lip reading and speech recognition.'),
                    size_hint=(None, None), size=(400, 400))
        pop.open()

    def update_audio_log(self, dt):
        global q
        if not q.empty():
            print('not empty, audio command adding')
            last_command = q.get(block = False)
            if self.ids.audio_text.text.count('\n') > 10:
                self.audio_text.text = ''
            self.ids.audio_text.text = self.ids.audio_text.text + '\n' + last_command
        else:
            print('audio log empty')

    def _update_button(self, event):
        '''
            Update the ON/OFF buttons and their color when the user click on
        '''
        global status
        self.event = event
        if self.event == "click_eye_btn":
            if status["eye_on"]:
                self.ids.eye_btn.text = "OFF"
                self.ids.eye_btn.background_color = utils.get_color_from_hex('#ED4E33')
                status["eye_on"] = False
            else:
                self.ids.eye_btn.text = "ON"
                self.ids.eye_btn.background_color = utils.get_color_from_hex('#00A598')
                status["eye_on"] = True

        elif self.event == "click_lip_btn":
            if status["lip_on"]:
                self.ids.lip_btn.text = "OFF"
                self.ids.lip_btn.background_color = utils.get_color_from_hex('#ED4E33')
                status["lip_on"] = False
            else:
                self.ids.lip_btn.text = "ON"
                self.ids.lip_btn.background_color = utils.get_color_from_hex('#00A598')
                status["lip_on"] = True

                # temporarily prints output to console
                lip_command, lip_words = start_lip_reading()
                print('lip command: ', lip_command)
                print('lip words: ', lip_words)

        elif self.event == "click_aux_btn":
            if status["aux_on"]:
                self.ids.aux_btn.text = "OFF"
                self.ids.aux_btn.background_color = utils.get_color_from_hex('#ED4E33')
                status["aux_on"] = False
            else:
                self.ids.aux_btn.text = "ON"
                self.ids.aux_btn.background_color = utils.get_color_from_hex('#00A598')
                status["aux_on"] = True

class Application(App):
    def build(self):
        return EyeudioGUI()


if __name__ == "__main__":
    status = {
        "eye_on": False,
        "lip_on": False,
        "aux_on": True
    }
    root_widget = None
    q = Queue()
    syntax_checker = Checker()

    def printOne():
        global status
        while True:
            if status["eye_on"]:
                print("Eye on")
                sleep(1)

    def printTwo():
        global status
        while True:
            if status["aux_on"]:
                print("Aux on")
                sleep(1)

    audio = Audio(q, syntax_checker, None).start()
    app = Application()
    app.run()
