from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from schemas.response_schemas import LD_GetTemplatesResponse, LD_UploadTemplateResponse
import base64
from io import BytesIO
import os
import requests

load_dotenv()  # Carga las variables de entorno desde el archivo .env

mcp = FastMCP(name="legaldocs-mcp", host="0.0.0.0", stateless_http=True)
LEGAL_DOCS_URL = os.getenv("LEGAL_DOCS_URL")

@mcp.tool(
    name="get_legal_docs_templates", 
    description="Get available legal document templates name from the external service."
)
def get_available_temples() -> str:
    try:
        response = requests.get(f"{LEGAL_DOCS_URL}/get-templates")
        if response.status_code == 200:
            response = response.json().get("available templates", [])
            print(f"Response from legal docs service: {response}")
            return LD_GetTemplatesResponse(templates=response).model_dump_json()
    except Exception as e:
        return "Error retrieving legal documents"

@mcp.tool(
    name="upload_legal_doc_template",
    structured_output=True
)
def upload_legal_doc_template(base64_content: str, filename: str) -> LD_UploadTemplateResponse:
    """
    Upload a legal document template to the external service.
    Args:
        base64_content (str): The base64 encoded content of the template.
        filename (str): The name of the file to be uploaded.

    Returns:
    """
    try:
        print(f"Uploading template: {filename}")
        file_bytes = base64.b64decode(base64_content)
        print(f"Decoded file size: {len(file_bytes)} bytes")
        files = {
            'file': (filename if filename.endswith(".pdf") else f"{filename}.pdf", BytesIO(file_bytes), 'application/pdf')
        }
        print(f"Prepared files for upload: {files['file'][0]}, size: {len(file_bytes)} bytes")
        
        data = {
            'name': filename
        }
        print(f"Uploading template: {filename}")
        response = requests.post(f"{LEGAL_DOCS_URL}/upload-template", files=files, data=data)
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.json()}")
        if response.status_code == 200:
            return LD_UploadTemplateResponse(
                result=response.json().get("message", "Template uploaded successfully"),
                filename=filename,
                status_code=response.status_code,
                success=True,
                
            )
        else:
            return LD_UploadTemplateResponse(
                result=f"Failed to upload template: {response.text}",
                filename=filename,
                status_code=response.status_code,
                success=False
            )
    except Exception as e:
        return LD_UploadTemplateResponse(
            result="Error uploading template",
            filename=filename,
            status_code=500,
            success=False
        )

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
