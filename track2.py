from scipy import stats
from numpy import interp
#from imutils.video.pivideostream import PiVideoStream
from imutils.video import FPS
#from picamera.array import PiRGBArray
#from picamera import PiCamera
import numpy
import cv2
import socket
import time
import imutils
import datetime

#try some sharpness

#happy hour
startTime = datetime.time(15,0)#inclusive
endTime = datetime.time(16,0)#exclusive
day = 4

#test
#startTime = datetime.time(14,15)
#endTime = datetime.time(14,16)
#day = 6

print "starting"

TCP_IP = '192.168.0.3'

#vs = PiVideoStream((624, 352)).start()
vs = cv2.VideoCapture('rtsp://admin:chan1234@'+TCP_IP+':554/cam/realmonitor?channel=1&subtype=0')

#get 1 frame
ret, frame = vs.read()
print "vision connected, frame size: ",frame.shape[1]," x ", frame.shape[0]


smoothedBounds = [0,0,frame.shape[1],frame.shape[0]]
smoothedBoundsTimer = [0,0,0,0]

fps = FPS().start()


fgbg = cv2.bgsegm.createBackgroundSubtractorMOG(200, 5, 0.7, 0)

#print  fgbg.getn
#fgbg.setBackgroundRatio(0.01)

font = cv2.FONT_HERSHEY_SIMPLEX
#todo add more on top
padding = 0 #for smoothed boundary
crop = [120,150,40,500] #ignore motions  top, bottom, left, right
threshold = 0 #ignore changes smaller than

targetAR = float(16)/9 #for smoothed bounds
smoothingArraySize = 1 #ring averages/mean buffer, bigger is slower
minWidth = 100 #min smoothed bounds width
minHeight = minWidth * (1/targetAR)

panFromTo = [-398,379]#-left,right
tiltFromTo = [-250,97]#down,up
zoomFromTo = [0,750]#out,in

#cannot use both

#applied in camera units b4 send
centerOffset = [+0,-126]#x/pan(+right),y/tilt(+up) - general alignment
centerOffset2 = [+0,-230]#x/pan(+right),y/tilt(+up) - for look around

#ptz camera on ceiling, flip image
inverted = True
	
zoomFromTo.reverse()

currentZoom = 0
targetZoom = 0
dirZoom = 0
#zoom 56 steps takes 15 seconds on speed 0
zoomTick = float(15)/56
lastZoomRequest = 0

scaledPTZ = [0,0,0]
lastRawBounds = [0,0,0,0]


offline = True #dont connect to ptz camera
forceConnect = False #override schedule
pulse = False
packet = []

noMotionExpand = False

			
lookAroundInterval = 300 #have a look around every seconds #0 disables
lookAroundStage = 0 #looking around state
lookAroundStageInterval = 20 #seconds for each stage
lookAroundTimer = time.time() #timer

TCP_IP = '192.168.60.200'
TCP_PORT = 5678
UPDATE_RATE = 10 #send rate seconds
TIMEOUT = 60 #connection recieve timeout
ptzSocket = None #socket
lastReceive = time.time()
lastTransmit = 0
connected = False

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

def connect():
	global ptzSocket
	global lastReceive
	global connected
	global packet
	global dirZoom
	global lookAroundStage
	global lookAroundTimer
	
	#class instead ??
	packet = []
	dirZoom = 0
	lookAroundStage = 0
	lookAroundTimer = time.time() #timer	
	
	
	if offline:
		connected = True
		print "offline connect"
		return;
	
	
	print "connecting to: "+TCP_IP+":"+str(TCP_PORT)
	while(1):	
		try:	
			ptzSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			ptzSocket.connect((TCP_IP, TCP_PORT))
			ptzSocket.setblocking(0)
			print "connected"
			connected = True	
			lastReceive = time.time()#reset
			
			#these are settings needed, but not saved between camera boots
			invertedByte = 0x03 if inverted else 0x00
			if inverted: print "inverted"
			ptzSocket.send(bytearray([0x81, 0x01, 0x04, 0xA4,invertedByte ,0xff]))#setup flip & mirror
			ptzSocket.send(bytearray([0x81, 0x01, 0x04, 0x23, 0x01, 0xff]))#setup 50Hz flicker
			ptzSocket.send(bytearray([0x81, 0x01, 0x04, 0x42, 0x00, 0x00, 0x00, 0x06, 0xff]))#sharpness level 6
			centerCamera()
			
			break
		except Exception as e:
			print "trying again"
			print str(e)

def disconnect():
	global connected

	if connected:
		centerCamera()
		ptzSocket.close()
		
	connected = False	
	print "disconnected" 

def updateRemoteCamera(scaledPTZ, speed = 0x01):

	global targetZoom
	global dirZoom
	
	if scaledPTZ[0] < 0:#left
		panDir = 0x0f
		panDirLabel = "Pan: L "
		panFactor1 = 0xf-(-scaledPTZ[0])//16**2
		panFactor2 = 0xf-(-scaledPTZ[0]%16**2)//16**1
		panFactor3 = 0xf-(-scaledPTZ[0]%16**2)%16**1
	else:#right
		panDir = 0x00
		panDirLabel = "Pan: R "

		panFactor1 = scaledPTZ[0]//16**2
		panFactor2 = (scaledPTZ[0]%16**2)//16**1
		panFactor3 = (scaledPTZ[0]%16**2)%16**1
			
	if scaledPTZ[1] < 0:#down
		tiltDir = 0x0f
		tiltDirLabel = "Tilt: D "
		tiltFactor1 = 0xf-(-scaledPTZ[1])//16**2 #max 0x0e 0x05 (25)
		tiltFactor2 = 0xf-(-scaledPTZ[1]%16**2)//16**1
		tiltFactor3 = 0xf-(-scaledPTZ[1]%16**2)%16**1
	else:#up
		tiltDir = 0x00
		tiltDirLabel = "Tilt: U "
		tiltFactor1 = scaledPTZ[1]//16**2 #max 0x05 0x01 (76)
		tiltFactor2 = (scaledPTZ[1]%16**2)//16**1
		tiltFactor3 = (scaledPTZ[1]%16**2)%16**1
		
	panTiltPacket = bytearray([	0x81, 0x01, 0x06, 0x02, #command
							speed, speed, #pan & tilt speed: 0x01-0x18 (24 steps)
							panDir, #left: 0x0f or right: 0x00
							panFactor1, panFactor2, panFactor3, # 0x00 to 0x0f for each (16 steps), going up for right, and down for left
							tiltDir, #up: 0x00 or down: 0x0f
							tiltFactor1, tiltFactor2, tiltFactor3, # 0x00 to 0x0f for each (16 steps), going up for up, and down for down
							0xff #end
	])
	
	transmit(panTiltPacket)

	if currentZoom > scaledPTZ[2]:
		transmit(bytearray([0x81, 0x01, 0x04, 0x07,0x30,0xff]))#slowest out
		dirZoom = -1 
		#print "zoom out"
	elif currentZoom < scaledPTZ[2]:
		transmit(bytearray([0x81, 0x01, 0x04, 0x07,0x20,0xff]))#slowest in
		dirZoom = 1
		#print "zoom in"
	targetZoom = scaledPTZ[2]
	
	print list(scaledPTZ)
	#print list(panTiltPacket)
	return
	
def transmit(packet):
	try:
		ptzSocket.send(packet)
	except Exception as e:
		print "transmit packet failed"
		print str(e)
		connect()

def processVideo():
	
	global lastRawBounds
	global smoothedBounds
	global smoothedBoundsTimer
	#global connected
	
	#get frame
	ret, frame = vs.read()
	
	#crop for ignore
	detectionArea = frame[0+crop[0] : frame.shape[0]-crop[1] , 0+crop[2] : frame.shape[1]-crop[3]]
	
	#detect motion
	fgmask = fgbg.apply(detectionArea)
	

	fgmask = cv2.GaussianBlur(fgmask, (21, 21), 0)
	#fgmask = cv2.medianBlur(fgmask,3)
	

	#pad back out to frame size for merge
	fgmask = cv2.copyMakeBorder(fgmask,crop[0],crop[1],crop[2],crop[3],cv2.BORDER_CONSTANT, value=[0,0,0])
	
	#calc bounds b4 color
	rawBounds = cv2.boundingRect(fgmask)#(x, y, w, h)
	
	#convert to color
	fgmask = cv2.cvtColor(fgmask,cv2.COLOR_GRAY2BGR)
 
	#merge motion & frame
	frame = cv2.add(frame, fgmask)

	#as 2x point coords (x1,y1,x2,y2)
	rawBounds = [rawBounds[0],rawBounds[1],rawBounds[0]+rawBounds[2],rawBounds[1]+rawBounds[3]]

	 
	#check for no motion
	if(rawBounds[0] == rawBounds[1] == rawBounds[2] == rawBounds[3] == 0):
		if noMotionExpand:
			rawBounds[2] = frame.shape[1]
			rawBounds[3] = frame.shape[0]
		else:
			rawBounds = lastRawBounds[:]
			
	lastRawBounds = rawBounds[:]
	
	#add padding        
	rawBounds[0] = max(0, rawBounds[0]-padding)
	rawBounds[1] = max(0, rawBounds[1]-padding)
	rawBounds[2] = min(frame.shape[1], rawBounds[2]+padding)
	rawBounds[3] = min(frame.shape[0], rawBounds[3]+padding)

	#raw center
	rawCenterPosition = [((rawBounds[2] - rawBounds[0])/2)+rawBounds[0], ((rawBounds[3] - rawBounds[1])/2)+rawBounds[1]]
	


	
	
	if rawBounds[0] < smoothedBounds[0]:#bigger
		smoothedBounds[0] = smoothedBounds[0] - 3
	elif rawBounds[0] > smoothedBounds[0]:
		#if time.time() - smoothedBoundsTimer[0] > 1:
		smoothedBounds[0] = smoothedBounds[0] + 1
		smoothedBoundsTimer[0] = time.time()
	
	if rawBounds[1] < smoothedBounds[1]:#bigger
		smoothedBounds[1] = smoothedBounds[1] - 3
	elif rawBounds[1] > smoothedBounds[1]:
		smoothedBounds[1] = smoothedBounds[1] + 1
	
	if rawBounds[2] < smoothedBounds[2]:#smaller
		smoothedBounds[2] = smoothedBounds[2] - 1
	elif rawBounds[2] > smoothedBounds[2]:
		smoothedBounds[2] = smoothedBounds[2] + 3
	
	if rawBounds[3] < smoothedBounds[3]:#smaller
		smoothedBounds[3] = smoothedBounds[3] - 1
	elif rawBounds[3] > smoothedBounds[3]:
		smoothedBounds[3] = smoothedBounds[3] + 3
	
		
	#bypass smoothing and ar correction	
	
	
#	if 'smoothingValues' not in locals():#initialise  
#		smoothingValues = numpy.zeros((smoothingArraySize,4))
#		smoothingValues[ : ,0] = rawCenterPosition[0]#x
#		smoothingValues[ : ,1] = rawCenterPosition[1]#y
#		smoothingValues[ : ,2] = max(minWidth, rawBounds[2] - rawBounds[0])#w (limited)
#		smoothingValues[ : ,3] = max(minWidth, rawBounds[3] - rawBounds[1])#h (limited)

	
	#smoothing
#	smoothingValues = numpy.roll(smoothingValues,1, axis=0)

#	smoothingValues[0][0] = rawCenterPosition[0]#x
#	smoothingValues[0][1] = rawCenterPosition[1]#y
#	smoothingValues[0][2] = max(minWidth, rawBounds[2] - rawBounds[0])#w (limited)
#	smoothingValues[0][3] = max(minHeight, rawBounds[3] - rawBounds[1])#h (limited)

	
	#calc average/mean
#	smoothedAverages = [int(numpy.mean(smoothingValues[ : ,0])), int(numpy.mean(smoothingValues[ : ,1])), int(numpy.mean(smoothingValues[ : ,2])), int(numpy.mean(smoothingValues[ : ,3]))]
	#smoothedAverages = [int(stats.trim_mean(smoothingValues[ : ,0],0.1)), int(stats.trim_mean(smoothingValues[ : ,1],0.1)), int(stats.trim_mean(smoothingValues[ : ,2],0.1)), int(stats.trim_mean(smoothingValues[ : ,3],0.1))]

	
	#calculate current aspect ratio    
#	smoothedAR = smoothedAverages[2]/smoothedAverages[3]#w/h
	
	
#	if( smoothedAR > targetAR):
#		arHeight = smoothedAverages[2] * (1/targetAR)
#		arWidth = smoothedAverages[2]

#	else:
#		arHeight = smoothedAverages[3]
#		arWidth = smoothedAverages[3] * targetAR	
	
	#make coords for green box
#	smoothedBounds = [int(smoothedAverages[0]-(arWidth/2)), int(smoothedAverages[1]-(arHeight/2)), int(smoothedAverages[0]+(arWidth/2)), int(smoothedAverages[1]+(arHeight/2))]	
	

	
	

	#draw detection window
	cv2.rectangle(frame,(crop[2],crop[0]),(frame.shape[1]-crop[3],frame.shape[0]-crop[1]),(255,255,255), 1)

	#static center cross bg
	cv2.line(frame,((frame.shape[1]/2)-minWidth/2,frame.shape[0]/2),((frame.shape[1]/2)+minWidth/2,frame.shape[0]/2), (0,0,0), 2)#x
	cv2.line(frame,(frame.shape[1]/2,(frame.shape[0]/2)+10),(frame.shape[1]/2,(frame.shape[0]/2)-10), (0,0,0), 2)#y
	
	#static center cross
	cv2.line(frame,((frame.shape[1]/2)-minWidth/2,frame.shape[0]/2),((frame.shape[1]/2)+minWidth/2,frame.shape[0]/2), (0,255,0), 1)#x
	cv2.line(frame,(frame.shape[1]/2,(frame.shape[0]/2)+10),(frame.shape[1]/2,(frame.shape[0]/2)-10), (255,255,255), 1)#y


	#raw bounding box 
	cv2.rectangle(frame, (rawBounds[0], rawBounds[1]), (rawBounds[2], rawBounds[3]), (255, 0, 0), 1)
	
	#raw center spot   
	cv2.circle(frame,(rawCenterPosition[0],rawCenterPosition[1]), 4, (255,0,0), 1) 

	#smoothed bounding box    
	cv2.rectangle(frame, (smoothedBounds[0],smoothedBounds[1]), (smoothedBounds[2],smoothedBounds[3]), (0, 255, 0), 1)
	

	#smoothed center spot    
	#cv2.circle(frame,(smoothedAverages[0],smoothedAverages[1]), 4, (0,255,0), 1) 

	#scale
	#scaledPTZ[0] = int(interp(smoothedAverages[0],[0,frame.shape[1]],panFromTo))#pan
	#scaledPTZ[1] = int(interp(smoothedAverages[1],[0,frame.shape[0]],tiltFromTo))#tilt
	#scaledPTZ[2] = int(interp(smoothedAverages[2],[minWidth,frame.shape[1]],zoomFromTo))#zoom

	#expand for readout
	frame = cv2.copyMakeBorder(frame,30,0,0,0,cv2.BORDER_CONSTANT, value=[0,0,0])
   
	fps.stop()
	cv2.putText(frame,'X:{0:+}'.format(scaledPTZ[0]) + ' Y:{0:+}'.format(scaledPTZ[1])+ ' Z:{0}'.format(scaledPTZ[2]) +' FPS:{0}'.format(int(fps.fps()))+' {0:}'.format("." if pulse else ""),(10,20), font, 0.5,(255,255,255),1,cv2.LINE_AA) #readings
	cv2.putText(frame, '{0:}'.format("connected" if connected else "offline"),(500,20), font, 0.5,(255,255,255),1,cv2.LINE_AA) #readings

	
	#scaledPTZ[0] = scaledPTZ[0] + centerOffset[0]
	#scaledPTZ[1] = scaledPTZ[1] + centerOffset[1]
	
	cv2.imshow('frame',frame)
	fps.update()

def receive():
	global lastReceive
	global packet
	global currentZoom
	global dirZoom

	#process incoming data
	try:
		data = ptzSocket.recv(1)
		
		while(data):			
			packet.append(ord(data))
			if ord(data) == 0xff :#packet end 0xff
				if packet in messages:
					index = messages.index(packet)
					if index > 7: print messages[index+1]#only print errors
				else:
					if packet[0] == 0x90 and packet[1] == 0x50:#enquiry response
						currentZoom = (packet[2]*16**2)+ (packet[3]*16**1)+(packet[4]*16**0)
						#print str(currentZoom)+"/"+str(targetZoom)
						if(dirZoom == 1 and currentZoom >= targetZoom) or (dirZoom == -1 and currentZoom <= targetZoom):
							transmit(bytearray([0x81, 0x01, 0x04, 0x07,0x00,0xff]))#stop
							dirZoom = 0
							#print "zoom stop"
					else:
						for i in packet:
							print hex(i),
						print
						raise ValueError("unknown packet")
				packet = []
				lastReceive = time.time()
				
			data = ptzSocket.recv(1)
			
	except:#no data
		pass
		
	#test for timeout
	if(connected and not lookAroundStage and (time.time()-lastReceive > TIMEOUT)):
		print "connection timeout"
		connect()#reconnect
		#initSettings()	
		pass

def checkSchedule():
	now = datetime.datetime.now()

	if now.weekday() == day and startTime <= now.time() <= endTime:
	#if now.minute % 2 == 0:#even minutes
		if not connected:
			print "schedule start"	
			connect()
	elif connected:
			print "schedule stop"
			disconnect()

def centerCamera():
	global lastTransmit
	#reset to home
	print "center camera"	
	updateRemoteCamera([centerOffset[0],centerOffset[1],0], 0x18)#fastest pan to
	transmit(bytearray([0x81, 0x01, 0x04, 0x07,0x37,0xff]))#fastest zoom out
	lastTransmit = time.time()
	time.sleep(5)#wait for home

def lookAround():
	global lookAroundStage
	global lookAroundTimer
	global lastReceive
	
	if lookAroundStage:#currently looking around stage 1 (left)
		if time.time() - lookAroundTimer > lookAroundStageInterval:#time for next stage 
			if lookAroundStage == 1:#looked left
				lookAroundStage = 2
				lookAroundTimer = time.time()		
				print "looking right"
				updateRemoteCamera([panFromTo[1],centerOffset2[1],0])#look right
			
			elif lookAroundStage == 2:#looked right
				print "re-center on action"
				lookAroundStage = 3
				lookAroundTimer = time.time()
				updateRemoteCamera([scaledPTZ[0],scaledPTZ[1],0])#center on action
				
			elif lookAroundStage == 3:#start again
				lookAroundStage = False
				lookAroundTimer = time.time()
				lastReceive = time.time()#reset the timeout timer
				print "done looking"
					
	elif lookAroundInterval > 0 and time.time() - lookAroundTimer > lookAroundInterval:#start looking around
		lookAroundStage = 1
		lookAroundTimer = time.time()
		print "looking left"
		updateRemoteCamera([panFromTo[0],centerOffset2[1],0])#look left			
	
	else:
		return False #not looking around
	
	return True #is

if not offline:
	print "initial connect/setup"
	connect()
	disconnect()


while(1):#main loop	

	if forceConnect:
		if not connected:
			connect()
	else:
		checkSchedule()
	
	
	if connected and not offline:	
		receive()
	
	#zoom active, request status
	if connected and dirZoom is not 0 and ((time.time()-lastZoomRequest) > zoomTick):	
		transmit(bytearray([0x81, 0x09, 0x04, 0x47, 0xff]))#zoom request
		lastZoomRequest = time.time()


	processVideo()

	if connected and not offline:		
		if not lookAround():
			if time.time() - lastTransmit > UPDATE_RATE: #send normal update
				updateRemoteCamera(scaledPTZ)
				lastTransmit = time.time()
				pulse = not pulse
			

	#detect exit key
	k = cv2.waitKey(30) & 0xff
	if k == 27:
		break

print "shutting down"	
disconnect()
vs.release()
cv2.destroyAllWindows()
fps.stop()
time.sleep(1)
