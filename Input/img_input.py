import numpy as np
import cv2

number_of_frames = 3
class Image_Input(Input):
    def __init__(self):
        pass

    def get_frames(self):
        cap = cv2.VideoCapture(0)
        counter = 0
        while(counter < number_of_frames):
            # Capture frame-by-frame
            ret, frame = cap.read()

            # Our operations on the frame come here
            if not ret:
                print('failed to grab frame')
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)

            # Display the resulting frame
            cv2.imshow('frame',gray)
            cv2.waitKey(3000)
            if cv2.waitKey(1000) & 0xFF == ord('q'):
                break
            counter++

        # When everything done, release the capture
        cap.release()
        cv2.destroyAllWindows()

input = Image_Input()
input.get_frames()
