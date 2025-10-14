from pydantic import BaseModel
from typing import List, Optional

class files_info(BaseModel):
    filename: str
    content: str

class LD_GenerateDocRequest(BaseModel):
    info_files: List[files_info]
    output_filename: str