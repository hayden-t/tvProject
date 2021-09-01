#!/bin/bash

path='/home/user/tvProject/'

RESULT1=`md5sum /var/www/html/playlist/playlist.xspf`

RESULT2=`cat /home/user/tvProject/playlist.md5` #must change name of playlist in here

if [ "$RESULT1" != "$RESULT2" ]; then
	echo "playlist updated, restarting"
	pkill -SIGINT -P $(cat $path'play.pid')
	bash /home/user/tvProject/tvControl.sh play
fi
