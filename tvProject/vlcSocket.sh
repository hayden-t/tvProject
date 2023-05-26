#!/bin/bash

echo $1 | socat - UNIX-CONNECT:./vlc.sock

