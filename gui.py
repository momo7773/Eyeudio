'''
    Usage: 
        1. Install Kivy dependencies: pip install requirements.txt
        2. Run GUI: python gui.py
'''

# General libraries
import os

# Kivy libraries
import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.lang import Builder
from kivy.properties import ListProperty

# Global variables
TITLE_SIZE = 30
BUTTON_FONT_SIZE = 20
BUTTON_SIZE = (.35,.2)
GREEN = (0,0.7,0,1)
BLACK = (0,0,0,1)

# Kivy system variables
Window.clearcolor = (1, 1, 1, 1) # Background Color (White)
Window.size = (600, 400) # Window size (x, y)


class ScreenManagement(ScreenManager):
    '''
        Initialization of the screen manager class to manage screens of GUI
    '''
    def __init__(self, **kwargs):
        super(ScreenManagement, self).__init__(**kwargs)


class MainMenu(Screen):
    '''
        Main Menu screen
    '''
    def __init__(self, **kwargs):
        super(MainMenu, self).__init__(**kwargs)

        # Image widget
        self.img = Image(source='images/logo.png', pos_hint={'x':.75, 'center_y':.85}, size_hint=(.25, .25))
        self.add_widget(self.img)

        # Label widget
        self.title = Label(text="Assistive Eyeudio Control GUI", font_size=TITLE_SIZE, color=BLACK, pos_hint={'x':.35, 'center_y':.85}, size_hint=(.125,.1))
        self.add_widget(self.title)

        # Button widget
        self.button = Button(text="Starting Eyeudio", font_size=BUTTON_FONT_SIZE, background_color=GREEN, pos_hint={'x':0.35, 'center_y': .1}, size_hint=BUTTON_SIZE)
        self.add_widget(self.button)
        self.button.bind(on_release=self.start_eyeudio)

    def start_eyeudio(self, *args):
        self.manager.current = 'Eyeudio'


class Eyeudio(Screen):
    '''
        Eyeudio screen
    '''
    def __init__(self, **kwargs):
        super(Eyeudio, self).__init__(**kwargs)

        # Label widget
        self.title = Label(text="Start Listening", font_size=TITLE_SIZE, color=BLACK, pos_hint={'x':.35, 'center_y':.85}, size_hint=(.125,.1))
        self.add_widget(self.title)

        # Button widget
        self.button = Button(text="Back", font_size=BUTTON_FONT_SIZE, background_color=GREEN, pos_hint={'x':0.35, 'center_y': .1}, size_hint=BUTTON_SIZE)
        self.add_widget(self.button)
        self.button.bind(on_release=self.go_back)

    def go_back(self, *args):
        self.manager.current = 'MainMenu'


class Application(App):
    '''
        Build all the Kivy screens
    '''
    def build(self):
        '''
            TODO: Add new screens here by sm.add_widget(NewScreenName(name='NewScreenName'))
        '''
        sm = ScreenManagement(transition=NoTransition())
        sm.add_widget(MainMenu(name='MainMenu'))
        sm.add_widget(Eyeudio(name='Eyeudio'))
        return sm


# Run the Graphic User Interface program
if __name__ == "__main__":
    Application().run()
