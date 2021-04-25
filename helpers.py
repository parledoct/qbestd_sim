import hashlib, os, shutil

from pydub import AudioSegment
from typing import List
from fastapi import FastAPI, File, UploadFile

def wav_to_s3files(upload_path: str, wav_path: str, mp3_path: str):
    s = AudioSegment.from_wav(upload_path).set_channels(1).set_frame_rate(16000)
    
    s.export(wav_path, format="wav")
    s.export(mp3_path, format="mp3")

# From https://stackoverflow.com/a/1131255/1703240
def generate_file_md5(filepath: str, blocksize: int=2**20):
    m = hashlib.md5()
    with open(filepath, "rb" ) as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            m.update(buf)
    return m.hexdigest()
