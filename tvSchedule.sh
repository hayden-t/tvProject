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

day=null
start=0
stop=0


#ncal -h |awk '/We/ {print $(NF)}'

nowDay=`date +%A`
nowTime=`date +%H%M`



export DISPLAY=:0

if  ! pgrep -F /home/user/tvProject/play.pid >/dev/null;
then
    	echo "schedule play"
	#xrandr --output DIN --set "tv standard" pal
	#bash /home/user/tvProject/tvControl.sh play
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

