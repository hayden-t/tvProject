#!/usr/bin/env python2.7

#written by hayden thring httech.com.au

import datetime
import os
import sys
import subprocess
import shlex
import json
import signal

path='/home/user/tvProject/'

#src=path+'Content/sample4.mp4'
#src1='rtsp://192.168.60.200:554/1' #hd
#src2='rtsp://192.168.60.200:554/2' #sd
tabletUrl='rtsp://192.168.60.206:8554/live' #ipad - in schedule too

vlcRecordDest=path+"Recorded/"+datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")+".mp4"
#0 0 * * * sshpass -p password rsync --remove-source-files -avz --progress /home/user/tvProject/Recorded/ rsync@192.168.60.250:happyHour >> /home/user/tvProject/cron.log

my_env = os.environ
my_env["DISPLAY"]=':0'
my_env["XDG_RUNTIME_DIR"]='/run/user/1000'

#(echo "volume 256";cat) | 
vlcCommand = '/snap/bin/vlc -L -f --codec=ffmpeg --rtsp-frame-buffer-size=500000 --no-volume-save "{source}" {quit} {record}'
vlcCommandQuit = 'vlc://quit'
vlcCommandRecord = '--sout \'#duplicate{dst=display,dst="std{access=file,mux=mp4,dst='+vlcRecordDest+'}"}\'' #no transcode
#vlcCommandRecord = '--sout \'#duplicate{dst=disp

vlcStateFile = path+'vlcState.txt'
tabletTest = '/usr/bin/ffprobe -v quiet '+tabletUrl


if os.path.isfile(vlcStateFile):
	vlcState = json.load(open(vlcStateFile, "rb"))
else:
	vlcState = {'detectEnd': False, 'pid': 0}

#print(vlcState['pid'])

def vlcStop():
	print('kill '+str(vlcState['pid']))
	try:
		os.remove(vlcStateFile)
		os.kill(vlcState['pid'], 2)	#SIGINT
	except:
		print('pid not running')

def vlcDetectEnd():#used by tablet
	#if vlcState['pid']:
		#try:
		#	os.kill(vlcState['pid'], 0)
		#except OSError:
		#	return False
		#else:
		#	return True #running
	#else:
	#	return False
	return vlcState['detectEnd']

def vlcPlay(source, stopTime, detectEnd, record):#todo record
	if vlcState['pid']:
		vlcStop()
	print('starting vlc')
	os.system('killall chrome')

	command = vlcCommand.format( source = source,quit=vlcCommandQuit if not stopTime else '',record=vlcCommandRecord if record == 'True' else '')

	process = subprocess.Popen(shlex.split(command), env=my_env)


	print(process.pid)


	state = {'detectEnd': detectEnd, 'pid': process.pid}

	json.dump(state, open(vlcStateFile, "w"))

def tabletStatus():
	res = os.system(tabletTest)
	if res == 0:
		return True
	else:
		return False



