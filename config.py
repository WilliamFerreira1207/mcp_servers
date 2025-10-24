from dotenv import load_dotenv
import os
load_dotenv()  # Carga las variables de entorno desde el archivo .env

class Config:
    LEGAL_DOCS_URL = os.getenv("LEGAL_DOCS_URL")
    CHIMBITAS_LAMBDA_URL = os.getenv("CHIMBITAS_LAMBDA_URL")
    USER_NAME_CHIMBITAS = os.getenv("USER_NAME_CHIMBITAS")
    USER_ID_CHIMBITAS = os.getenv("USER_ID_CHIMBITAS")
    COMPANY_ID_CHIMBITAS = os.getenv("COMPANY_ID_CHIMBITAS")
    PASSWORD_CHIMBITAS = os.getenv("PASSWORD_CHIMBITAS")
    API_CHIMBITAS_URL = os.getenv("API_CHIMBITAS_URL")
    
config = Config()