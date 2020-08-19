
import numpy as np
import pyaudio
import wave
from pydub import AudioSegment
import struct
import math
import os, sys, glob
import hashlib
import subprocess
from requests import exceptions
from pytube import YouTube
from AESCipher import AESCipher 

fs= 44100               #Sample Hz
scales = 8              #Amount of musical scales to work with (12 semitones)
duration = 0            #Audio duration in ms to control splitting
detected_notes = []     #Array to store detected notes
detected_freqs = []     #Array to store detected frequencies
downloads_path = 'media_tmp'
key= ''

def printHelp():
    print("***Usage steps***")
    print("----------------------------------------")
    print("To encrypt text: AudioAES.py -e -t 'text_to_encrypt' <YoutubeLink>")
    print("To encrypt file: AudioAES.py -e -f 'file_to_encrypt' <YoutubeLink>")
    print("To encrypt text: AudioAES.py -d -t 'text_to_encrypt' <YoutubeLink>")
    print("To encrypt file: AudioAES.py -d -f 'file_to_encrypt' <YoutubeLink>")
    print("If you just call the program without arguments, it will ask for them")

#Function to find the closer element in an array
def closest(lst, K): 
    return lst[min(range(len(lst)), key = lambda i: abs(lst[i]-K))] 

#Function to match Hz with note name
def matchingFreq(freq):
    freq_array = [16.351, 18.354, 20.601, 21.827, 24.499, 27.500, 30.868] # 0 scale float values
    notes = ['C', 'D', 'E', 'F', 'G' , 'A', 'B']
    scale_multiplier = 0    #Could be used to restrict notes by multiples
    current_note=0
    for i in range(len(freq_array)*scales):
        if(i%len(freq_array) == 0):
            freq_array=[element * 2 for element in freq_array]
            scale_multiplier += 1
        current_note = freq_array[i%len(notes)]
        if(freq < current_note):  
            return notes[freq_array.index(closest(freq_array, freq))] + str(scale_multiplier-1)
    return 'Unknown'

#Function that filter silences, not audible and repeated data in found freqs.
def filterFrequencyArray(unfiltered_freqs):                                      
    filtered_freqs=[]
    for i in range (len(unfiltered_freqs)-1):
            if(unfiltered_freqs[i]>15.0 and unfiltered_freqs[i]<8000):
                if(matchingFreq(unfiltered_freqs[i])!=matchingFreq(unfiltered_freqs[i+1])):
                    filtered_freqs.append(unfiltered_freqs[i])
    return filtered_freqs

#Removes consecutive duplication in final notes array.
def removeRepeatedNotes(detected_notes):
    filtered_notes=[]
    for i in range(len(detected_notes)-1):
        if(detected_notes[i]!=detected_notes[i+1]):
            filtered_notes.append(detected_notes[i])
    filtered_notes.append(detected_notes[i+1])        
    return filtered_notes        
    
#Almost all the magic is done in this function. It reads, splits, operates and detect frequencies.
def noteDetect(audio_file):
    file_length = audio_file.getnframes()
    window_size = int(file_length*0.01) 
    print(f'Audio Length: {str(window_size)} bytes')
    
    #Clearing arrays to allow reuse of function
    detected_freqs.clear()

    for i in range(int(file_length/window_size)):
        data = audio_file.readframes(window_size)
        data = struct.unpack('{n}h'.format(n=window_size), data)
        sound = np.array(data) 
        #sound = np.divide(sound, float(2**15))
        #window = sound * np.blackman(len(sound))
        f = np.fft.fft(sound)
        i_max = np.argmax(abs(f))
        #DEBUG print("Fourier (abs) value: " + str(i_max))
        freq = round((i_max * fs)/len(sound),3) #Freqs rounded to 3 decimals
        detected_freqs.append(freq)
    #DEBUGprint('-----RAW Frequencies array-----')
    #DEBUGprint(*detected_freqs)
    clean_freqs = filterFrequencyArray(detected_freqs)
    #DEBUGprint('-----Cleaned Frequencies array-----')
    #DEBUGprint(*clean_freqs)
    for freq in clean_freqs:
            detected_notes.append(matchingFreq(freq))
    
    return removeRepeatedNotes(detected_notes)

def soundProcessing(file_name):
    try:
        sound_file = wave.open( f'{downloads_path}/{file_name}.wav', 'r')
        print('Conversion completed. Now starting to analize.')
        print('----------------------------------------------')
        filtered_notes= noteDetect(sound_file)
        #DEBUG print("Approximated Notes: " + str(filtered_notes))
    except IOError:
        print('[Error] reading file')

def splitAudio(t1,t2,input_file):
    start_time= int(t1)*1000 #Works in ms
    finish_time= int(t2)*1000
    newAudio = AudioSegment.from_wav(f'{downloads_path}/{input_file}.wav')
    duration = len(newAudio)
    if(start_time<duration and (duration-start_time)>finish_time and finish_time>start_time):
        newAudio = newAudio[start_time:finish_time]
        filename_no_ext = file_name[0:len(file_name)-4]     #Just deletes extension
        filename_output = f'{filename_no_ext}_split.wav'
        newAudio.export(f'{downloads_path}/{filename_output}', format='wav')
        return True
    print('[Error] splitting file')    
    return False


def convertToWav(file_name):
        #FFMpeg conversion. Bitrate 96kbps, Audio Channels 1 (Mono), Bitrate 44.1kHz
        command= f"ffmpeg -i '{downloads_path}/{file_name}.mp4' -ab 96k -ac 1 -ar 44100 -vn '{downloads_path}/{file_name}.wav'"
        #DEBUG print(command) 
        print(f'Converting to wav: {file_name}')
        subprocess.call(command, shell=True)

def getYoutubeMedia(isAudio=True):
    try:
        ytlink = input('YouTube link that you will use as passphrase: ')
        print('Downloading stream (audio), wait a bit') #TODO Maybe video streams support
        yt = YouTube(ytlink, on_complete_callback=downloadedTrigger)
        stream = yt.streams.filter(only_audio=isAudio).first()
        stream.download(downloads_path)
        return stream.default_filename
    except request.exceptions.RequestException:
        print ("[Error] downloading file.")

def downloadedTrigger(stream, file_handle):
    print('Download Completed')

if __name__ == "__main__":
    if(sys.argv[0]=='-h' or sys.argv[0]=='--help'):
        printHelp()
    else:
        file_name=getYoutubeMedia(isAudio=True)
        print(file_name)
        filename_no_ext = file_name[0:len(file_name)-4]
        print(filename_no_ext)     #Just deletes .mp4
        convertToWav(filename_no_ext)
        print('(2/6) Do you wanna use audio splitting to increase security?')
        isSplitted=input('For decrypt mode, splitting must be selected if you selected it to encypt(y/N): ')
        if(isSplitted=='y'):
            startTime= input('(3/6) Choose splitting start in seconds: ')
            finishTime = input('(4/6) Choose splitting end  in seconds: ')
            splitAudio(startTime,finishTime,filename_no_ext)
            soundProcessing(f'{filename_no_ext}_split')
        else:
            soundProcessing(filename_no_ext)
        opMode = input('(5/6) Do you want to encrypt or decrypt?(E/D): ')
        opText = ''
        key=''
        for note in detected_notes:
            key += note 
        aes=AESCipher(key)
        if(opMode=='E'):
            opText=input('(6/6) Text to encrypt?: ')
            print(f'Encrypted text: {aes.encrypt(opText)}')
        else:
            opText=input('(6/6) Text to decrypt?: ')
            print(f'Decrypted text: {aes.decrypt(opText)}')
        #COMMENT KEY PRINTING ON PRODUCTION
        #DEBUG print ("Key: " + key)
        files = glob.glob(f'{downloads_path}/*')
        for f in files:
            os.remove(f)
        


    

    
    