from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label

# Load template file
Builder.load_file('template_gui.kv')

# Kivy system variables
Window.size = (800, 500) # Window size (x, y)


class EyeudioGUI(Widget):
    def __init__(self, **kwargs):
        super(EyeudioGUI, self).__init__(**kwargs)
        self.eye_on = False # Status of Eye Tracking       (ON/OFF)
        self.lip_on = False # Status of Lip Reading        (ON/OFF)
        self.aux_on = True  # Status of Speech Recognition (ON/OFF)

    def _open_popup(self):
        pop = Popup(title='Eyeudio',
                    content=Label(text='More Info Here'),
                    size_hint=(None, None), size=(400, 400))
        pop.open()

    def _update_button(self, event):
        self.event = event
        if self.event == "click_eye_btn":
            if self.eye_on:
                self.ids.eye_btn.text = "OFF"
                self.eye_on = False
            else:
                self.ids.eye_btn.text = "ON"
                self.eye_on = True
        elif self.event == "click_lip_btn":
            if self.lip_on:
                self.ids.lip_btn.text = "OFF"
                self.lip_on = False
            else:
                self.ids.lip_btn.text = "ON"
                self.lip_on = True
        elif self.event == "click_aux_btn":    
            if self.aux_on:
                self.ids.aux_btn.text = "OFF"
                self.aux_on = False
            else:
                self.ids.aux_btn.text = "ON"
                self.aux_on = True


class Application(App):
    def build(self):
        return EyeudioGUI()


if __name__ == "__main__":
    Application().run()
