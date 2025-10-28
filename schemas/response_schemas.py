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

class AA_SessionsResponseItem(BaseModel):
    session_id: int
    company_id: int
    user_id: int
    session_name: str
    task: str
    objective: str
    analysis_type_id: int
    created_at: str
    kb_id: str
    process_name: str
    process_description: str
    parent_session_id: Optional[int]
    is_info_source: int

class AA_GetParentSessionFromUserResponse(BaseModel):
    message: str
    sessions: List[AA_SessionsResponseItem]