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
from kivy.uix.button import Button
from kivy import utils
from kivy.clock import Clock

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
from lip_reading.lip_preprocessing.record_and_crop_video import process_frame, initialize_lipreading_variables #lip_reading uncomment
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
        Clock.schedule_interval(self.update_cursor_position, 1) # every second
        Clock.schedule_interval(self._update_audio_status, 0.5)
        Clock.schedule_interval(self._update_log, 1)

        self.current_lip_output = ''
        self.current_audio_output = ''
        self.selected_audio = True

    def update_cursor_position(self, dt):
        self.cursor_position = "X: {:.0f}\nY: {:.0f}".format(STATUS["x"], STATUS["y"])

    def _open_info_popup(self, *args):
        '''
            Open a popup when a user click on the "More Info" button
        '''
        info_popup = Popup(title='Eyeudio Application Help', title_size=(30), title_align='center',
                           content=WrappedLabel(text='Activate Speech Recognition: Say "Start Speech Recognition"\nActivate Lip Reading: Say "Start Lip Reading"\nActivate Eye Tracking: Say "Start Eye Tracking"\n',
                                                font_size=14),
                           size_hint=(None, None), size=(400, 400))
        info_popup.open()

    def _update_audio_status(self, dt, *args):
        global AUDIO_STATUS_QUEUE
        if (not AUDIO_STATUS_QUEUE.empty()):
            AUDIO_STATUS_QUEUE.get()
            self._update_button('click_audio_btn')
        

    def _update_text(self, module_text, last_command, *args):
        if module_text.text.count('\n') > 10:
            module_text.text = ''
        module_text.text += f'\n{last_command}'

    def _update_log(self, dt, *args):
        global COMMAND_QUEUE, STATUS
        if not COMMAND_QUEUE.empty():
            last_command = COMMAND_QUEUE.get(block=False)
            print('command queue not empty, {}'.format(last_command))

            if STATUS["audio_on"] and not STATUS["lip_on"]:
                self._update_text(module_text=self.ids.audio_text, last_command=last_command)

            elif STATUS["lip_on"] and not STATUS["audio_on"]:
                self._update_text(module_text=self.ids.lip_text, last_command=last_command)

            elif STATUS["lip_on"] and STATUS["audio_on"]:
                if self.selected_audio:
                    self._update_text(module_text=self.ids.audio_text, last_command=last_command)
                else:
                    self._update_text(module_text=self.ids.lip_text, last_command=last_command)

    def _open_do_you_mean_popup(self, *args):
        '''
            Open a popup to ask the user to select between speech recognition or lip reading output
        '''
        box = BoxLayout(orientation='vertical', padding=(10))
        btn_lip = WrappedButton(text=self.current_lip_output, halign="center", font_size=20)
        box.add_widget(btn_lip)
        btn_lip.bind(on_release=self._select_lip)

        box.add_widget(Label(text="or", font_size=30))

        btn_audio = WrappedButton(text=self.current_audio_output, halign="center", font_size=20)
        box.add_widget(btn_audio)
        btn_audio.bind(on_release=self._select_audio)

        self.do_you_mean_popup = Popup(title='Do you mean ...', title_size=(30), title_align='center', content=box, size_hint=(None, None), size=(400, 400))
        self.do_you_mean_popup.open()

    def _select_lip(self, *args):
        global CHECKER, COMMAND_QUEUE

        self.selected_audio = False

        # Send lip output to syntax checker and update COMMAND_QUEUE
        cmd = CHECKER.execute_command(self.current_lip_output)
        if cmd is not None:
            COMMAND_QUEUE.put(cmd)

        # Close popup
        self.do_you_mean_popup.dismiss()

    def _select_audio(self, *args):
        global CHECKER, COMMAND_QUEUE

        self.selected_audio = True

        # Send audio output to syntax checker and update COMMAND_QUEUE
        cmd = CHECKER.execute_command(self.current_audio_output)
        if cmd is not None:
            COMMAND_QUEUE.put(cmd)

        # Close popup
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
                self.ids.eye_btn.text = "OFF"
                self.ids.eye_btn.background_color = utils.get_color_from_hex('#ED4E33')
                STATUS["eye_on"] = False

            # Turn eye button on event
            else:
                self.ids.eye_btn.text = "ON"
                self.ids.eye_btn.background_color = utils.get_color_from_hex('#00A598')
                STATUS["eye_on"] = True

        # Check for lip button click event
        elif self.event == "click_lip_btn":
            # Turn lip button off event
            if STATUS["lip_on"]:
                self.ids.lip_btn.text = "RECORD"
                self.ids.lip_btn.background_color = utils.get_color_from_hex('#00A598')
                STATUS["lip_on"] = False

                # If speech recognition is also on, open popup to ask user to choose
                if STATUS["audio_on"]:
                    # Clear lip and audio queue
                    while not LIP_QUEUE.empty():
                        LIP_QUEUE.get()
                    while not AUDIO_QUEUE.empty():
                        AUDIO_QUEUE.get()

                    # Start Deep Lip Reading and save raw lip reading output
                    lip_sentence, lip_words = start_lip_reading()
                    print("Lipreading Output: ", lip_sentence)
                    LIP_QUEUE.put(lip_sentence)
                    self.current_lip_output = LIP_QUEUE.get()

                    # Save the raw speech recognition input into self.current_audio_output
                    self.current_audio_output = AUDIO_QUEUE.get()

                    # Start popup for user to choose lip reading or speech recognition output
                    self._open_do_you_mean_popup()

                # If only lip reading is on, send output to syntax checker
                else:
                    # Start Deep Lip Reading and save raw lip reading output
                    lip_sentence, lip_words = start_lip_reading()
                    print("Lipreading Output: ", lip_sentence)
                    LIP_QUEUE.put(lip_sentence)
                    self.current_lip_output = LIP_QUEUE.get()

                    # Syntax check raw lip reading output
                    cmd = CHECKER.execute_command(self.current_lip_output)
                    if cmd is not None:
                        COMMAND_QUEUE.put(cmd)

            # Turn lip button on event
            else:
                initialize_lipreading_variables() # reinitialize the start lip vars (clear deque) before cropping
                self.ids.lip_btn.text = "STOP"
                self.ids.lip_btn.background_color = utils.get_color_from_hex('#ED4E33')
                STATUS["lip_on"] = True

        # Check for audio button click event
        elif self.event == "click_audio_btn":
            # Turn audio button off event
            if STATUS["audio_on"]:
                self.ids.audio_btn.text = "OFF"
                self.ids.audio_btn.background_color = utils.get_color_from_hex('#ED4E33')
                STATUS["audio_on"] = False

            # Turn audio button on event
            else:
                self.ids.audio_btn.text = "ON"
                self.ids.audio_btn.background_color = utils.get_color_from_hex('#00A598')
                STATUS["audio_on"] = True

                # If lip reading is also on, open popup to ask user to choose
                if STATUS["lip_on"]:
                    # Clear lip and audio queue
                    while not LIP_QUEUE.empty():
                        LIP_QUEUE.get()
                    while not AUDIO_QUEUE.empty():
                        AUDIO_QUEUE.get()

                    # Start Deep Lip Reading and save raw lip reading output
                    lip_sentence, lip_words = start_lip_reading()
                    LIP_QUEUE.put(lip_sentence)
                    self.current_lip_output = LIP_QUEUE.get()

                    # TODO: save the raw speech recognition input into self.current_audio_output
                    self.current_audio_output = AUDIO_QUEUE.get()

                    # Start popup for user to choose lip reading or speech recognition output
                    self._open_do_you_mean_popup()

                # If only speech recognition is on, send output to syntax checker
                else:
                    # Save the raw speech recognition input into self.current_audio_output
                    self.current_audio_output = AUDIO_QUEUE.get()

                    # Syntax check raw audio reading output
                    cmd = CHECKER.execute_command(self.current_audio_output)
                    if cmd is not None:
                        COMMAND_QUEUE.put(cmd)


class Application(App):
    def build(self):
        return EyeudioGUI()


if __name__ == "__main__":
    STATUS = {
        "eye_on": False,
        "lip_on": False,
        "audio_on": False,
        "x": 0,
        "y": 0
    }    

    COMMAND_QUEUE = Queue() # queue for syntax checked commands
    AUDIO_QUEUE = Queue() # speech recognition queue to be used for popup suggestion
    LIP_QUEUE = Queue() # lip reading queue to be used for popup suggestion
    AUDIO_STATUS_QUEUE = Queue()
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
        CALIBRATION_INTERVAL = 3 # change this interval
        CURSOR_INTERVAL = 2
        lock.release()

        # first four results is used to calibration
        x_right, x_left, y_up, y_down = 0, 0, 0, 0
        # min     max     min     max


        #sleep here, check the switch every half second.
        global STATUS
        while STATUS["eye_on"] is not True:
            sleep(0.5)

        iteration = 0
        while True:
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
                sleep(CALIBRATION_INTERVAL)
                iteration += 1
                continue
            if iteration == 1: # upper-left
                x_left += x
                y_up += y
                print("------------------- Then Look Upper-right -------------------")
                sleep(CALIBRATION_INTERVAL)
                iteration += 1
                continue
            elif iteration == 2: # upper-right
                x_right += x
                y_up += y
                print("------------------- Then Look lower-right -------------------")
                sleep(CALIBRATION_INTERVAL)
                iteration += 1
                continue
            elif iteration == 3: # lower-right
                x_right += x
                y_down += y
                print("------------------- Then Look lower-left -------------------")
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

    # lipreading task 1 (cropping)
    def process_lip_frame_loop(lip_reading_deque):
        while True:
            # only process_frame if lipreading is on, and there exists a frame to process
            if STATUS["lip_on"] and (len(lip_reading_deque) > 0):
                process_frame(lip_reading_deque)
                # print("lip processing frame") # debugging
            else:
                time.sleep(0.2) # arbitrary time to wait if no frame to pop

    #### --- Speech Recognition --- ####
    audio = Audio(AUDIO_QUEUE, COMMAND_QUEUE, AUDIO_STATUS_QUEUE, CHECKER, None).start()

    ### Please comment the eye tracking and lip reading related things if you thing the initialization is too long! ###
    #### --- Eye Tracking --- ####
    args = parse_args()
    task_eye_tracker = Thread(target=eye_tracker, args=(args,lip_reading_deque,))
    task_eye_tracker.start()

    task_eye_cursor = Thread(target=eye_cursor, args=())
    task_eye_cursor.start()

    #### --- Lip Reading --- ####
    task_process_lip_frames = Thread(target=process_lip_frame_loop, args=(lip_reading_deque,))
    task_process_lip_frames.start()

    app = Application()
    app.run()

    # def exit_handler():
    #     cv2.destroyAllWindows()
    # atexit.register(exit_handler)
