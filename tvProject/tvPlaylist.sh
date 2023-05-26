#!/bin/bash
#check if playlist changed and restart
path='/home/user/tvProject/'

RESULT1=`md5sum /home/user/tvProject-manager/html/playlist/playlist.xspf`

RESULT2=`cat /home/user/tvProject/playlist.md5` #must change name of playlist in here

if [ "$RESULT1" != "$RESULT2" ]; then
	echo "playlist updated, restarting"
	md5sum /home/user/tvProject-manager/html/playlist/playlist.xspf > $path'playlist.md5'
	
	echo "clear" | socat - UNIX-CONNECT:/home/user/tvProject/vlc.sock
	echo "add /home/user/tvProject-manager/html/playlist/playlist.xspf" | socat - UNIX-CONNECT:/home/user/tvProject/vlc.sock
fi
