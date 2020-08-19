#!/bin/bash
echo "---------------------"
echo "Installing ffmpeg ..."
echo "---------------------"
cd /root/Desktop/
git clone git://source.ffmpeg.org/ffmpeg.git ffmpeg
cd ffmpeg
./configure
make
make install
cd ..
rm -rf ffmpeg
echo "-----------------------------"
echo "FFMPEG Installation Finished."
echo "-----------------------------"
