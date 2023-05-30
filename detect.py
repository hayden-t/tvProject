#!/usr/bin/env python

from numpy import interp
from imutils.video.pivideostream import PiVideoStream
from imutils.video import FPS
from imutils.object_detection import non_max_suppression
from picamera.array import PiRGBArray
from picamera import PiCamera
import numpy
import cv2
import socket
import time
import imutils



vs = PiVideoStream((624, 352)).start()
fps = FPS().start()
time.sleep(2.0)

font = cv2.FONT_HERSHEY_SIMPLEX

# initialize the HOG descriptor/person detector
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

while(1):
		#detect key
		k = cv2.waitKey(30) & 0xff
		if k == 27:
			break	


		#get pi cam piFrame
		piFrame = vs.read()	
		
		image = imutils.resize(piFrame, width=min(400, piFrame.shape[1]))
		orig = image.copy()
		
		# detect people in the image
		(rects, weights) = hog.detectMultiScale(image, winStride=(4, 4),
			padding=(8, 8), scale=1.05)

		# draw the original bounding boxes
		for (x, y, w, h) in rects:
			cv2.rectangle(orig, (x, y), (x + w, y + h), (0, 0, 255), 2)

		# apply non-maxima suppression to the bounding boxes using a
		# fairly large overlap threshold to try to maintain overlapping
		# boxes that are still people
		rects = numpy.array([[x, y, x + w, y + h] for (x, y, w, h) in rects])
		pick = non_max_suppression(rects, probs=None, overlapThresh=0.65)

		# draw the final bounding boxes
		for (xA, yA, xB, yB) in pick:
			cv2.rectangle(image, (xA, yA), (xB, yB), (0, 255, 0), 2)
		
		
		fps.stop()

		cv2.putText(image,'FPS:{0}'.format(int(fps.fps()))  ,(10,20), font, 0.5,(255,255,255),1,cv2.LINE_AA) 
		
		cv2.imshow('piFrame',image)
		fps.update()

vs.stop()
cv2.destroyAllWindows()
fps.stop()

