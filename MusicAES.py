
import numpy as np
import pyaudio
import wave
import struct
import math
import os

filename = "prueba2.wav"
fs= 44100               #Sample Hz
scales = 8              #Amount of musical scales to work with (12 semitones)
window_size = 2800      #Will be used to identify silences. (Read https://en.wikipedia.org/wiki/Window_function for more info)
detected_notes = []     #Array to store detected notes
detected_freqs = []     #Array to store detected frequencies
filtered_freqs = []

#Function to find the closer element in an array
def closest(lst, K): 
    return lst[min(range(len(lst)), key = lambda i: abs(lst[i]-K))] 

#Function to match Hz with note name
def matchingFreq(freq):
    freq_array = [27.500, 29.135, 30.868, 32.703, 34.648, 36.708, 38.891, 41.203, 43.654, 46.249, 48.999, 51.913] # 0 scale float values
    notes = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']
    scale_multiplier = 0
    current_note=0
    for i in range(len(freq_array)*scales):
        if(i%len(freq_array) == 0):
            freq_array=[element * 2 for element in freq_array]
            scale_multiplier += 1
        current_note = freq_array[i%len(notes)]
        if(freq < current_note):  
            return notes[freq_array.index(closest(freq_array, freq))] + str(scale_multiplier)  #TODO Still some adjustment on window must be done. Disable scale_mult for more accuracy.   
    return 'Unknown'

#Function that filter silences, not audible and repeated data from sample.
def filterFrequencyArray():                                                                                                                 #and silences and gets the notes for the found frequencies 
    j=0              
    temp=1
    while(j<len(detected_freqs)-4):
        if(detected_freqs[j]==0):
            temp=1
        if((detected_freqs[j]!=temp) & (detected_freqs[j]!=0)):
            if(detected_freqs[j]==detected_freqs[j+1]):
                temp=detected_freqs[j]
                if(temp<20000):      #Discard not audible freqs above 20KHz
                    filtered_freqs.append(temp)
        j=j+1 
#Almost all the magic is done in this function. It reads, splits, operates and detect frequencies.
def noteDetect(audio_file):
    file_length = audio_file.getnframes()
    #Clearing arrays to allow reuse of function
    detected_freqs.clear()

    for i in range(int(file_length/window_size)):
        data = audio_file.readframes(window_size)
        data = struct.unpack('{n}h'.format(n=window_size), data)
        sound = np.array(data) 
        #sound = np.divide(sound, float(2**15))
        window = sound * np.blackman(len(sound))
        f = np.fft.fft(sound)
        i_max = np.argmax(abs(f))
        #DEBUG print("Fourier (abs) value: " + str(i_max))
        freq = round((i_max * fs)/len(sound),3) #Freqs rounded to 3 decimals
        detected_freqs.append(freq)
        #DEBUG print("DEBUG Unfiltered Frequency detected: " + str(freq) + " Hz")
    filterFrequencyArray()
    for freq in filtered_freqs:
            detected_notes.append(matchingFreq(freq))
    return detected_notes


if __name__ == "__main__":
    
    sound_file = wave.open( filename , 'r')
    print("Approximated Notes: " + str(noteDetect(sound_file)))
    print (*filtered_freqs)
    