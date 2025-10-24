from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from schemas.response_schemas import LD_GetTemplatesResponse, LD_UploadTemplateResponse, LD_UploadFileTemplateCompletitionResponse
from schemas.request_schemas import LD_UploadFileTemplateCompletition
from io import BytesIO

import base64
import os
import requests

load_dotenv()  # Carga las variables de entorno desde el archivo .env

mcp = FastMCP(name="legaldocs-mcp", host="0.0.0.0", stateless_http=True)
LEGAL_DOCS_URL = os.getenv("LEGAL_DOCS_URL")
CREATE_DOCUMENT_LAMBDA = os.getenv("CREATE_DOCUMENT_LAMBDA")

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
def upload_legal_doc_template(file_path: str, filename: str) -> LD_UploadTemplateResponse:
    """
    Upload a legal document template to the external service.
    Args:
        file_path (str): The path to the file to be uploaded.
        filename (str): The name of the file to be uploaded.

    Returns:
    """
    try:
        print(f"Uploading template: {filename}")
        print(f"File path: {file_path}")
        # print(f"Base64 content size: {len(base64_content)} characters")
        # print(f"First 100 chars': {base64_content[:100]}")
        # b64 = base64_content.split(",")[-1] if "," in base64_content else base64_content
        # file_bytes = base64.b64decode(b64)
        # print(f"Decoded file size: {len(file_bytes)} bytes")
        # Request para obtener el archivo y subirlo
        response = requests.get(file_path)
        if response.status_code != 200:
            return LD_UploadTemplateResponse(
                result=f"Failed to download file from {file_path}",
                filename=filename,
                status_code=response.status_code,
                success=False
            )
        file_bytes = response.content
        files = {
            'file': (filename.strip() if filename.strip().endswith(".pdf") else f"{filename.strip()}.pdf", BytesIO(file_bytes), 'application/pdf')
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
    name="upload_doc_for_template_completition",
    structured_output=True
)
def upload_doc_for_template_completition(filename: str, file_path: str) -> LD_UploadFileTemplateCompletitionResponse:
    """
    Upload a legal document template to the external service.
    Args:
        filename (str): The name of the file.
        file_path (str): The path to the file.


    Returns:
    """
    try:
        print(f"Generating document from template: {filename}")
        print(f"File path: {file_path}")
        response = requests.get(file_path)
        if response.status_code != 200:
            return LD_UploadFileTemplateCompletitionResponse(
                result=f"Failed to download file from {file_path}",
                filename=filename,
                status_code=response.status_code,
                success=False
            )
        file_bytes = response.content
        file_name = filename if filename.strip().endswith(".pdf") else f"{filename.strip()}.pdf"
        files = []
        files.append((
                "files",
                (file_name, BytesIO(file_bytes), "application/pdf")
            ))
        print(f"Prepared {len(files)} info files for upload.")
        response = requests.post(f"{LEGAL_DOCS_URL}/upload_unstructured_document", files=files)
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.json()}")
        if response.status_code == 200:
            return LD_UploadFileTemplateCompletitionResponse(
                result=response.json().get("message", "Document generated successfully"),
                filename=response.json().get("document_names", [])[0] if response.json().get("document_names") else "",
                status_code=response.status_code,
                success=True,
            )
        else:
            return LD_UploadFileTemplateCompletitionResponse(
                result=f"Failed to generate document: {response.text}",
                filename="",
                status_code=response.status_code,
                success=False
            )
    except Exception as e:
        return LD_UploadFileTemplateCompletitionResponse(
            result=f"Error generating document: {e}",
            filename="",
            status_code=500,
            success=False
        )

@mcp.tool(
    name="create_document_from_template",
    description="Create a legal document from a template and a list of info files.",
    structured_output=False,
)
def create_document_from_template(template_name: str, info_file_names: list[str], email: str) -> dict:
    try:
        payload = {
            "template_name": template_name,
            "document_names": ",".join(info_file_names),
            "email": email
        }
        print(f"Creating document with payload: {payload}")
        response = requests.post(CREATE_DOCUMENT_LAMBDA, json=payload)
        if response.status_code == 200 or response.status_code == 201 or response.status_code == 202:
            return response.json()
        else:
            return {"error": f"Failed to create document: {response.text}"}
       
    except Exception as e:
        return {"error": f"Error creating document from template: {e}"}

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
