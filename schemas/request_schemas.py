from pydantic import BaseModel
from typing import List, Optional

class LD_UploadFileTemplateCompletition(BaseModel):
    filename: str
    file_path: str

# class LD_GenerateDocRequest(BaseModel):
#     info_files: List[files_info]
#     output_filename: str

class FileInfo(BaseModel):
    filename: str
    file_url: str
    description: Optional[str] = ''

class AA_CreateAuditProcessRequest(BaseModel):
    nombre_compania: str
    cargo_usuario: str
    titulo_proceso: str
    descripcion_proceso: str
    urls_planteamiento_proceso_auditoria: List[FileInfo]
    urls_normativas_proceso: List[FileInfo]
    urls_informes_auditoria: List[FileInfo]
    
    