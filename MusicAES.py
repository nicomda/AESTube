
import numpy as np
import pyaudio
import wave
import struct
import math
import os

filename = "prueba2.wav"
fs= 44100               #Sample Hz
scales = 8              #Amount of musical scales to work with (12 semitones)
detected_notes = []      #Array to store detected notes

def matching_freq(freq):
    freq_array = [16.35, 17.32, 18.35, 19.45, 20.60, 21.83, 23.12, 24.50, 25.96, 27.50, 29.14, 30.87] # 0 scale float values
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    scale_multiplier = 0
    current_note=0
    for i in range(len(freq_array)*scales):
        if(i%len(freq_array) == 0):
            freq_array=[element * 2 for element in freq_array]
            scale_multiplier += 1
        current_note = freq_array[i%len(notes)]
        if(freq < current_note): 
            return notes[(i)%len(notes)] + str(scale_multiplier)     
    return 'Unknown'
     

def note_detect(audio_file):
    #Clearing arrays to allow reuse of function


    file_length = audio_file.getnframes()
    sound  = np.zeros(file_length)

    for i in range(file_length):
        data = audio_file.readframes(1)
        data = struct.unpack("<h", data)
        sound[i] = int(data[0])

    sound = np.divide(sound, float(2**15))

    silence_window = sound * np.blackman(len(sound))
    f = np.fft.fft(silence_window)
    i_max = np.argmax(abs(f))
    print("Fourier (abs) value: " + str(i_max))
    freq = (i_max * fs)/len(sound)
    print("Frequency detected: " + str(freq) + " Hz")
    detected_notes = matching_freq(freq)
    return detected_notes


if __name__ == "__main__":
    
    sound_file = wave.open( filename , 'r')
    print("Approximated Note: " + str(note_detect(sound_file)))