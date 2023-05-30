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


TCP_IP = '192.168.60.200'
TCP_PORT = 5678
BUFFER_SIZE = 11 #max bytes returned in protocol
TIMEOUT = 5 #seconds
UPDATE_RATE = 1 #seconds

doTransmit = True;

vs = PiVideoStream((624, 352)).start()
fps = FPS().start()
time.sleep(2.0)

minWidth = 100 #min smoothed bounds width

#cap = cv2.VideoCapture('rtsp://'+TCP_IP+":554/2")


font = cv2.FONT_HERSHEY_SIMPLEX


panTiltRequest = bytearray([0x81, 0x09, 0x06, 0x12, 0xff])#pan/tilt
zoomRequest = bytearray([0x81, 0x09, 0x04, 0x47, 0xff])#zoom

def connect():
	global s
	global lastRecieve
	print "connecting to: "+TCP_IP+":"+str(TCP_PORT)
	while(1):		
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect((TCP_IP, TCP_PORT))
			s.setblocking(0)
			print "connected"
			lastRecieve = time.time()
			break
		except:
			print "trying again"

if doTransmit:
	connect()

lastTransmit = time.time()

messages = 	[
				[0x90, 0x41, 0xff],"ACK,socket 1",
				[0x90, 0x42, 0xff],"ACK, socket 2",
				[0x90, 0x51, 0xff],"Completion, socket 1",
				[0x90, 0x52, 0xff],"Completion, socket 2",
				[0x90, 0x60, 0x02, 0xff],"Syntax Error",
				[0x90, 0x60, 0x03, 0xff],"Command Buffer Full",
				[0x90, 0x61, 0x04, 0xff],"Command Cancelled, socket 1",
				[0x90, 0x62, 0x04, 0xff],"Command Cancelled, socket 2",
				[0x90, 0x61, 0x05, 0xff],"No Socket, socket 1",
				[0x90, 0x62, 0x05, 0xff],"No Socket, socket 2",		
				[0x90, 0x61, 0x41, 0xff],"Command Not Executable, socket 1",
				[0x90, 0x62, 0x41, 0xff],"Command Not Executable, socket 2",
			]
packet = []
pan = 0
tilt = 0
zoom = 0
pulse = False

def transmit(packet):
	try:
		s.send(packet)		
	except Exception as e:
		print "transmit packet failed"
		print str(e)
		connect()
		

while(1):
		#detect key
		k = cv2.waitKey(30) & 0xff
		if k == 27:
			break
	
				
		try:
			data = s.recv(1)
			
			while(data):
				packet.append(ord(data))
				if ord(data) == 0xff :
					if packet in messages:
						index = messages.index(packet)
						if index > -1: print messages[index+1]#only print errors
					else:
						if packet[0] == 0x90 and packet[1] == 0x50:# enquiry response
							if len(packet) == 7:#zoom
								zoom = (packet[2]*16**2)+ (packet[3]*16**1)+(packet[4]*16**0)
							elif len(packet) == 11:#pan/tilt

								pan = (packet[3]*16**2)+ (packet[4]*16**1)+(packet[5]*16**0)
								if(packet[2] == 0xf):pan = (0xfff-pan)*-1#counts down
								
								tilt = (packet[7]*16**2)+ (packet[8]*16**1)+(packet[9]*16**0)
								if(packet[6] == 0xf):tilt = (0xfff-tilt)*-1#counts down
								
								pulse = not pulse

							else:
								print "unknown packet: " + repr(packet)
							print packet
						else:
							print "unknown packet: " + repr(packet)
					packet = []
					#packet end 0xff
					
				data = s.recv(1)
				
		except:#no data
			pass	
			
					
		if time.time() - lastTransmit > UPDATE_RATE:
			lastTransmit = time.time()
			
			if doTransmit:
				transmit(panTiltRequest)			
				transmit(zoomRequest)	
			
			
		#get pi cam piFrame
		piFrame = vs.read()	
		
		#pi center cross bg
		cv2.line(piFrame,((piFrame.shape[1]/2)-minWidth/2,piFrame.shape[0]/2),((piFrame.shape[1]/2)+minWidth/2,piFrame.shape[0]/2), (0,0,0), 2)#x
		cv2.line(piFrame,(piFrame.shape[1]/2,(piFrame.shape[0]/2)+10),(piFrame.shape[1]/2,(piFrame.shape[0]/2)-10), (0,0,0), 2)#y
		
		#pi center cross
		cv2.line(piFrame,((piFrame.shape[1]/2)-minWidth/2,piFrame.shape[0]/2),((piFrame.shape[1]/2)+minWidth/2,piFrame.shape[0]/2), (0,255,0), 1)#x
		cv2.line(piFrame,(piFrame.shape[1]/2,(piFrame.shape[0]/2)+10),(piFrame.shape[1]/2,(piFrame.shape[0]/2)-10), (255,255,255), 1)#y

		
		#get ip cam piFrame
		#ret, ipFrame = cap.read()
		#resize ip frame
		#ipFrame = cv2.resize(ipFrame,(piFrame.shape[1], piFrame.shape[0]))	
		#ip center cross   
		#cv2.line(ipFrame,((ipFrame.shape[1]/2)-10,ipFrame.shape[0]/2),((ipFrame.shape[1]/2)+10,ipFrame.shape[0]/2), (0,0,0), 2)
		#cv2.line(ipFrame,(ipFrame.shape[1]/2,(ipFrame.shape[0]/2)+10),(ipFrame.shape[1]/2,(ipFrame.shape[0]/2)-10), (0,0,0), 2) 		 
		#cv2.line(ipFrame,((ipFrame.shape[1]/2)-10,ipFrame.shape[0]/2),((ipFrame.shape[1]/2)+10,ipFrame.shape[0]/2), (255,255,255), 1)
		#cv2.line(ipFrame,(ipFrame.shape[1]/2,(ipFrame.shape[0]/2)+10),(ipFrame.shape[1]/2,(ipFrame.shape[0]/2)-10), (255,255,255), 1)


		#expand for ip frame
		#newFrame = cv2.copyMakeBorder(piFrame,0,ipFrame.shape[0],0,0,cv2.BORDER_CONSTANT, value=[0,0,0])
		#add ip frame
		#newFrame[piFrame.shape[0]:piFrame.shape[0]+ipFrame.shape[0],0:piFrame.shape[1]]  = ipFrame
		newFrame = piFrame

		#expand for readout
		newFrame = cv2.copyMakeBorder(newFrame,30,0,0,0,cv2.BORDER_CONSTANT, value=[0,0,0])
		
		fps.stop()				
		#readings
		cv2.putText(newFrame,'P:{0:+}'.format(pan)+' T:{0:+}'.format(tilt)+' Z:{0:+}'.format(zoom)+' FPS:{0}'.format(int(fps.fps()))+' {0:}'.format("." if pulse else "")  ,(10,20), font, 0.5,(255,255,255),1,cv2.LINE_AA) 
		

		cv2.imshow('piFrame',newFrame)
		fps.update()

if doTransmit:
	s.close()
vs.stop()
cv2.destroyAllWindows()
