# Note: must be placed at same level as landmarks.dat, unless you change predictor_path below

# Credit: Jordan Wong jotywong@berkeley.edu
# Credit: lip cropping largely based on code\lip_tracking\VisualizeLip.py 
#         from "3D Convolutional Neural Networks for Cross Audio-Visual 
#         Matching Recognition"
#         https://github.com/astorfi/lip-reading-deeplearning

from collections import deque
import os
import numpy as np
import cv2 as cv
import dlib
import threading
import copy
import time

# Mouth cropping changeable parameters ------------------------
max_frames_to_hold = 120 # max number of processed frames to keep track of
dirname = os.path.dirname(__file__) # to get path of predictor, relative to this file, regardless of imported or not
predictor_path = os.path.join(dirname, './shape_predictor_68_face_landmarks.dat')
font = cv.FONT_HERSHEY_SIMPLEX
size_of_crops = 80

# dlib requirements -------------------------------------------
lip_detector = dlib.get_frontal_face_detector()
lip_predictor = dlib.shape_predictor(predictor_path)

# global variables --------------------------------------------
g_exit_flag = 0 # for signaling to threads to exit
g_frame_count = 0 # for labeling output cropped frames
g_message_to_display = 'Starting...' # for updating the real time feed
g_output_queue = deque(maxlen=max_frames_to_hold)

def initialize_lipreading_variables():
    global g_exit_flag, g_frame_count, g_output_queue
    g_exit_flag = 0 # for signaling to threads to exit
    g_frame_count = 0 # for labeling output cropped frames
    g_output_queue.clear()

class mouth_crop_thread (threading.Thread):
   def __init__(self, threadID, name, workQueue):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.workQueue = workQueue

   def run(self):
        print("Starting " + self.name)
        while not g_exit_flag:
            if (len(self.workQueue) > 0):
                # crop and process frame, process_frame() will popLeft a frame from deque
                process_frame(self.workQueue)

                global g_frame_count
                print("%s processing frame %s" % (self.name, g_frame_count))
            else:
                time.sleep(0.1)
        print("Exiting " + self.name)

def get_copy_of_output_frames():
    return copy.deepcopy(g_output_queue)

def process_frame(lip_reading_deque):
    global g_frame_count, g_message_to_display, g_output_queue

    # grab frame from deque
    frame = lip_reading_deque.popleft()
    (h, w, _) = frame.shape
    
    # Detection of the frame
    frame.setflags(write=True)
    detection = lip_detector(frame, 1)

    # 20 mark for mouth
    marks = np.zeros((2, 20))

    # If the face is detected.
    if len(detection) > 0:
        # Shape of the face.
        shape = lip_predictor(frame, detection[0])

        co = 0
        # Specific for the mouth.
        for ii in range(48, 68):
            """
            This for loop is going over all mouth-related features.
            X and Y coordinates are extracted and stored separately.
            """
            X = shape.part(ii)
            marks[0, co] = X.x
            marks[1, co] = X.y
            co += 1

        # Get the extreme points(top-left & bottom-right)
        X_left, Y_left, X_right, Y_right = [int(np.amin(marks, axis=1)[0]), int(np.amin(marks, axis=1)[1]),
                                            int(np.amax(marks, axis=1)[0]), int(np.amax(marks, axis=1)[1])]

        # Find the center of the mouth.
        X_center = (X_left + X_right) / 2.0
        Y_center = (Y_left + Y_right) / 2.0

        # Make a border for cropping.
        border = 30
        X_left_new = X_left - border
        Y_left_new = Y_left - border
        X_right_new = X_right + border
        Y_right_new = Y_right + border

        # Width and height for cropping(before and after considering the border).
        width_new = X_right_new - X_left_new
        height_new = Y_right_new - Y_left_new

        # # # Uncomment if the lip area is desired to be rectangular # # # #
        #########################################################
        # Find the cropping points(top-left and bottom-right).
        # X_left_crop = int(X_center - width_new / 2.0)
        # X_right_crop = int(X_center + width_new / 2.0)
        # Y_left_crop = int(Y_center - height_new / 2.0)
        # Y_right_crop = int(Y_center + height_new / 2.0)
        #########################################################

        # # Use this part if the cropped area should look like a square.
        # #######################################
        crop_length_max = max(width_new, height_new) / 2
        if (size_of_crops != 0):
            crop_length_max = 80
        
        # Find the cropping points(top-left and bottom-right).
        X_left_crop = int(X_center - crop_length_max)
        X_right_crop = int(X_center + crop_length_max)
        Y_left_crop = int(Y_center - crop_length_max)
        Y_right_crop = int(Y_center + crop_length_max)
        #########################################

        if X_left_crop >= 0 and Y_left_crop >= 0 and X_right_crop < w and Y_right_crop < h:
            mouth = frame[Y_left_crop:Y_right_crop, X_left_crop:X_right_crop, :]

            # Save the mouth area.
            mouth_gray = cv.cvtColor(mouth, cv.COLOR_RGB2GRAY)

            # Or to our queue
            g_output_queue.append(mouth_gray)

            g_frame_count += 1 # increment so we write to a new file name next frame
            if (g_frame_count >= max_frames_to_hold): # but don't keep more frames than requested
                g_frame_count = 0

            g_message_to_display = "The cropped mouth is detected ..."
            # print("The cropped mouth is detected ...") # debugging
        else:
            g_message_to_display = "The full mouth is not detectable. ..."
            # print("The full mouth is not detectable. ...") # debugging

    else:
        g_message_to_display = "Mouth is not detectable. ..."
        # print("Mouth is not detectable. ...") # debugging

def record_and_crop():
    initialize_lipreading_variables()

    # Init threads
    threadList = ["Thread-1"] # Can add threads by adding to this list
    workQueue = deque(maxlen=len(threadList)*2)
    threads = []
    threadID = 1
    for tName in threadList:
        thread = mouth_crop_thread(threadID, tName, workQueue)
        thread.start()
        threads.append(thread)
        threadID += 1

    # Init camera
    cap = cv.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        exit()

    # Capture frame-by-frame
    while True:
        # Capture frame
        ret, frame = cap.read()
        # if frame is read correctly ret is True
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break

        # fill workQueue every frame (if queue has no room, it deletes oldest frame
        workQueue.append(frame)

        # Add message to real time feed
        message_color = (0, 0, 255) # red
        if (g_message_to_display == "The cropped mouth is detected ..."):
            message_color = (0, 255, 0) # green
        image = cv.putText(frame, g_message_to_display, (30, 30), font, 1, message_color, 2)
        # Display the resulting frame
        cv.imshow('frame', image)

        # Press q to exit loop
        if cv.waitKey(1) == ord('q'):
            break
    
    # When everything done, release the capture
    cap.release()
    cv.destroyAllWindows()

    # Notify threads it's time to exit
    g_exit_flag = 1

    # Wait for all threads to complete
    for t in threads:
        t.join()
    print("Exiting Main Thread")

if __name__ == "__main__":
    record_and_crop()
    frames = np.array(get_copy_of_output_frames())
    print(frames.shape)
