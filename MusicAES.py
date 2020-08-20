
import numpy as np
import pyaudio
import wave
from pydub import AudioSegment
import struct
import math
import os, sys, glob, getopt
import hashlib
import subprocess
import base64
from requests import exceptions
from pytube import YouTube
from AESCipher import AESCipher 

fs= 44100               #Sample Hz
scales = 8              #Amount of musical scales to work with (12 semitones)
duration = 0            #Audio duration in ms to control splitting
detected_notes = []     #Array to store detected notes
detected_freqs = []     #Array to store detected frequencies
downloads_path = '/tmp/media_tmp'
key= ''

def printHelp():
    print("***Usage steps***")
    print("----------------------------------------")
    print("To encrypt text: AudioAES.py -e -t 'text_to_encrypt' 'YoutubeLink' -s 'start_seconds' 'end_seconds'")
    print("To encrypt file: AudioAES.py -e -f <file_to_encrypt> 'YoutubeLink' -s 'start_seconds' 'end_seconds'")
    print("To encrypt text: AudioAES.py -d -t 'text_to_encrypt' 'YoutubeLink' -s 'start_seconds' 'end_seconds'")
    print("To encrypt file: AudioAES.py -d -f <file_to_encrypt> 'YoutubeLink' -s 'start_seconds' 'end_seconds'")
    print("If you just call the program without arguments, it will ask for them in interactive mode")

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
    audio_file.close() #Close audio file
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
    print('[Error] splitting file. Maybe trying to split bigger than audio.')    
    return False

def convertToWav(file_name):
        #FFMpeg conversion. Bitrate 96kbps, Audio Channels 1 (Mono), Bitrate 44.1kHz
        command= f"ffmpeg -i '{downloads_path}/{file_name}.mp4' -ab 96k -ac 1 -ar 44100 -vn '{downloads_path}/{file_name}.wav'"
        #DEBUG print(command) 
        print(f'Converting to wav: {file_name}')
        subprocess.call(command, shell=True)

def getYoutubeMedia(ytlink, isAudio=True):
    try:
        print('Downloading stream (audio), wait a bit') #TODO Maybe video streams support
        yt = YouTube(ytlink, on_complete_callback=downloadedTrigger)
        stream = yt.streams.filter(only_audio=isAudio).first()
        stream.download(downloads_path)
        return stream.default_filename
    except request.exceptions.RequestException:
        print ("[Error] downloading file.")
        sys.exit()

def downloadedTrigger(stream, file_handle):
    print('Download Completed')

def binReadToB64(filepath):
    try:
        raw_data = open(filepath, "rb").read()
        b64_string = base64.b64encode(raw_data)
        return b64_string
    except IOError:
        print('[Error] Reading file to encrypt')
        sys.exit()

def binWriteToFile(data,filename):
    try:
        newFile = open(filename, 'wb')
        newFile.write(bytes(data, 'utf-8'))
        newFile.close()
    except IOError:
        print('[Error] Writing to file')

if __name__ == "__main__":
    ytLink = ''
    opData = ''
    opMode = ''
    opType = ''
    isInteractive = False
    isSplitted = False
    isInvalid = False
    startTime = 0
    endTime = 0
    #Interactive Mode Questions
    if(len(sys.argv)==1):
        isInteractive = True
        ytLink = input('(1/6)YouTube link that you will use as passphrase: ')
        print('(2/6) Do you wanna use audio splitting to increase security?')
        if(input('For decrypt mode, splitting must be selected if you selected it to encrypt(y/N): ') == 'y'):
            isSplitted = True
        opMode = input('(5/6) Do you want to encrypt or decrypt?(E/D): ')
        opType = input('(6/6) Which kind?(T)ext or (F)ile: ')
        #TODO INTERACTIVE MODE
    #Print help
    elif(sys.argv[1]=='-h' or sys.argv[1]=='--help'):
        printHelp()
    #Getting Arguments from console    
    else:
        if(sys.argv[1]=='-e'):
            opMode = 'E'
        elif(sys.argv[1]=='-d'):
            opMode = 'D'
        else:
            isInvalid = True
        if(sys.argv[2]=='-t'):
            opType = 'T'
        elif(sys.argv[2]=='-f'):
            opType = 'F'
        else:
            isInvalid = True
        if(len(sys.argv)>4):
            if(sys.argv[5]=='-s'):
                isSplitted = True
                startTime=sys.argv[6]
                endTime=sys.argv[7]
            else:
                isInvalid = True
        ytLink = sys.argv[4]
        opData = sys.argv[3]
    #Creating tmp directory
    if(not os.path.isdir(downloads_path)):
        try:
            os.mkdir(downloads_path)
        except OSError:
            print (f'Creation of the directory {downloads_path} failed')
        else:
            print (f'Successfully created the directory {downloads_path} ')
    #Downloading audio
    file_name=getYoutubeMedia(ytLink,isAudio=True) #TODO Set ytLink
    print(file_name)
    filename_no_ext = file_name[0:len(file_name)-4]
    print(filename_no_ext)     #Just deletes .mp4
    #Converting to wav
    convertToWav(filename_no_ext)
    #Splitting if selected 
    if(isSplitted):
        startTime= input('(3/6) Choose splitting start in seconds: ')
        finishTime = input('(4/6) Choose splitting end  in seconds: ')
        if(splitAudio(startTime,endTime,filename_no_ext)):
            sys.exit() #Exit if there's problems while splitting
        soundProcessing(f'{filename_no_ext}_split')     #Sound processing
    else:
        soundProcessing(filename_no_ext)
    #Creating key for encryption
    key=''
    for note in detected_notes:
        key += note 
    aes=AESCipher(key)
    if(opMode=='E'): #Encryption
        if(opType=='T'): #Text mode
            if(isInteractive):
                opData=input('(6/6) Text to encrypt?: ')
            print(f'Encrypted text: {aes.encrypt(opData)}')
        else:   #File mode
            if(isInteractive):
                opData = input('(6/6) File to encrypt?: ')
            encryptedData = aes.encrypt(base64.b64decode(binReadToB64(opData)).decode('utf-8'))
            binWriteToFile(base64.decodebytes(encryptedData), f'{opData}.aenc')
    else:
        if(opType=='T'): #Text mode
            if(isInteractive):
                opData=input('(6/6) Text to decrypt?: ')
            print(f'Decrypted text: {aes.decrypt(opData)}')
        else:   #File mode
            if(isInteractive):
                opData = input('(6/6) File to decrypt?: ')
            decryptedData = aes.decrypt(binReadToB64(opData))
            binWriteToFile(decryptedData, opData[0:len(opData)-5]) #Binary write deleting aenc extension

    files = glob.glob(f'{downloads_path}/*')
    for f in files:
        os.remove(f)    #Deleting remaining media files
        


    

    
    