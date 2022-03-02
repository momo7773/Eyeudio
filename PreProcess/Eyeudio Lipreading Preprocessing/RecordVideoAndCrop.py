# Note: must be placed at same level as landmarks.dat

# Credit: Jordan Wong jotywong@berkeley.edu
# Credit: lip cropping largely based on code\lip_tracking\VisualizeLip.py 
#         from "3D Convolutional Neural Networks for Cross Audio-Visual 
#         Matching Recognition"
#         https://github.com/astorfi/lip-reading-deeplearning

import os
import numpy as np
import cv2 as cv
import dlib
import threading
import queue

import time

# Mouth cropping changeable parameters ---------------------------
predictor_path = 'shape_predictor_68_face_landmarks.dat'
output_dir = "results" # output_dir is put through os.path.join
font = cv.FONT_HERSHEY_SIMPLEX
width_crop_max = 0
height_crop_max = 0

# global variables
exitFlag = 0 # for signaling to threads to exit

class mouth_crop_thread (threading.Thread):
   def __init__(self, threadID, name, queue, queueLock, mouth_destination_path):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.queue = queue
        self.queueLock = queueLock

        # dlib requirements ------------------------
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(predictor_path)
        self.mouth_destination_path = mouth_destination_path

   def run(self):
        print("Starting " + self.name)
        while not exitFlag:
            self.queueLock.acquire()
            if not self.queue.empty():
                frame, frame_count = self.queue.get()
                self.queueLock.release()

                # crop and process frame
                process_frame(frame, frame_count, 
                    self.detector, self.predictor, self.mouth_destination_path)
                print("%s processing frame %s" % (self.name, frame_count))
            else:
                self.queueLock.release()
                time.sleep(0.1)
        print("Exiting " + self.name)

def process_frame(frame, frame_count, detector, predictor, mouth_destination_path):
    global width_crop_max, height_crop_max
    (h, w, _) = frame.shape
    
    # Detection of the frame
    frame.setflags(write=True)
    detection = detector(frame, 1)

    # 20 mark for mouth
    marks = np.zeros((2, 20))

    # If the face is detected.
    if len(detection) > 0:
        # Shape of the face.
        shape = predictor(frame, detection[0])

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
            mouth_gray = cv.cvtColor(mouth, cv.COLOR_RGB2GRAY)
            cv.imwrite(mouth_destination_path + '/' + 'frame' + '_' + str(frame_count) + '.png', mouth_gray)

            print("The cropped mouth is detected ...")
        else:
            cv.putText(frame, 'The full mouth is not detectable. ', (30, 30), font, 1, (0, 255, 255), 2)
            print("The full mouth is not detectable. ...")

    else:
        cv.putText(frame, 'Mouth is not detectable. ', (30, 30), font, 1, (0, 0, 255), 2)
        print("Mouth is not detectable. ...")

def main():
    # Make the output directory correct for the OS
    mouth_destination_path = os.path.join(output_dir)
    # Create directory if it doesn't already exist
    if not os.path.exists(mouth_destination_path):
        os.makedirs(mouth_destination_path)

    # Init threads
    threadList = ["Thread-1"]
    workQueue = queue.Queue(30)
    queueLock = threading.Lock()
    threads = []
    threadID = 1
    for tName in threadList:
        thread = mouth_crop_thread(threadID, tName, workQueue, queueLock, mouth_destination_path)
        thread.start()
        threads.append(thread)
        threadID += 1

    # Init camera
    cap = cv.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        exit()

    # Capture frame-by-frame
    frame_count = 0
    while True:

        # Capture frame
        ret, frame = cap.read()
        # if frame is read correctly ret is True
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break
        # Our operations on the frame come here
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        # Display the resulting frame
        cv.imshow('frame', gray)

        # fill workQueue every frame
        data = (frame, frame_count)
        queueLock.acquire()
        try:
            workQueue.put(data, block=False)
        except Exception as err:
            frame_count -= 1
        queueLock.release()

        # increment frame count so we label the output frames accordingly
        frame_count += 1
        print(frame_count)

        # Press q to exit loop
        if cv.waitKey(1) == ord('q'):
            break
    
    # When everything done, release the capture
    cap.release()
    cv.destroyAllWindows()

    # Notify threads it's time to exit
    global exitFlag 
    exitFlag = 1

    # Wait for all threads to complete
    for t in threads:
        t.join()
    print("Exiting Main Thread")

if __name__ == "__main__":
    main()