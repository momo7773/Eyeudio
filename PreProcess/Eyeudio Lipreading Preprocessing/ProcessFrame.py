# Note: must be placed at same level as landmarks.dat

# Credit: largely based on code\lip_tracking\VisualizeLip.py from 
#         "3D Convolutional Neural Networks for Cross Audio-Visual 
#         Matching Recognition"
#         https://github.com/astorfi/lip-reading-deeplearning

import numpy as np
import cv2
import dlib
import math
import sys
import pickle
import argparse
import os
import skvideo.io

import time

def process_frame(frame, output_dir, frame_count):

    """
    PART2: Calling and defining required parameters for:

        1 - Processing video for extracting each frame.
        2 - Lip extraction from frames.
    """

    # Dlib requirements.
    predictor_path = 'shape_predictor_68_face_landmarks.dat'
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(predictor_path)
    mouth_destination_path = os.path.dirname(output_dir) + '/' + 'mouth'
    if not os.path.exists(mouth_destination_path):
        os.makedirs(mouth_destination_path)

    video_shape = frame.shape
    (h, w, c) = video_shape
    # print(h, w, c)

    # The required parameters
    font = cv2.FONT_HERSHEY_SIMPLEX

    # Required parameters for mouth extraction.
    width_crop_max = 0
    height_crop_max = 0

    """
    PART3: Processing the video.

    Procedure:
        1 - Extracting each frame.
        2 - Detect the mouth in the frame.
        3 - Define a boarder around the mouth.
        4 - Crop and save the mouth.

    Technical considerations:
        * - For the first frame the mouth is detected and by using a boarder the mouth is extracted and cropped.
        * - After the first frame the size of the cropped windows remains fixed unless for the subsequent frames
            a bigger windows is required. In such a case the windows size will be increased and it will be held
            fixed again unless increasing the size becoming necessary again too.
    """
    # print('frame_shape:', frame.shape)

    # Detection of the frame
    frame.setflags(write=True)
    detections = detector(frame, 1)

    # 20 mark for mouth
    marks = np.zeros((2, 20))

    # If the face is detected.
    # print(len(detections))
    if len(detections) > 0:
        for k, d in enumerate(detections):

            # Shape of the face.
            shape = predictor(frame, d)

            co = 0
            # Specific for the mouth.
            for ii in range(48, 68):
                """
                This for loop is going over all mouth-related features.
                X and Y coordinates are extracted and stored separately.
                """
                X = shape.part(ii)
                A = (X.x, X.y)
                marks[0, co] = X.x
                marks[1, co] = X.y
                co += 1

            # Get the extreme points(top-left & bottom-right)
            X_left, Y_left, X_right, Y_right = [int(np.amin(marks, axis=1)[0]), int(np.amin(marks, axis=1)[1]),
                                                int(np.amax(marks, axis=1)[0]),
                                                int(np.amax(marks, axis=1)[1])]

            # Find the center of the mouth.
            X_center = (X_left + X_right) / 2.0
            Y_center = (Y_left + Y_right) / 2.0

            # Make a boarder for cropping.
            border = 30
            X_left_new = X_left - border
            Y_left_new = Y_left - border
            X_right_new = X_right + border
            Y_right_new = Y_right + border

            # Width and height for cropping(before and after considering the border).
            width_new = X_right_new - X_left_new
            height_new = Y_right_new - Y_left_new
            width_current = X_right - X_left
            height_current = Y_right - Y_left

            # Determine the cropping rectangle dimensions(the main purpose is to have a fixed area).
            if width_crop_max == 0 and height_crop_max == 0:
                width_crop_max = width_new
                height_crop_max = height_new
            else:
                width_crop_max += 1.5 * np.maximum(width_current - width_crop_max, 0)
                height_crop_max += 1.5 * np.maximum(height_current - height_crop_max, 0)

            # # # Uncomment if the lip area is desired to be rectangular # # # #
            #########################################################
            # Find the cropping points(top-left and bottom-right).
            X_left_crop = int(X_center - width_crop_max / 2.0)
            X_right_crop = int(X_center + width_crop_max / 2.0)
            Y_left_crop = int(Y_center - height_crop_max / 2.0)
            Y_right_crop = int(Y_center + height_crop_max / 2.0)
            #########################################################

            # # # # # Uncomment if the lip area is desired to be rectangular # # # #
            # #######################################
            # # Use this part if the cropped area should look like a square.
            # crop_length_max = max(width_crop_max, height_crop_max) / 2
            #
            # # Find the cropping points(top-left and bottom-right).
            # X_left_crop = int(X_center - crop_length_max)
            # X_right_crop = int(X_center + crop_length_max)
            # Y_left_crop = int(Y_center - crop_length_max)
            # Y_right_crop = int(Y_center + crop_length_max)
            #########################################

            if X_left_crop >= 0 and Y_left_crop >= 0 and X_right_crop < w and Y_right_crop < h:
                mouth = frame[Y_left_crop:Y_right_crop, X_left_crop:X_right_crop, :]

                # Save the mouth area.
                mouth_gray = cv2.cvtColor(mouth, cv2.COLOR_RGB2GRAY)
                cv2.imwrite(mouth_destination_path + '/' + 'frame' + '_' + str(frame_count) + '.png', mouth_gray)

                print("The cropped mouth is detected ...")
            else:
                cv2.putText(frame, 'The full mouth is not detectable. ', (30, 30), font, 1, (0, 255, 255), 2)
                print("The full mouth is not detectable. ...")

    else:
        cv2.putText(frame, 'Mouth is not detectable. ', (30, 30), font, 1, (0, 0, 255), 2)
        print("Mouth is not detectable. ...")
