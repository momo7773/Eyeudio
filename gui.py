from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy import utils
from kivy.clock import Clock
from kivy.lang import Builder
from playsound import playsound
import platform
import time

import cv2
import argparse
import logging
import pathlib
import warnings
import torch
import numpy as np
import pyautogui
import atexit
import time

from multiprocessing import Process, Queue
from omegaconf import DictConfig, OmegaConf
from threading import Thread, Lock
from time import sleep, ctime
from collections import deque

# EYEUDIO IMPORTS =============================================
from audio import Audio
from syntax_checker import Checker
from lip_reading.start_lip_reading import start_lip_reading
from lip_reading.lip_preprocessing.record_and_crop_video import process_frame, initialize_lipreading_variables
from eyetracking.main import parse_args, load_mode_config
from eyetracking.demo import Demo
from eyetracking.utils import (check_path_all, download_dlib_pretrained_model,
                    download_ethxgaze_model, download_mpiifacegaze_model,
                    download_mpiigaze_model, expanduser_all,
                    generate_dummy_camera_params)

# Load template file
Builder.load_file('template_gui.kv')

# Kivy system variables
Window.size = (800, 500) # Window size (x, y)


RED = '#ED4E33'
GREEN = '#00A598'
SCROLLBAR = '#C1C1C1'


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


class WrappedButton(Button):
    '''
        Kivy's Button with automatic word wrap
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
        Attributes:
            current_lip_output (str): the sentence recognized by lip reading module
            current_audio_output (str): the sentence recognized by speech recognition module
            selected_audio (bool): whether the user select the lip reading prediction or speech recognition prediction (in the "Do you mean..." popup)
    '''
    cursor_position = StringProperty("X: 0 \nY: 0")

    def __init__(self, **kwargs):
        super(EyeudioGUI, self).__init__(**kwargs)
        Clock.schedule_interval(self._update_cursor_position, 1) # every second
        Clock.schedule_interval(self._update_log, 1)
        Clock.schedule_interval(self._update_audio_status, 0.5)
        Clock.schedule_interval(self._update_current_lip_output, 0.5)
        Clock.schedule_interval(self._update_current_audio_output, 0.5)
        Clock.schedule_interval(self._check_background_noise, 0.5)

        self.ids.computer_info.text = platform.system().upper()
        self.ids.camera_info.text = "AVAILABLE"
        self.ids.microphone_info.text = "AVAILABLE"
        self.ids.speaker_info.text = "AVAILABLE"

        self.current_lip_output = ''
        self.current_audio_output = ''
        self.selected_audio = True
        self.select_lip_btn = WrappedButton(text=self.current_lip_output, halign="center", font_size=20)
        self.select_audio_btn = WrappedButton(text=self.current_audio_output, halign="center", font_size=20)
        self.resetTime = -60


    def _check_background_noise(self, dt):
        if (Audio.background_noise_high):
            print("too high")
            Audio.background_noise_high = False
            if (STATUS["audio_on"] and time.time() > self.resetTime + 60):
                self._suggest_Input_Switch()
                self.resetTime =  time.time()
                #Audio.resetTime = time.time()


    def _update_cursor_position(self, dt):
        self.cursor_position = "X: {:.0f}\nY: {:.0f}".format(STATUS["x"], STATUS["y"])


    def _suggest_Input_Switch(self):
        
            #Open a popup when the audio exceeds a limit, prompting the user to switch speech recognition -> lip reading
        
        pop = Popup(title = 'Suggest Activating Lip Input',
                    content=WrappedLabel(text='The background audio level has exceeded the calibrated threshold for optimal speech recognition performace. Consider activating the lip-reading input.'),
                    size_hint=(None, None), size= (500, 500))
        pop.open()

    def _open_info_popup(self, *args):
        '''
            Open a popup when a user click on the "More Info" button
        '''
        info_popup = Popup(title='Eyeudio Application Help', title_size=(30), title_align='center', size_hint=(None, None), size=(400, 400))

        popup_content = {
            "blank0"          : WrappedLabel(text='', font_size=20),
            "help_start_title"  : WrappedLabel(text='Activate Assistive Technologies: ', bold=True, font_size=20, halign='center'),
            "blank1.0"          : WrappedLabel(text='', font_size=13),
            "help_start_audio"  : WrappedLabel(text='    \u2022  Speech Recognition: Say "Start Speech Recognition"', font_size=13, halign='left'),
            "help_start_lip"    : WrappedLabel(text='    \u2022  Lip Reading: Say "Start Lip Reading"', font_size=13, halign='left'),
            "help_start_eye"    : WrappedLabel(text='    \u2022  Eye Tracking: Say "Start Eye Tracking"', font_size=13, halign='left'),
            "blank1.1"          : WrappedLabel(text='', font_size=20),
            "help_stop_title"   : WrappedLabel(text='Deactivate Assistive Technologies: ', bold=True, font_size=20, halign='center'),
            "blank2.0"          : WrappedLabel(text='', font_size=13),
            "help_stop_audio"   : WrappedLabel(text='    \u2022  Speech Recognition: Say "Stop Speech Recognition"', font_size=13, halign='left'),
            "help_stop_lip"     : WrappedLabel(text='    \u2022  Lip Reading: Say "Stop Lip Reading"', font_size=13, halign='left'),
            "help_stop_eye"     : WrappedLabel(text='    \u2022  Eye Tracking: Say "Stop Eye Tracking"', font_size=13, halign='left'),
            "blank2.1"          : WrappedLabel(text='', font_size=20),
            "help_command_title": WrappedLabel(text='Supported Commands: ', bold=True, font_size=20, halign='center'),
            "blank3.0"            : WrappedLabel(text='', font_size=13),
            "help_commands"     : [
                WrappedLabel(text="    \u2022  turn up volume", font_size=13, halign='left'),
                WrappedLabel(text="    \u2022  turn down volume", font_size=13, halign='left'),
                WrappedLabel(text="    \u2022  single click", font_size=13, halign='left'),
                WrappedLabel(text="    \u2022  open new tab", font_size=13, halign='left'),
                WrappedLabel(text="    \u2022  next tab", font_size=13, halign='left'),
                WrappedLabel(text="    \u2022  open new window", font_size=13, halign='left'),
                WrappedLabel(text="    \u2022  open chrome", font_size=13, halign='left'),
                WrappedLabel(text="    \u2022  close chrome", font_size=13, halign='left'),
                WrappedLabel(text="    \u2022  close tab", font_size=13, halign='left'),
                WrappedLabel(text="    \u2022  larger", font_size=13, halign='left'),
                WrappedLabel(text="    \u2022  smaller", font_size=13, halign='left'),
                WrappedLabel(text="    \u2022  mute", font_size=13, halign='left'),
                WrappedLabel(text="    \u2022  pause", font_size=13, halign='left'),
                WrappedLabel(text="    \u2022  resume", font_size=13, halign='left'),
            ],
            "blank3.1"            : WrappedLabel(text='', font_size=20)
        }

        scroll_view = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            size=(1000, info_popup.size[1]),
            bar_color=utils.get_color_from_hex(SCROLLBAR),
            bar_width=12
        )

        layout = GridLayout(
            size_hint_y=None,
            cols=1,
            height=1000,
            width=scroll_view.size[1],
            row_default_height='20dp',
            row_force_default=True,
            spacing=(5, 5),
            padding=(0, 0)
        )

        for label_name, label_content in popup_content.items():
            if isinstance(label_content, list):
                for sublabel in label_content:
                    layout.add_widget(sublabel)
            else:
                layout.add_widget(label_content)

        scroll_view.add_widget(layout)
        info_popup.content = scroll_view
        info_popup.open()


    def _update_audio_status(self, dt, *args):
        global GUI_STATUS_QUEUE
        while not GUI_STATUS_QUEUE.empty():
            status_dict = GUI_STATUS_QUEUE.get()
            if 'audio' in status_dict:
                self._update_button('click_audio_btn')
            if 'eye_tracking' in status_dict:
                self._update_button('click_eye_btn')
            if 'lip_reading' in status_dict:
                self._update_button('click_lip_btn')

    def _update_current_lip_output(self, dt, *args):
        global LIP_QUEUE
        if not LIP_QUEUE.empty():
            self.current_lip_output = LIP_QUEUE.get()
            self.select_lip_btn.text = self.current_lip_output

    def _update_current_audio_output(self, dt, *args):
        global AUDIO_QUEUE
        if not AUDIO_QUEUE.empty():
            self.current_audio_output = AUDIO_QUEUE.get()
            self.select_audio_btn.text = self.current_audio_output

    def _update_text(self, module_text, last_command, *args):
        command_text = Label(text=last_command, halign="center", font_size=16, color=(0,0,0,1))
        module_text.add_widget(command_text)

    def _update_log(self, dt, *args):
        global COMMAND_QUEUE, STATUS
        if not COMMAND_QUEUE.empty():
            last_command = COMMAND_QUEUE.get(block=False)
            print('command queue not empty, {}'.format(last_command))
            # TODO: Double check the logic, might be incorrect.
            if STATUS["audio_on"] and not STATUS["lip_on"]:
                self._update_text(module_text=self.ids.audio_text, last_command=last_command)

            elif STATUS["lip_on"] and not STATUS["audio_on"]:
                self._update_text(module_text=self.ids.lip_text, last_command=last_command)

            elif STATUS["lip_on"] and STATUS["audio_on"]:
                if self.selected_audio:
                    self._update_text(module_text=self.ids.audio_text, last_command=last_command)
                else:
                    self._update_text(module_text=self.ids.lip_text, last_command=last_command)

    def _open_please_wait_popup(self, *args):
        '''
            Open a popup telling the user to wait for lip reading to finish processing
        '''
        box = BoxLayout(orientation='vertical', padding=(10))
        box.add_widget(Label(text="Lip reading in progress!", font_size=30))

        self.please_wait_popup = Popup(title='Please wait!', title_size=(30), title_align='center', content=box, size_hint=(None, None), size=(400, 400))
        self.please_wait_popup.open()

        self.select_lip_btn_updater = Clock.schedule_interval(self._update_select_lip_btn, 0.5)

    def _update_select_lip_btn(self, *args):
        '''
            Dismiss the Please Wait popup and open do you mean popup with the lip button 
        '''
        if self.current_lip_output:
            self.please_wait_popup.dismiss()
            self.select_lip_btn_updater.cancel()
            self._open_do_you_mean_popup()

    def _open_do_you_mean_popup(self, *args):
        '''
            Open a popup to ask the user to select between speech recognition or lip reading output
        '''
        box = BoxLayout(orientation='vertical', padding=(10))
        self.select_lip_btn = WrappedButton(text=self.current_lip_output, halign="center", font_size=20)
        self.select_audio_btn = WrappedButton(text=self.current_audio_output, halign="center", font_size=20)
        box.add_widget(self.select_lip_btn)
        self.select_lip_btn.bind(on_release=self._select_lip)

        box.add_widget(Label(text="or", font_size=30))

        box.add_widget(self.select_audio_btn)
        self.select_audio_btn.bind(on_release=self._select_audio)

        self.do_you_mean_popup = Popup(title='Do you mean ...', title_size=(30), title_align='center', content=box, size_hint=(None, None), size=(400, 400))
        self.do_you_mean_popup.open()

    def _select_lip(self, *args):
        global CHECKER, COMMAND_QUEUE

        self.selected_audio = False

        # Send lip output to syntax checker and update COMMAND_QUEUE
        cmd = CHECKER.execute_command(self.current_lip_output)
        if cmd is not None:
            COMMAND_QUEUE.put(cmd)

        # Clear button content and close popup
        self.current_lip_output = ''
        self.current_audio_output = ''
        self.select_lip_btn.text = ''
        self.select_audio_btn.text = ''
        self.do_you_mean_popup.dismiss()

    def _select_audio(self, *args):
        global CHECKER, COMMAND_QUEUE

        self.selected_audio = True

        # Send audio output to syntax checker and update COMMAND_QUEUE
        cmd = CHECKER.execute_command(self.current_audio_output)
        if cmd is not None:
            COMMAND_QUEUE.put(cmd)

        # Clear button content and close popup
        self.current_lip_output = ''
        self.current_audio_output = ''
        self.select_lip_btn.text = ''
        self.select_audio_btn.text = ''
        self.do_you_mean_popup.dismiss()

    def _update_button(self, event, *args):
        '''
            Update the ON/OFF buttons and their color when the user click on
        '''
        global STATUS, LIP_QUEUE, AUDIO_QUEUE, COMMAND_QUEUE, CHECKER
        self.event = event

        # Check for eye button click event
        if self.event == "click_eye_btn":
            # Turn eye button off event
            if STATUS["eye_on"]:
                self.ids.eye_status.text = "OFF"
                self.ids.eye_status.color = utils.get_color_from_hex(RED)

                self.ids.eye_btn.text = "TURN ON"
                self.ids.eye_btn.background_color = utils.get_color_from_hex(GREEN)

                STATUS["eye_on"] = False

            # Turn eye button on event
            else:
                self.ids.eye_status.text = "ON"
                self.ids.eye_status.color = utils.get_color_from_hex(GREEN)

                self.ids.eye_btn.text = "TURN OFF"
                self.ids.eye_btn.background_color = utils.get_color_from_hex(RED)

                STATUS["eye_on"] = True

        # Check for lip button click event
        elif self.event == "click_lip_btn":
            # Turn lip button off event, start recognize lip command
            if STATUS["lip_on"]:
                self.ids.lip_status.text = "OFF"
                self.ids.lip_status.color = utils.get_color_from_hex(RED)

                self.ids.lip_btn.text = "RECORD"
                self.ids.lip_btn.background_color = utils.get_color_from_hex(GREEN)

                # Change lip status to OFF and stop cropping thread
                STATUS["lip_on"] = False

                # Start Deep Lip Reading
                STATUS["start_dlr"] = True

                # If speech recognition is already on, open popup to ask user to choose
                if STATUS["audio_on"]:
                    self._open_please_wait_popup()

                # If speech recognition is NOT already on, send output to syntax checker
                else:
                    # Syntax check raw lip reading output
                    self.lip_command_queue_updater = Clock.schedule_interval(self._update_lip_command_queue, 1)

            # Turn lip button on event, start cropping
            else:
                initialize_lipreading_variables() # reinitialize the start lip vars (clear deque) before cropping

                # Clear lip and audio queue
                while not LIP_QUEUE.empty():
                    LIP_QUEUE.get()
                if STATUS["audio_on"]:
                    while not AUDIO_QUEUE.empty():
                        AUDIO_QUEUE.get()

                self.ids.lip_status.text = "ON"
                self.ids.lip_status.color = utils.get_color_from_hex(GREEN)

                self.ids.lip_btn.text = "STOP"
                self.ids.lip_btn.background_color = utils.get_color_from_hex(RED)

                # If speech recognition is already on, stop updating the audio command queue so that the command is not executed immediately
                if STATUS["audio_on"]:
                    self.audio_command_queue_updater.cancel()

                # Change lip status to ON and start cropping thread
                STATUS["lip_on"] = True

        # Check for audio button click event
        elif self.event == "click_audio_btn":
            # Turn audio button off event
            if STATUS["audio_on"]:
                self.ids.audio_status.text = "OFF"
                self.ids.audio_status.color = utils.get_color_from_hex(RED)

                self.ids.audio_btn.text = "TURN ON"
                self.ids.audio_btn.background_color = utils.get_color_from_hex(GREEN)

                STATUS["audio_on"] = False
                Audio.audio_start_flag = False

                self.current_audio_output = ''
                # self.audio_command_queue_updater.cancel()

            # Turn audio button on event
            else:
                # Clear audio queue
                while not AUDIO_QUEUE.empty():
                    AUDIO_QUEUE.get()

                self.ids.audio_status.text = "ON"
                self.ids.audio_status.color = utils.get_color_from_hex(GREEN)

                self.ids.audio_btn.text = "TURN OFF"
                self.ids.audio_btn.background_color = utils.get_color_from_hex(RED)

                STATUS["audio_on"] = True
                Audio.audio_start_flag = True

                # If lip reading is already on, open popup to ask user to choose
                if STATUS["lip_on"]:
                    initialize_lipreading_variables() # reinitialize the start lip vars (clear deque) before cropping

                    # Clear lip queue
                    while not LIP_QUEUE.empty():
                        LIP_QUEUE.get()

                # If lip reading is NOT already on, send output to syntax checker
                else:
                    self.audio_command_queue_updater = Clock.schedule_interval(self._update_audio_command_queue, 1)

    def _update_lip_command_queue(self, *args):
        global CHECKER, COMMAND_QUEUE
        if self.current_lip_output:
            cmd = CHECKER.execute_command(self.current_lip_output)
            if cmd is not None:
                COMMAND_QUEUE.put(cmd)
            self.lip_command_queue_updater.cancel()
            self.current_lip_output = ''

    def _update_audio_command_queue(self, *args):
        global CHECKER, COMMAND_QUEUE
        if self.current_audio_output:
            cmd = CHECKER.execute_command(self.current_audio_output)
            if cmd is not None:
                COMMAND_QUEUE.put(cmd)
            self.audio_command_queue_updater.cancel()
            self.current_audio_output = ''


class Application(App):
    def build(self):
        return EyeudioGUI()


STATUS = {
    "eye_on": False,
    "lip_on": False,
    "start_dlr": False,
    "audio_on": False,
    "x": 0,
    "y": 0
}

COMMAND_QUEUE = Queue() # queue for syntax checked commands
AUDIO_QUEUE = Queue() # speech recognition queue to be used for popup suggestion
LIP_QUEUE = Queue() # lip reading queue to be used for popup suggestion
GUI_STATUS_QUEUE = Queue()
CHECKER = Checker() # syntax checker for lip reading and speech recognition
lock = Lock() # eyetracker for priority
lip_reading_deque = deque(maxlen=4) # 4 is an arbitrary max number of raw frames to keep prior to cropping (which is slow)

# eyetracking task 1
def eye_tracker(args, lip_reading_deque):
    global face_eye
    lock.acquire()
    config = load_mode_config(args)
    expanduser_all(config)
    if config.gaze_estimator.use_dummy_camera_params:
        generate_dummy_camera_params(config)
    OmegaConf.set_readonly(config, True)

    if config.face_detector.mode == 'dlib':
        download_dlib_pretrained_model()
    if args.mode:
        if config.mode == 'MPIIGaze':
            download_mpiigaze_model()
        elif config.mode == 'MPIIFaceGaze':
            download_mpiifacegaze_model()
        elif config.mode == 'ETH-XGaze':
            download_ethxgaze_model()

    check_path_all(config)
    face_eye = Demo(config)
    lock.release()
    face_eye.run(lip_reading_deque)

# eyetracking task 2
def eye_cursor():
    screenWidth, screenHeight = pyautogui.size() # Get the size of the primary monitor.
    currentMouseX, currentMouseY = pyautogui.position()
    sleep(1) # make sure work1 can get the lock first to init the face_eye
    lock.acquire()
    global face_eye
    CALIBRATION_INTERVAL = 4 # change this interval
    CURSOR_INTERVAL = 1.5
    lock.release()

    # TODO: add a while loop so user can recalibrate
    while True:
        # first four results is used to calibration
        x_right, x_left, y_up, y_down = 0, 0, 0, 0
        # min     max     min     max


        #sleep here, check the switch every half second.
        global STATUS
        while STATUS["eye_on"] is not True:
            sleep(0.5)

        iteration = 0
        while True:
            if iteration == 0:
                playsound('.\\eyetracking\\calibration_start.mp3')
            x = 0
            y = 0
            for res in face_eye.gaze_estimator.results:
                x += res[0]
                y += res[1]
            if len(face_eye.gaze_estimator.results) == 0:
                sleep(CURSOR_INTERVAL)
                continue

            array = np.array(face_eye.gaze_estimator.results)
            # preprocesing:
            arr = np.array(array)
            logical_arr = np.abs(arr - np.mean(arr, axis=0)) < np.std(arr, axis=0)
            filtered_arr = arr[logical_arr]
            if len(filtered_arr) == 0:
                sleep(CURSOR_INTERVAL)
                continue
            x /= -len(filtered_arr) # change sign (right should be larger than left)
            y /= len(filtered_arr)

            # calibration
            if iteration == 0:
                print("------------------- Look Upper-left -------------------")
                playsound('.\\eyetracking\\upperleft.mp3')
                sleep(CALIBRATION_INTERVAL)
                iteration += 1
                continue
            if iteration == 1: # upper-left
                x_left += x
                y_up += y
                print("------------------- Then Look Upper-right -------------------")
                playsound('.\\eyetracking\\upperright.mp3')
                sleep(CALIBRATION_INTERVAL)
                iteration += 1
                continue
            elif iteration == 2: # upper-right
                x_right += x
                y_up += y
                print("------------------- Then Look lower-right -------------------")
                playsound('.\\eyetracking\\lowerright.mp3')
                sleep(CALIBRATION_INTERVAL)
                iteration += 1
                continue
            elif iteration == 3: # lower-right
                x_right += x
                y_down += y
                print("------------------- Then Look lower-left -------------------")
                playsound('.\\eyetracking\\lowerleft.mp3')
                sleep(CALIBRATION_INTERVAL)
                iteration += 1
                continue
            elif iteration == 4: # lower-left
                x_left += x
                y_down += y
                print("-------------------------------------- Finished --------------------------------------")
                sleep(CALIBRATION_INTERVAL)
                iteration += 1
                continue
            elif iteration == 5:
                x_right, x_left, y_up, y_down = x_right / 2, x_left / 2, y_up / 2, y_down / 2
                print("\nFinished calibration: \n x_right {}, \n x_left {}, \n y_up {}, \n y_down {}".format(x_right, x_left, y_up, y_down))

            if STATUS["eye_on"]:
                # scale x and y
                x = (x - x_left) / (x_right - x_left) * (screenWidth)
                y = (y - y_up) / (y_down - y_up) * (screenHeight)
                print("\n x:{}   y: {}".format(x, y))
                STATUS["x"] = x
                STATUS["y"] = y

                if x <= 0:
                    x = 1
                if x >= screenWidth:
                    x = screenWidth - 1
                if y <= 0:
                    y = 1
                if y >= screenHeight:
                    y = screenHeight - 1

                pyautogui.moveTo(x, y) # x, y  positive number

                sleep(CURSOR_INTERVAL)
                iteration += 1
            else:
                break

#### --- Speech Recognition --- ####
AUDIO = Audio(audio_q=AUDIO_QUEUE, command_q=COMMAND_QUEUE, audio_status_q=GUI_STATUS_QUEUE, checker=CHECKER).start()

#### --- Eye Tracking --- ####
args = parse_args()
task_eye_tracker = Thread(target=eye_tracker, args=(args,lip_reading_deque,))
task_eye_tracker.start()

task_eye_cursor = Thread(target=eye_cursor, args=())
task_eye_cursor.start()

#### --- Lip Reading --- ####
# lipreading task 1 (cropping)
def process_lip_frame_loop(lip_reading_deque):
    global STATUS
    while True:
        # only process_frame if lipreading is on, and there exists a frame to process
        if STATUS["lip_on"] and (len(lip_reading_deque) > 0):
            process_frame(lip_reading_deque)
            # print("lip processing frame") # debugging
        else:
            time.sleep(0.2) # arbitrary time to wait if no frame to pop

# lipreading task 2 (recognizing)
def recognize_lip_frame_loop():
    global STATUS, LIP_QUEUE
    while True:
        if STATUS["start_dlr"]:
            try:
                lip_sentence, lip_words = start_lip_reading()
                LIP_QUEUE.put(lip_sentence)
            except:
                lip_sentence, lip_words = '', ''
            print("Lipreading Output: ", lip_sentence)
            STATUS["start_dlr"] = False
        else:
            time.sleep(0.2) # arbitrary time to wait

task_process_lip_frames = Thread(target=process_lip_frame_loop, args=(lip_reading_deque,))
task_process_lip_frames.start()

task_recognize_lip_frames = Thread(target=recognize_lip_frame_loop)
task_recognize_lip_frames.start()

app = Application()
app.run()

# def exit_handler():
#     cv2.destroyAllWindows()
# atexit.register(exit_handler)
