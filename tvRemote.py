#!/usr/bin/python3
import os
import datetime
import json

import tvControl

import cgitb
cgitb.enable()

#called by apache2 cgi-bin
#a2enmod cgi
#chown root:user (filename)
#chmod 775 (filename)
#ln -s filename /usr/lib/cgi-bin/

now = datetime.datetime.now()

cameraSource = [{"day": "", "start": "", "stop": "", "record": "True", "file": "rtsp://192.168.60.205:554/1"}]
blankSource = [{"day": "", "start": "", "stop": "", "record": "False", "file": "vlc://quit"}]

queryString = os.environ.get('QUERY_STRING')

print("Content-Type: text/html;charset=utf-8")
print ("Content-type:text/html\r\n")
print("<title>Channel 700 control</title>")
print("<H2>Channel 700 control</H2>")
print("<style>body{padding:30px}table, th, td{border: thin solid grey;text-align:left;padding:5px;}</style>")

#print(queryString)
#print(os.getuid())

try:
	f = open("/home/user/tvProject/tvRemote.json", "r")
	schedule = json.load(f)
except:
	f = open("/home/user/tvProject/tvSchedule.json", "r")
	schedule = json.load(f)
	

if(queryString):
	f = open("/home/user/tvProject/tvRemote.json", "w")
	if('start' in queryString or 'pause' in queryString):
	
		length = int(queryString.split('=')[-1])
		#print(length)
		
		if('start' in queryString):
			playlist = cameraSource
		elif('pause' in queryString):
			playlist = blankSource

		
		start = now + datetime.timedelta(minutes=1)
		playlist[0]['day'] = now.isoweekday()
		playlist[0]['start'] = start.strftime('%H%M')
		
		stop = start + datetime.timedelta(hours=length)
		playlist[0]['stop'] = stop.strftime('%H%M')
		

		f.write(json.dumps(playlist))
		
		print('<p>Option will start for '+ str(length) +' hour/s within 1 minute</p>')
		
		
	elif(queryString == 'stop=1'):	
		
		print('<p>Stream stopped</p>')
		#f.write('')
		tvControl.vlcStop()
	
	print("<p><a href='/cgi-bin/tvRemote.py'>Return to Menu</a></p>")	
	f.close()
	
else:
	print("<p><a style='display:inline-block;padding:10px;border:thin solid blue;margin-left:10px;' href='/cgi-bin/tvRemote.py?start=1'>Start camera and record for 1 Hour</a>")
	print(" <a style='display:inline-block;padding:10px;border:thin solid blue;margin-left:10px;'  href='/cgi-bin/tvRemote.py?start=2'>Start camera and record for 2 Hour</a>")
	print(" <a style='display:inline-block;padding:10px;border:thin solid blue;margin-left:10px;' href='/cgi-bin/tvRemote.py?start=3'>Start camera and record for 3 Hour</a></p>")

	print("<p><a style='display:inline-block;padding:10px;border:thin solid red;color:red;margin-left:10px;' href='/cgi-bin/tvRemote.py?pause=1'>Pause schedule for 1 Hour</a>")
	print(" <a style='display:inline-block;padding:10px;border:thin solid red;color:red;margin-left:10px;'  href='/cgi-bin/tvRemote.py?pause=2'>Pause schedule for 2 Hour</a>")
	print(" <a style='display:inline-block;padding:10px;border:thin solid red;color:red;margin-left:10px;' href='/cgi-bin/tvRemote.py?pause=3'>Pause schedule for 3 Hour</a></p>")
	
	print("<p><a style='display:inline-block;padding:10px;border:thin solid blue;margin-left:10px;' href='/cgi-bin/tvRemote.py?stop=1'>Cancel camera/pause</a></p>")
	
	print('<h3>Current day: '+str(now.isoweekday())+' time: '+now.strftime('%H%M')+'</h3>')

	print('<h3>Current playlist:</h3>')
	print('<table><tr><th>Day</th><th>Start</th><th>Source</th></tr>')
	
	for item in schedule:
		print('<tr>')
		print('<td>'+str(item['day'])+'</td>')
		print('<td>'+str(item['start'])+'</td>')
		print('<td>'+str(item['file'])+'</td>')
		print('</tr>')

	print('</table>')


