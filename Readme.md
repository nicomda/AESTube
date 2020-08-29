# AESTube
This is a PoC using youtube audio to encrypt text/files. It uses AES-256.
How it's done:
1. Download MP4 audio stream from a YouTube link.
2. MP4 audio is converted to WAV..
3. WAV is processed through FFT to extract audio frequencies.
4. Frequencies are mapped to musical notes.
5. These notes are used as the passphrase for AES encryption.
6. That's all folks 😎

In addition to this, I created some audio splitting mechanism that allows you to trim it, improving the security.
## Installation
Assure that you have python3 installed on your system.
```sh
#Clone this repo
git clone https://github.com/nicomda/AESTube.git

#Install FFmpeg in your system 
cd AESTube
sudo chmod +x ffmpeg-installer.sh
./ffmpeg-installer.sh

#Install if not installed
pip3 install virtualenv

#Creating virtualenv
python3 -m venv AESTube

#Activating venv
source ./bin/activate

#Installing required libraries in the virtual enviroment
sudo apt-get install python-pyaudio python3-pyaudio
pip3 install -r requirements.txt
pip3 install git+https://github.com/nficano/pytube.git --upgrade
#At the moment there are some issues with pytube so, to make it work...
#Go to lib/pytube/extract.py and delete this line 
#r";ytplayer\.config\s*=\s*({.*?});",
#Will be solved ASAP maybe updating library or changing to another. 
```
## Quick Start
```bash
#To encrypt text: 
./AESTube.py -e -t 'text_to_encrypt' -l 'YoutubeLink' -s 'start_seconds' 'end_seconds'

#To decrypt files: 
./AESTube.py -e -t 'filepath' -l 'YoutubeLink' -s 'start_seconds' 'end_seconds'
```

### **Available arguments:**

| Argument        | What it does | Optional |
| --------------- |:-------------|:---------:| 
| -e                               |Encrypt mode | 
| -d                               |Decrypt mode
| -t                               |String data
| -f <file_to_encrypt>             |File to encrypt
| -l, --yt_link= 'Youtube link'    |Audio that will be used to get passphrase
| -s                               |Splitted mode. Will get just a part of the audio. If used, you must set start_time and end_time args |✔
| --start_time=                    |Start of the split in seconds |✔
| --end_time=                      |Start of the split in seconds |✔
| -o, --output_path=               |Path where output will be created |On progress
| -a                               |Interactive mode (Will ask for options) |✔

