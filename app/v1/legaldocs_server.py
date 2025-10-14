from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from schemas.response_schemas import LD_GetTemplatesResponse, LD_UploadTemplateResponse, LD_GenerateDocResponse
from schemas.request_schemas import LD_GenerateDocRequest, files_info
from io import BytesIO

import base64
import os
import requests

load_dotenv()  # Carga las variables de entorno desde el archivo .env

mcp = FastMCP(name="legaldocs-mcp", host="0.0.0.0", stateless_http=True)
LEGAL_DOCS_URL = os.getenv("LEGAL_DOCS_URL")

@mcp.tool(
    name="get_legal_docs_templates", 
    description="Get available legal document templates name from the external service.",
    structured_output=True,
)
def get_available_temples() -> LD_GetTemplatesResponse:
    try:
        response = requests.get(f"{LEGAL_DOCS_URL}/get-templates")
        if response.status_code == 200:
            response = response.json().get("available templates", [])
            print(f"Response from legal docs service: {response}")
            return LD_GetTemplatesResponse(templates=response, result="Success")
    except Exception as e:
        return LD_GetTemplatesResponse(templates=[], result="Error retrieving legal documents")

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
        print(f"Base64 content size: {len(base64_content)} characters")
        print(f"First 100 chars': {base64_content[:100]}")
        b64 = base64_content.split(",")[-1] if "," in base64_content else base64_content
        file_bytes = base64.b64decode(b64)
        print(f"Decoded file size: {len(file_bytes)} bytes")
        files = {
            'file': (filename.strip().split(".")[0] if filename.strip().endswith(".pdf") else f"{filename.strip()}", BytesIO(file_bytes), 'application/pdf')
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

@mcp.tool(
    name="generate_legal_doc_from_template",
    structured_output=True
)
def generate_legal_doc_from_template(request: LD_GenerateDocRequest) -> LD_GenerateDocResponse:
    """
    Upload a legal document template to the external service.
    Args:
        request (LD_GenerateDocRequest): The request object containing:
            - info_files (List[files_info]): List of files information. This should include:
                - filename (str): The name of the file.
                - content (str): The base64 encoded content of the file.
            - output_filename (str): The desired output filename.
        

    Returns:
    """
    try:
        print(f"Generating document from template: {request.output_filename}")
        print("Uploading Info Files")
        files = []
        for f in request.info_files:
            print(f" - {f.filename}")
            b64 = f.content.split(",")[-1] if "," in f.content else f.content
            file_bytes = base64.b64decode(b64)
            file_name = f.filename if f.filename.strip().endswith(".pdf") else f"{f.filename.strip()}.pdf"
            files.append((
                "files",
                (file_name, BytesIO(file_bytes), "application/pdf")
            ))
        print(f"Prepared {len(files)} info files for upload.")
        response = requests.post(f"{LEGAL_DOCS_URL}/upload_unstructured_document", files=files)
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.json()}")
        if response.status_code == 200:
            return LD_GenerateDocResponse(
                result=response.json().get("message", "Document generated successfully"),
                filenames=response.json().get("document_names", []),
                status_code=response.status_code,
                success=True,
                
            )
        else:
            return LD_GenerateDocResponse(
                result=f"Failed to generate document: {response.text}",
                filenames=[],
                status_code=response.status_code,
                success=False
            )
    except Exception as e:
        return LD_GenerateDocResponse(
            result=f"Error generating document: {e}",
            filenames=[],
            status_code=500,
            success=False
        )

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
