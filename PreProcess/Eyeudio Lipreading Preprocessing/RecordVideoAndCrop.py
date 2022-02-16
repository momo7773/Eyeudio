import cv2 as cv
import threading
import queue
import time

from ProcessFrame import process_frame

# Init thread vars
threadList = ["Thread-1", "Thread-2", "Thread-3", "Thread-4", "Thread-5"]
queueLock = threading.Lock()
workQueue = queue.Queue(30)
threads = []
threadID = 1
exitFlag = 0

class myThread (threading.Thread):
   def __init__(self, threadID, name, q):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
      self.q = q
   def run(self):
      print("Starting " + self.name)
      process_data(self.name, self.q)
      print("Exiting " + self.name)

def process_data(threadName, q):
    while not exitFlag:
        queueLock.acquire()
        if not workQueue.empty():
            frame, frame_count = q.get()
            queueLock.release()

            # crop and process frame
            process_frame(frame, "results/out.mp4", frame_count) # TODO: Change output to just the directory
            print("%s processing frame %s" % (threadName, frame_count))
        else:
            queueLock.release()
            time.sleep(0.5)

# Create new threads
for tName in threadList:
    thread = myThread(threadID, tName, workQueue)
    thread.start()
    threads.append(thread)
    threadID += 1

def main():
    # Init camera
    cap = cv.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        exit()

    # Capture frame-by-frame
    frame_count = 0
    frame_buffer = []
    while True:
        start = time.time()

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
        
        print("frame captured" + str(time.time()-start))

        # fill workQueue every 5 frames
        data = (frame, frame_count)
        frame_buffer.append(data)
        print("data appended" + str(time.time()-start))
        if(frame_count % 5 == 4):
            queueLock.acquire()
            print("Lock acquired" + str(time.time()-start))
            for data in frame_buffer:
                workQueue.put(data)
                print("Added frame %i" % data[1])
            frame_buffer = []
            queueLock.release()
            print("lock released" + str(time.time()-start))

        # increment frame count so we label the output frames accordingly
        frame_count += 1

        # Press q to exit loop
        if cv.waitKey(1) == ord('q'):
            break
    
    # When everything done, release the capture
    cap.release()
    cv.destroyAllWindows()

if __name__ == "__main__":
    main()

    # Notify threads it's time to exit
    exitFlag = 1

    # Wait for all threads to complete
    for t in threads:
        t.join()
    print("Exiting Main Thread")