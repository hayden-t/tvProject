while read -r line
do
  newline="[$(date +%x-%X)] $line"
  echo $newline >> /home/user/tvProject/vlclogtime.txt
done
