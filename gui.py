from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from multiprocessing import Process, Queue
from threading import Thread, Lock
from time import sleep
from audio import *


# Load template file
Builder.load_file('template_gui.kv')

# Kivy system variables
Window.size = (800, 500) # Window size (x, y)


class EyeudioGUI(Widget):
    def __init__(self, **kwargs):
        super(EyeudioGUI, self).__init__(**kwargs)

    def _open_popup(self):
        pop = Popup(title='Eyeudio',
                    content=Label(text='More Info Here'),
                    size_hint=(None, None), size=(400, 400))
        pop.open()

    def _update_button(self, event):
        global status
        self.event = event
        if self.event == "click_eye_btn":
            if status["eye_on"]:
                self.ids.eye_btn.text = "OFF"
                status["eye_on"] = False
            else:
                self.ids.eye_btn.text = "ON"
                status["eye_on"] = True

        elif self.event == "click_lip_btn":
            if status["lip_on"]:
                self.ids.lip_btn.text = "OFF"
                status["lip_on"] = False
            else:
                self.ids.lip_btn.text = "ON"
                status["lip_on"] = True

        elif self.event == "click_aux_btn":
            if status["aux_on"]:
                self.ids.aux_btn.text = "OFF"
                status["aux_on"] = False
            else:
                self.ids.aux_btn.text = "ON"
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

    audio = Audio(q, None).start()
    app = Application()
    app.run()
