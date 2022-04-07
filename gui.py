from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
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
from threading import Thread, Lock
from time import sleep
from collections import deque

# EYEUDIO IMPORTS =============================================
# from audio import * # audio uncomment
# from syntax_checker import * # audio uncomment
# from lip_reading.start_lip_reading import start_lip_reading #lip_reading uncomment
# from lip_reading.lip_preprocessing.record_and_crop_video import process_lip_frame_loop #lip_reading uncomment
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


class EyeudioGUI(Widget):
    '''
        Graphic User Interface screen for Eyeudio
    '''
    cursor_position = StringProperty("X: 0 \nY: 0")
    def __init__(self, **kwargs):
        super(EyeudioGUI, self).__init__(**kwargs)
        # Clock.schedule_interval(self.update_lip_log, 1) # audio uncomment
        Clock.schedule_interval(self.update_cursor_position, 1) # every second

    def _open_popup(self):
        '''
            Open a popup when a user click on the "More Info" button
        '''
        pop = Popup(title='Eyeudio Project',
                    content=WrappedLabel(text='Authors: Hoang Nguyen, Yiqing Tao, Kanglan Tang, Jordan Wong, Yaowei Ma, Frank Cai, Vincent Wang, Ananth Goyal\n\nBy 2040, over 78 million people in the US are projected to experience hand mobility limitations such as Arthritis or Repetitive Strain Injury (RSI), which affect their ability to perform computer-related tasks. The Assistive Eyeudio Control Team is developing an affordable hands-free alternative for interacting with a computer. Eyeudio makes use of the camera and microphone on any common computer (i.e. laptop) to control the mouse cursor with eye-tracking while carrying out specific commands with lip reading and speech recognition.'),
                    size_hint=(None, None), size=(400, 400))
        pop.open()

    def update_cursor_position(self, dt):
        self.cursor_position = "X: {:.0f}\nY: {:.0f}".format(status["x"], status["y"])

    def update_lip_log(self, dt):
        global q
        if not q.empty():
            print('not empty, lip command adding')
            last_command = q.get(block = False)
            if self.ids.audio_text.text.count('\n') > 10:
                self.audio_text.text = ''
            self.ids.audio_text.text = self.ids.audio_text.text + '\n' + last_command
        else:
            print('lip log empty')
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
        "aux_on": True,
        "x": 0,
        "y": 0
    }
    root_widget = None
    q = Queue()
    # syntax_checker = Checker() # audio uncomment

    lock = Lock()
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
        global status
        while status["eye_on"] is not True:
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

            if status["eye_on"]:
                # scale x and y
                x = (x - x_left) / (x_right - x_left) * (screenWidth)
                y = (y - y_up) / (y_down - y_up) * (screenHeight)
                print("\n x:{}   y: {}".format(x, y))
                status["x"] = x
                status["y"] = y

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

    #### --- Speech Recognition --- ####
    # audio = Audio(q, syntax_checker, None).start() # audio uncomment

    ### Please comment the eye tracking and lip reading related things if you thing the initialization is too long! ###
    #### --- Eye Tracking --- ####
    args = parse_args()
    task_eye_tracker = Thread(target=eye_tracker, args=(args,lip_reading_deque,))
    task_eye_tracker.start()

    task_eye_cursor = Thread(target=eye_cursor, args=()) # commented out to keep from moving cursor
    task_eye_cursor.start()

    #### --- Lip Reading --- ####
    # task_process_lip_frames = Thread(target=process_lip_frame_loop, args=(lip_reading_deque,))
    # task_process_lip_frames.start()

    app = Application()
    app.run()

    def exit_handler():
        cv2.destroyAllWindows()
    atexit.register(exit_handler)
