from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from dotenv import load_dotenv
import os

load_dotenv()

KEY = os.getenv('ENCRYPTION_KEY')
if not KEY:
    raise ValueError("❌ ERRORE: ENCRYPTION_KEY non impostata. Aggiungila nel file .env!")

try:
    KEY = bytes.fromhex(KEY)
except ValueError:
    raise ValueError("❌ ERRORE: ENCRYPTION_KEY deve essere in formato esadecimale!")

def encrypt_file(file_data):
    cipher = AES.new(KEY, AES.MODE_CBC)
    encrypted_data = cipher.encrypt(pad(file_data, AES.block_size))
    return cipher.iv + encrypted_data

def decrypt_file(encrypted_data):
    iv = encrypted_data[:16]
    cipher = AES.new(KEY, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(encrypted_data[16:]), AES.block_size)

