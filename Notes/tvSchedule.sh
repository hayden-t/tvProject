#!/bin/bash

#day='Friday'
#start=1500
#stop=1600

#day='Wednesday'
#start=1345
#stop=1530

#day=Tuesday
#start=1400
#stop=1425

#ncal -h |awk '/We/ {print $(NF)}'

nowDay=`date +%A`
nowTime=`date +%H%M`

streamTest="/usr/bin/ffprobe -v quiet rtsp://192.168.60.206:8554/live"

export DISPLAY=:0

if  ! pgrep -F /home/user/tvProject/play.pid >/dev/null;
then
	eval $streamTest
	if [ $? -eq 0 ]; #stream is up, play it
	then
    		echo "schedule play"
		bash /home/user/tvProject/tvControl.sh play
	fi
else	
	eval $streamTest
	if [ $? -ne 0 ]; #stream has ended, kill vlc
	then		
		echo "closing vlc"
		pkill -SIGINT -P $(cat '/home/user/tvProject/play.pid')
	fi

fi

if [ $nowDay = $day ] && [ $nowTime -ge $start ] && [ $nowTime -lt $stop ]
then
	if  ! pgrep -F /home/user/tvProject/record.pid >/dev/null;
	then
		echo "schedule record"
		bash /home/user/tvProject/tvControl.sh record
	fi

elif [ -f /home/user/tvProject/record.pid ]
then
	echo "schedule stop"
	bash /home/user/tvProject/tvControl.sh stop
fi

