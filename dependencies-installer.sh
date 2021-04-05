#!/bin/bash
echo "Installing ffmpeg ..."
echo "---------------------"
sudo apt update
sudo apt install ffmpeg 
echo "Installing pyaudio dependencies ..."
echo "---------------------"
sudo apt install libasound-dev portaudio19-dev
echo "Installing PyAudio3 ..."
echo "---------------------"
sudo apt install python3-pyaudio
echo "You must manually install python3 requirements. If you wanna use venv, README."
echo "Once done, you're ready to use AESTube. Enjoy it..."

