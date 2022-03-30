from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy import utils

import cv2
import argparse
import logging
import pathlib
import warnings
import torch
import numpy as np
import pyautogui
import atexit

from multiprocessing import Queue
from omegaconf import DictConfig, OmegaConf
from threading import Thread, Lock
from time import sleep, ctime
from threading import Thread, Lock
from time import sleep
from audio import *
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
    def __init__(self, **kwargs):
        super(EyeudioGUI, self).__init__(**kwargs)

    def _open_popup(self):
        '''
            Open a popup when a user click on the "More Info" button
        '''
        pop = Popup(title='Eyeudio Project',
                    content=WrappedLabel(text='Authors: Hoang Nguyen, Yiqing Tao, Kanglan Tang, Jordan Wong, Yaowei Ma, Frank Cai, Vincent Wang, Ananth Goyal\n\nBy 2040, over 78 million people in the US are projected to experience hand mobility limitations such as Arthritis or Repetitive Strain Injury (RSI), which affect their ability to perform computer-related tasks. The Assistive Eyeudio Control Team is developing an affordable hands-free alternative for interacting with a computer. Eyeudio makes use of the camera and microphone on any common computer (i.e. laptop) to control the mouse cursor with eye-tracking while carrying out specific commands with lip reading and speech recognition.'),
                    size_hint=(None, None), size=(400, 400))
        pop.open()

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


    lock = Lock()
    queue = Queue()

    # eyetracking task 1
    def eye_tracker(args, queue):
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
        face_eye.run(queue)

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
            array = np.array(face_eye.gaze_estimator.results)
            # preprocesing: np.abs(data - np.mean(data, axis=0)) > np.std(data, axis=0) and only keep the all true ones
            if len(face_eye.gaze_estimator.results) == 0:
                sleep(CURSOR_INTERVAL)
                continue
            x /= -len(face_eye.gaze_estimator.results) # change sign (right should be larger than left)
            y /= len(face_eye.gaze_estimator.results)
            

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

    # for lip-reading usage
    def show_stored_frame(queue): 
        while True:
            if not queue.empty():
                # 1. get a frame and it's sequential id.
                frame, id = queue.get()
                # 2. try to show it
                cv2.imshow("current frame", frame)  
                key = cv2.waitKey(1)
                if key == 27: #'q'
                    cv2.destroyAllWindows()
                
    #### --- Speech Recognition --- ####
    # initialize_audio()
    # t1 = Thread(target=audio_process, args=())
    # t1.start()

    #### --- Eye Tracking --- ####
    args = parse_args()
    task_eye_tracker = Thread(target=eye_tracker, args=(args,queue,))
    task_eye_tracker.start()

    task_eye_cursor = Thread(target=eye_cursor, args=())
    task_eye_cursor.start()

    #### --- Lip Reading --- ####
    ## To Jordan:
    # frames are stored a message queue
    # task_show_frame is an example
    task_show_frame = Thread(target=show_stored_frame, args=(queue,))
    task_show_frame.start()

    app = Application()
    app.run()

    def exit_handler():
        cv2.destroyAllWindows()
    atexit.register(exit_handler)
    