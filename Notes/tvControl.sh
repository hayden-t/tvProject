#!/bin/bash

export DISPLAY=:0

path='/home/user/tvProject/'
playSocket=$path'play.sock'
recordSocket=$path'record.sock'
#src=$path'Content/sample4.mp4'
src1='rtsp://192.168.60.200:554/1' #hd
src2='rtsp://192.168.60.200:554/2' #sd
src3='rtsp://192.168.60.206:8554/live' #ipad - in schedule too
tmp=$path'Temp'
dest=$path'Sync'
filename="$tmp/`date '+%Y-%m-%d_%H-%M-%S'`.mp4"
udpAddress='239.0.0.1'

#--extraintf oldrc --rc-unix=$playSocket --rc-fake-tty

vlcPlay="vlc -R -f --no-osd --no-qt-error-dialogs $src3"
#vlcPlay="vlc -R -f --no-osd --no-qt-error-dialogs --aspect-ratio 5:4 $src3"

#vlcRecord="vlc -I oldrc --rc-unix=$recordSocket --rc-fake-tty $src2 --sout '#std{access=file,mux=mp4,dst='$filename'}'"

#vlcStream=" --sout '#duplicate{dst=display,dst=std{access=udp,mux=ts,dst=$udpAddress}}'"

#ffmpegPlay="ffplay -fs $src2"

ffmpegRecord="ffmpeg -i $src1 -metadata title="" -codec copy $filename"

if [ "$1" = 'play' ]
then
	echo "starting play"
	echo $$ > $path'play.pid'
	eval $vlcPlay
	

elif [ "$1" = 'record' ]
then
	echo "starting record"
	echo $$ > $path'record.pid'
	eval $ffmpegRecord
	

elif [ "$1" = 'stop' ]
then
	echo "stopping record"
	#echo stop | socat - UNIX-CONNECT:$recordSocket
	#echo quit | socat - UNIX-CONNECT:$recordSocket
	pkill -SIGINT -P $(cat $path'record.pid')
	mv $tmp/* $dest
	rm $path'record.pid'

elif [ "$1" = 'status' ]
then
	if [ "$2" = 'play' ]
	then
		result=$(echo is_playing | socat - UNIX-CONNECT:$playSocket 2>/dev/null | tr -d '\r')
		


	elif [ "$2" = 'record' ]
	then
		echo is_playing | socat - UNIX-CONNECT:$recordSocket 2>/dev/null | tr -d '\r'

	fi

	if [ "$result" = 1 ]
	then
		echo "1"
	else
		echo "0"
	fi

fi


