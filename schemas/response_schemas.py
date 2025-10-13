from pydantic import BaseModel
from typing import List, Optional

class LD_GetTemplatesResponse(BaseModel):
    templates: List[str]