
import numpy as np
import pyaudio
import wave
import struct
import math
import os, sys
import hashlib
from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
from base64 import b64encode
from base64 import b64decode
from pytube import YouTube


fs= 44100               #Sample Hz
scales = 8              #Amount of musical scales to work with (12 semitones)
detected_notes = []     #Array to store detected notes
detected_freqs = []     #Array to store detected frequencies

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
    window_size = int(file_length*0.025) 
    print('Longitud: '+str(window_size))
    
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
    print(*detected_freqs)
    clean_freqs = filterFrequencyArray(detected_freqs)
    print('Cleaned')
    print(*clean_freqs)
    for freq in clean_freqs:
            detected_notes.append(matchingFreq(freq))
    
    return removeRepeatedNotes(detected_notes)

def encrypt(plain_text, password):
    # generate a random salt
    salt = get_random_bytes(AES.block_size)

    # use the Scrypt KDF to get a private key from the password
    private_key = hashlib.scrypt(
        password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)

    # create cipher config
    cipher_config = AES.new(private_key, AES.MODE_GCM)

    # return a dictionary with the encrypted text
    cipher_text, tag = cipher_config.encrypt_and_digest(bytes(plain_text, 'utf-8'))
    return {
        'cipher_text': b64encode(cipher_text).decode('utf-8'),
        'salt': b64encode(salt).decode('utf-8'),
        'nonce': b64encode(cipher_config.nonce).decode('utf-8'),
        'tag': b64encode(tag).decode('utf-8')
    }

def decrypt(enc_dict, password):
    # decode the dictionary entries from base64
    salt = b64decode(enc_dict['salt'])
    cipher_text = b64decode(enc_dict['cipher_text'])
    nonce = b64decode(enc_dict['nonce'])
    tag = b64decode(enc_dict['tag'])
    
    # generate the private key from the password and salt
    private_key = hashlib.scrypt(
        password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)

    # create the cipher config
    cipher = AES.new(private_key, AES.MODE_GCM, nonce=nonce)

    # decrypt the cipher text
    decrypted = cipher.decrypt_and_verify(cipher_text, tag)

    return decrypted




if __name__ == "__main__":
    if(len(sys.argv) < 4 or sys.argv[1]=='-h'):
        print("***Usage steps***")
        print("----------------------------------------")
        print("To encrypt: AudioAES.py -e 'text_to_encript' <audiopassfile>")
        print("To decrypt: AudioAES.py -d 'encrypted_text' <audiopassfile>")
    try:
        YouTube('https://www.youtube.com/watch?v=kh1sF-sbkbw').streams.first().download()
        print(stream = yt.streams.filter(only_audio=True).first())
        stream.download()
        sound_file = wave.open( sys.argv[3] , 'r')
        filtered_notes= noteDetect(sound_file)
        print("Approximated Notes: " + str(filtered_notes))
    except IOError:
        print ("Error opening file")
    key=''
    for note in detected_notes:
        key += note
    print ("Key: " + key)
    enc_dict = encrypt(sys.argv[2],key)
    print ("Encrypted data:" + str(enc_dict))
    print("Original data:" + str(decrypt(enc_dict, key)))


    

    
    