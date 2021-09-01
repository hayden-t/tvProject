#!/usr/bin/env python

#written by hayden thring httech.com.au

import datetime
import tvControl

now = datetime.datetime.now()

day = now.isoweekday()
time = now.strftime('%H%M')

#print day
#Monday is 1
#can have stop then start on same minute, will both be run
playlist = [
	{'day': 1, 'start': '1000', 'stop': '', 'record': '', 'file': '/home/user/Videos/Andre Rieu - Life is Beautiful.mp4'},
	{'day': 1, 'start': '1400', 'stop': '', 'record': '', 'file': '/home/user/Videos/Slim Dusty - Concert For Slim.mp4'},

	{'day': 2, 'start': '1000', 'stop': '', 'record': '', 'file': '/home/user/Videos/Andre Rieu - Magic Of The Musicals.mp4'},
	{'day': 2, 'start': '1400', 'stop': '', 'record': '', 'file': '/home/user/Videos/Daniel ODonnell - Can You Feel the Love.mp4'},

	{'day': 3, 'start': '1000', 'stop': '', 'record': '', 'file': '/home/user/Videos/Daniel ODonnell - From The Heartland.mp4'},
	{'day': 3, 'start': '1400', 'stop': '', 'record': '', 'file': '/home/user/Videos/alan-jackson-precious-memories-gospel-songs.mp4'},

	{'day': 4, 'start': '1400', 'stop': '', 'record': '', 'file': '/home/user/Videos/Daniel ODonnell - Rock And Roll Show.mp4'},
	
	{'day': 5, 'start': '1100', 'stop': '', 'record': '', 'file': '/home/user/Videos/30 Greatest Hymns with Lyrics.mp4'},
	{'day': 5, 'start': '1300', 'stop': '1400', 'record': '', 'file': 'rtsp://192.168.60.205:554/1'},#happy hour
	{'day': 5, 'start': '1400', 'stop': '1500', 'record': True, 'file': 'rtsp://192.168.60.205:554/1'},#happy hour - record
	{'day': 5, 'start': '1500', 'stop': '1600', 'record': '', 'file': 'rtsp://192.168.60.205:554/1'},#happy hour

	{'day': 6, 'start': '1000', 'stop': '', 'record': '', 'file': '/home/user/Videos/Slim Dusty - The Very Best Of Slim Dusty.mp4'},
	{'day': 6, 'start': '1400', 'stop': '', 'record': '', 'file': '/home/user/Videos/Andre Rieu - Live In Sydney.mp4'},

	{'day': 7, 'start': '0900', 'stop': '', 'record': '', 'file': '/home/user/Videos/church_karaoke.mp4'},
	{'day': 7, 'start': '1400', 'stop': '', 'record': '', 'file': '/home/user/Videos/Daniel ODonnell - The Gospel Show.mp4'},

	#{'day': 7, 'start': '1431', 'stop': '1432', 'record': '', 'file': 'rtsp://192.168.60.205:554/1'},#test
]


vlcDetectEnd = tvControl.vlcDetectEnd()
tabletStatus = tvControl.tabletStatus()


#print("ping")

if vlcDetectEnd and not tabletStatus:#was streaming but stream ended
	print(now, " Tablet Stopped")
	tvControl.vlcStop()

elif not vlcDetectEnd and tabletStatus:#stream is up, vlc not streaming
	print(now,  " Tablet Started")
	tvControl.vlcPlay(tvControl.tabletUrl, True, True, False)


if not tabletStatus:
	for item in playlist:
		if item['day'] == day and item['start'] == time:
			print(now, " Video Started")			
			tvControl.vlcPlay(item['file'], item['stop'], False, item['record'])		
		if item['day'] == day and item['stop'] and item['stop'] == time:
			print(now, " Stop Time")
			tvControl.vlcStop()
