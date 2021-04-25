import hashlib, io, os, shutil, sqlite3, uuid, datetime

from pydub import AudioSegment
from typing import List
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse

from typing import List, Optional
from pydantic import BaseModel

from helpers import *
from ResponseModels import *

con = sqlite3.connect('data/qbestd.sqlite')

app = FastAPI(
    title="QbE-STD API",
    description="Application Programming Interface for Query-by-Example Spoken Term Detection",
    version="0.0.1",
    openapi_tags=[
        {
            "name": "audio",
            "description": "Audio-related endpoints."
        }
    ],
    docs_url=None,
    redoc_url="/docs"
)

@app.post("/audio/upload/", tags = ["audio"], summary="Upload .wav files", response_model=UploadFileStatus)
async def upload_wav_files(files: List[UploadFile] = File(...)):
    """
    Upload and process a set .wav files selected by the user. If the file according to its
    md5 hash already exists on the configured S3 bucket, it will be skipped. Similary, for
    any other validations errors (e.g. not a wav file), the file will be added to the skip
    list with an appropriate message.
    
    Otherwise, the processing component will convert the
    .wav files to 16 kHz mono and upload .wav and .mp3 versions of the audio to the configured
    S3 bucket, and issue UUIDs for each file.
    """

    cur = con.cursor()

    cur.execute("SELECT file_hash, file_id FROM files")
    already_on_server = dict(cur.fetchall())

    upload_status = UploadFileStatus()

    for f in files:

        upload_location = f"tmp/{f.filename}"

        with open(upload_location, "wb+") as file_object:
            
            # Copy uploaded wav file to tmp folder
            shutil.copyfileobj(f.file, file_object)

            wav_hash = generate_file_md5(upload_location)

            if(wav_hash not in already_on_server.keys()):

                new_file_id = str(uuid.uuid1())

                wav_location = "tmp/" + new_file_id + ".wav"
                mp3_location = "tmp/" + new_file_id + ".mp3"

                wav_to_s3files(upload_location, wav_location, mp3_location)
                
                # Upload mp3 file to s3 bucket (not implemented here)
                # Simulate s3 upload
                shutil.copy(wav_location, "data/audio/wav/")
                shutil.copy(mp3_location, "data/audio/mp3/")

                # Delete files after s3 upload
                os.remove(upload_location)
                os.remove(wav_location)
                os.remove(mp3_location)

                cur = con.cursor()

                with con:
                    cur.execute(
                        "INSERT INTO files (file_id, file_hash, upload_date, upload_filename) VALUES (?, ?, ?, ?)",
                        (new_file_id, wav_hash, datetime.datetime.utcnow().isoformat(), f.filename)
                    )

                upload_status.processed.append(
                    FileStatus(
                        file_id = new_file_id,
                        upload_filename = f.filename
                    )
                )

            else:

                upload_status.skipped.append(FileStatus(
                        file_id = already_on_server[wav_hash],
                        upload_filename = f.filename,
                        message = "File already on server"
                    ))

    return upload_status

@app.get("/audio/mp3/{id}/", tags = ["audio"], summary="Fetch mp3 audio by identifier")
def get_mp3_audio(id: str, start_sec: Optional[float] = None, end_sec: Optional[float] = None):
    """
    Get mp3 audio by identifier, optionally specifying start and end time (in seconds). The identifier
    can be a file_id or a query_id (labelled portion of a query audio file). The unique (UUID) will
    automatically resolve to the correct resource. As the audio must resolve to a single source,
    collection_id cannot be used to fetch audio from all items within a collection.
    """

    song = AudioSegment.from_mp3(f"data/audio/mp3/{id}.mp3")

    start_ms = start_sec * 1000 if start_sec is not None else 0
    end_ms   = end_sec * 1000 if end_sec is not None else song.duration_seconds * 1000
    song = song[start_ms:end_ms]
    
    buf = io.BytesIO()
    song.export(buf, format="mp3")

    return StreamingResponse(buf, media_type="audio/mp3")
