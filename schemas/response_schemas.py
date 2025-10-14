from pydantic import BaseModel
from typing import List, Optional

class LD_GetTemplatesResponse(BaseModel):
    templates: List[str]
    
class LD_UploadTemplateResponse(BaseModel):
    filename: str
    status_code: int
    success: bool
    result: str

class LD_GenerateDocResponse(BaseModel):
    filenames: List[str]
    status_code: int
    success: bool
    result: str