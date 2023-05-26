#!/bin/bash

export DISPLAY=:0
export XDG_RUNTIME_DIR=/run/user/1000
#export HOME=/home/user/tvProject/ 

path='/home/user/tvProject/'
playlist='/home/user/tvProject-manager/html/playlist/playlist.xspf'
#playlist='/home/user/tvProject/temp.xspf'

md5sum $playlist > $path'playlist.md5'

#become vlc, if window closed will be in hang state, use kill -9 pid
#--intf=dummy --random
exec /snap/bin/vlc --extraintf=oldrc --rc-unix=$path'vlc.sock' --rc-fake-tty --loop  --fullscreen --codec=ffmpeg--log-verbose=0 $playlist
