from pydantic import BaseModel
from typing import List, Optional

class LD_GetTemplatesResponse(BaseModel):
    templates: List[str]
    result: str = "Success"
    
class LD_UploadTemplateResponse(BaseModel):
    filename: str
    status_code: int
    success: bool
    result: str

class LD_UploadFileTemplateCompletitionResponse(BaseModel):
    filename: str
    status_code: int
    success: bool
    result: str
