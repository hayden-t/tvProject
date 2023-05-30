import numpy as np
import argparse
import imutils
import time
import cv2

# load our serialized model from disk
#print("[INFO] loading model...")
#net = cv2.dnn.readNetFromCaffe(".\deploy.prototxt.txt", ".\res10_300x300_ssd_iter_140000.caffemodel")

print("[INFO] starting video stream...")
TCP_IP = '192.168.1.234'
vs = cv2.VideoCapture('rtsp://'+TCP_IP+':554/user=admin&password=&channel=1&stream=0.sdp?real_stream--rtp-caching=100')
time.sleep(2.0)

while(True):
    # Capture frame-by-frame
    ret, frame = vs.read()
   # frame = imutils.resize(frame, width=400)
   
    print(frame.shape)

    # Display the resulting frame
    cv2.imshow('frame',frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
vs.release()
cv2.destroyAllWindows()
