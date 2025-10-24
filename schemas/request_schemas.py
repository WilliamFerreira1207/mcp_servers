from pydantic import BaseModel
from typing import List, Optional

class LD_UploadFileTemplateCompletition(BaseModel):
    filename: str
    file_path: str

# class LD_GenerateDocRequest(BaseModel):
#     info_files: List[files_info]
#     output_filename: str