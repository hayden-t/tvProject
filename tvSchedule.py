#!/usr/bin/env python2.7

#written by hayden thring httech.com.au

import datetime
import tvControl
import json

now = datetime.datetime.now()

day = now.isoweekday()
time = now.strftime('%H%M')

#print day
#Monday is 1
#can have stop then start on same minute, will both be run



f = open("/home/user/tvProject/tvSchedule.json", "r")
schedule = json.load(f)

try:
	f = open("/home/user/tvProject/tvRemote.json", "r")
	remote = json.load(f)
	#print(remote)
	if(remote):
		schedule= remote #overrides normal programming
		#print(schedule)
except Exception as e:
	#print(e)
	pass
	


vlcDetectEnd = tvControl.vlcDetectEnd()
tabletStatus = tvControl.tabletStatus()


#print("ping")

if vlcDetectEnd and not tabletStatus:#was streaming but stream ended
	print(now, " Tablet Stopped")
	tvControl.vlcStop()

elif not vlcDetectEnd and tabletStatus:#stream is up, vlc not streaming
	print(now,  " Tablet Started")
	tvControl.vlcPlay(tvControl.tabletUrl, True, True, False)


if not tabletStatus:#if tablet not playing check schedule
	for item in schedule:
		if item['day'] == day and item['start'] == time:
			print(now, " Video Started")
			tvControl.vlcPlay(item['file'], item['stop'], False, item['record'])
		if item['day'] == day and item['stop'] and item['stop'] == time:
			print(now, " Stop Time")
			tvControl.vlcStop()
			open("/home/user/tvProject/tvRemote.json", "w").close()#clear remote playlist
