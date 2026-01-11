import base64
import os
import settings
import sys
from Crypto.Util.Padding import pad, unpad
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

class DBCrypt():
    def encrypt(self, text, keyfile, keylen):
        self.key = os.urandom(keylen)
        cipher = AES.new(self.key, AES.MODE_CBC)
        encrypted = cipher.encrypt(pad(text.encode('utf-8'), AES.block_size))
        with open(keyfile, 'wb') as f:
            f.write(self.key)
            f.write(cipher.iv)
        print(base64.b64encode(encrypted))

    def readkey(self, keyfile, keylen):
        with open(keyfile, 'rb') as f:
            self.key = f.read(keylen)
            self.iv = f.read()

    def __init__(self, keyfile='.keys/db.key', keylen=256, engine_str=''):
        try:
            os.makedirs('.keys')
        except Exception as exc:
            pass
        keypath = os.path.join(settings.BASE_DIR, keyfile)
        keylen = int(keylen/8) 
        if os.path.exists(keypath):
            self.readkey(keypath, keylen)
        else:
            self.encrypt(
                engine_str,
                keypath, 
                keylen)

    def decrypt(self, encrypted):
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return unpad(cipher.decrypt(base64.b64decode(encrypted)), AES.block_size).decode()

