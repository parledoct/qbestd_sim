import hashlib, os, shutil

from pydub import AudioSegment
from typing import List
from fastapi import FastAPI, File, UploadFile

app = FastAPI()

def wav_to_mp3(wav_path: str, mp3_path: str):
    AudioSegment.from_wav(wav_path).set_channels(1).set_frame_rate(8000).export(mp3_path, format="mp3", bitrate="192k")

# From https://stackoverflow.com/a/1131255/1703240
def generate_file_md5(filepath, blocksize=2**20):
    m = hashlib.md5()
    with open(filepath, "rb" ) as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            m.update(buf)
    return m.hexdigest()

@app.post("/uploadfiles/")
async def create_upload_files(files: List[UploadFile] = File(...)):

    # Get hashes of already uploaded files on s3 bucket (not implemented here)
    already_on_server = []

    skipped_files     = []
    processed_files   = []

    for f in files:

        wav_location = f"tmp/{f.filename}"

        with open(wav_location, "wb+") as file_object:
            
            # Copy uploaded wav file to tmp folder
            shutil.copyfileobj(f.file, file_object)

            wav_hash = generate_file_md5(wav_location)

            if(wav_hash not in already_on_server):

                # Use the hash of the original wav file as name for converted mp3 file for future checks
                mp3_location = "tmp/" + wav_hash + ".mp3"

                wav_to_mp3(wav_location, mp3_location)
                
                # Upload mp3 file to s3 bucket (not implemented here)
                # upload_to_s3(wav_location)

                # Delete files after s3 upload (not implemented here)
                # os.remove(wav_location)
                # os.remove(mp3_location)

                processed_files.append(f.filename)

            else:

                skipped_files.append(f.filename)

    return {"files" : { "processed": processed_files, "skipped": skipped_files }}
