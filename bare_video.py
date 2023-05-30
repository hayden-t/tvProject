#!/usr/bin/env python

from numpy import interp
from imutils.video.pivideostream import PiVideoStream
from imutils.video import FPS
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

while(1):
		#detect key
		k = cv2.waitKey(30) & 0xff
		if k == 27:
			break
	


		#get pi cam piFrame
		piFrame = vs.read()	
		
		fps.stop()

		cv2.putText(piFrame,'FPS:{0}'.format(int(fps.fps()))  ,(10,20), font, 0.5,(255,255,255),1,cv2.LINE_AA) 
		
		cv2.imshow('piFrame',piFrame)
		fps.update()

vs.stop()
cv2.destroyAllWindows()
fps.stop()

