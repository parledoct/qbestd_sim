from typing import List, Optional
from pydantic import BaseModel

class FileStatus(BaseModel):
    file_id: str
    upload_filename: str
    message: Optional[str] = None

class UploadFileStatus(BaseModel):
    processed: List[FileStatus] = []
    skipped: List[FileStatus] = []
