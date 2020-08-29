import base64
import hashlib
from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes

class AESCipher:
    def __init__(self, key): 
        self.key = hashlib.sha256(key.encode()).digest() # use SHA-256 over our key to get a proper-sized AES key

    def encrypt(self, source, encode=True):
        IV = get_random_bytes(AES.block_size)  # generate IV
        encryptor = AES.new(self.key, AES.MODE_CBC, IV)
        padding = AES.block_size - len(source) % AES.block_size  # calculating needed padding
        source += bytes([padding]) * padding 
        data = IV + encryptor.encrypt(source)  # store the IV at the beginning and encrypt
        return base64.b64encode(data).decode("latin-1") if encode else data

    def decrypt(self, source, decode=True):
        if decode:
            source = base64.b64decode(source.encode("latin-1"))
        IV = source[:AES.block_size]  # extract the IV from the beginning
        decryptor = AES.new(self.key, AES.MODE_CBC, IV)
        data = decryptor.decrypt(source[AES.block_size:])  # decrypt
        padding = data[-1]
        if data[-padding:] != bytes([padding]) * padding:
            raise ValueError("Invalid padding...")
        return data[:-padding]  # remove the padding