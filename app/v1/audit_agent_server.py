# main.py
from mcp.server.fastmcp import FastMCP
from config import config
from schemas.request_schemas import AA_CreateAuditProcessRequest, FileInfo
from typing import List
from requests_toolbelt.multipart.encoder import MultipartEncoder
from schemas.response_schemas import AA_SessionsResponseItem, AA_GetParentSessionFromUserResponse

import requests


import time
import math, sys
import os
import io
mcp = FastMCP(name="secrets-mcp", host="0.0.0.0", stateless_http=True)

def obtain_chimbitas_access_token() -> str:
    """
        Obtains an access token from the Chimbitas API using the provided credentials.
    """
    try:
        # Login into Chimbitas to get acccess token
        login_payload = {
            "username": config.USER_NAME_CHIMBITAS,
            "password": config.PASSWORD_CHIMBITAS,
            "grant_type": "password"
        }
        response = requests.post(f"{config.CHIMBITAS_LAMBDA_URL}/token", data=login_payload)
        response.raise_for_status()
        if response.status_code == 200:
            print("Successfully obtained Chimbitas session ID.")
            access_token = response.json().get("access_token", "")
            return access_token
        else:
            raise Exception(f"Failed to obtain Chimbitas access token, status code: {response.status_code}")
    except Exception as e:
        print(f"Error obtaining Chimbitas access token: {e}")
        return None

def get_chimbitas_session_id(session_name: str, access_token: str) -> str:
    """
        Obtains a session ID from the Chimbitas API using the provided credentials.
    """
    try:
        sessionid_payload = {
            "company_id": config.COMPANY_ID_CHIMBITAS,
            "user_id": config.USER_ID_CHIMBITAS,
            "name": session_name,
            "analysis_type": 1,
            "task": f"Audit Process Creation: {session_name}. Parent Session ID of process: {session_name}",
            "objective": "Audit Process",
            "process_description": f"Audit process created on behalf of user {config.USER_NAME_CHIMBITAS}. Parent Session ID of process: {session_name}",
            "is_info_source": 1
        }
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.post(f"{config.CHIMBITAS_LAMBDA_URL}/sessions/add", json=sessionid_payload, headers=headers)
        response.raise_for_status()
        if response.status_code == 200:
            
            return str(response.json().get("session", "").get("session_id", ""))
        else:
            raise Exception(f"Failed to create Chimbitas session, status code: {response.status_code}")
    except Exception as e:
        print(f"Error obtaining Chimbitas session ID: {e}")
        return ""

def generate_presigned_s3url_chimbitas(session_id: str, object_name: str, access_token: str, object_prefix: str) -> dict:
    """
        Generates a presigned S3 URL for file upload to Chimbitas.
    """
    try:
        payload = {
            "object_name": object_name,
            "analysis_type_id": 1,
            "company_id": config.COMPANY_ID_CHIMBITAS,
            "user_id": config.USER_ID_CHIMBITAS,
            "session_id": session_id,
            "s3_bucket_name": "aws-us-east-1-dev-s3-chimbitas-back-0004",
            "object_prefix": object_prefix
        }
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.post(f"{config.API_CHIMBITAS_URL}/files/upload", json=payload, headers=headers)
        response.raise_for_status()
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to generate presigned S3 URL, status code: {response.status_code}")
    except Exception as e:
        print(f"Error generating presigned S3 URL: {e}")
        return {}

def download_file(file_url: str) -> bytes:
    """
        Downloads a file from the given URL and returns its content as bytes.
    """
    try:
        response = requests.get(file_url)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"Error downloading file from {file_url}: {e}")
        return b""

def upload_files_to_s3(presigned_content: dict, content_type="multipart/form-data", file_content: bytes = None, filename: str = None) -> bool:
    """
        Uploads files to the given presigned S3 URL.
    """
    try:
        files = {}
        if file_content is not None:
            files = {'file': (filename, file_content, content_type)}
        form_data_subida_s3 = MultipartEncoder(
            fields={**presigned_content.get("fields", {}), **files}
        )
        print(f"Uploading file to S3 with presigned URL: {type(presigned_content.get('fields', ''))}")
        response = requests.post(presigned_content.get("url", ""), data=form_data_subida_s3, headers={'Content-Type': form_data_subida_s3.content_type})
        print(f"File uploaded to S3 with status code: {response.status_code}")
        response.raise_for_status()
        return response.status_code == 200 or response.status_code == 204
    except Exception as e:
        print(f"Error uploading files to S3: {e}")
        return False

def manage_upload_process(file_urls: List[FileInfo], session_id: str, access_token: str, list_type: str) -> bool:
    s3_keys = []
    object_prefix = ''
    if list_type == "audict_process_files":
        object_prefix = f"{config.COMPANY_ID_CHIMBITAS}/{config.USER_ID_CHIMBITAS}/{session_id}"
    elif list_type == "normatives":
        object_prefix = f"{config.COMPANY_ID_CHIMBITAS}/{config.USER_ID_CHIMBITAS}/{session_id}/norm"
    elif list_type == "audit_reports":
        object_prefix = f"{config.COMPANY_ID_CHIMBITAS}/{config.USER_ID_CHIMBITAS}/{session_id}/audits"
    else:
        object_prefix = None   
        
    for file_info in file_urls:
        file_content = download_file(file_info.file_url)
        if not file_content:
            print(f"Failed to download file from {file_info.file_url}")
            return False
        presigned_content = generate_presigned_s3url_chimbitas(session_id, file_info.filename, access_token, object_prefix)
        if not presigned_content:
            print(f"Failed to generate presigned URL for {file_info.filename}")
            return False
        success = upload_files_to_s3(presigned_content, file_content=file_content, filename=file_info.filename)
        if not success:
            print(f"Failed to upload file {file_info.filename} to S3")
            return False
        s3_keys.append({
            'name': file_info.filename,
            's3_key': presigned_content.get('fields', {}).get('key', ''),
            'description': file_info.description,
            'file_prefix': object_prefix,
            'type': "file"
        })
    print(f"All files uploaded successfully: {s3_keys}")
    return True, s3_keys

async def poll_status(session_id: str, token: str, analysis_type_id: int):
    start_time = time.time()
    requestsCount = 0
    pollingInterval = 3000 # Initial polling interval (3 seconds)
    maxPollingDuration = 10800000 # 3 hours
    while True:
        requestsCount += 1
        if requestsCount > 3 and requestsCount <= 10:
            pollingInterval = 10000 # After 3 requests, set interval to 10 seconds
        elif requestsCount > 10:
            pollingInterval = 30000 # After 6 requests, set interval to 30 seconds

        if requestsCount == 20:
            print("Proceso de obtener polling status detenido en el count: ", requestsCount)
            return "failed", {'session_id': session_id, 'status': 'failed'}
        if requestsCount % 2 == 0:
            print(f"Seguimos procesando la informacion: Polling count: {requestsCount}")
            # print("SEGUIMOS PROCESANDO EL ARCHIVOS")

        print(f"Polling interval: {pollingInterval / 1000} seconds")

        try:
            response = requests.get(f"{config.API_CHIMBITAS_URL}/task/status?session_id={int(session_id)}&analysis_type_id={int(analysis_type_id)}", headers={"Authorization ": f"Bearer {token}"})
            status = response.json().get("status")
            print(f"STATUS DEL POLL STATUS: {status}")
            print(f"RESPUESTAS DEL POLL STATUS: {response.json()}")

            if status == "completed" or status == "failed":
                return status,response
            if time.time() - start_time > maxPollingDuration:
                return None,"Polling timed out."
            time.sleep(pollingInterval/1000)
        except Exception as e:
            print(f"Error polling status: {e}")
            return None,"Error fetching task status. Please try again."

async def process_files(session_id: str, s3_keys: List[str], company_name: str, job_description: str, project_description: str):
    try:
        access_token = obtain_chimbitas_access_token()
        if not access_token:
            print("Failed to obtain Chimbitas access token.")
            return False
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        payload = {
            "company_id": int(config.COMPANY_ID_CHIMBITAS),
            "user_id": int(config.USER_ID_CHIMBITAS),
            "session_id": int(session_id),
            ## Llenar con nombres de archivos que van a subir  
            "s3_keys": s3_keys,
            "s3_bucket_name": "aws-us-east-1-dev-s3-chimbitas-back-0004",
            "context": "audit_demo", #IMPORTANTE
            "audit_demo": {
                "axon_company": company_name,
                "axon_job": job_description,
                "axon_project_description": project_description,
                "axon_image_format": "svg",
                "norms_folder": "norm",
                "audits_folder": "audits"
            }
        }
        print(f"Processing files with payload: {payload}")
        response = requests.post(f"{config.API_CHIMBITAS_URL}/files/search", json=payload, headers=headers)
        response.raise_for_status()
        if response.status_code != 200:
            print(f"Failed to process files, status code: {response.status_code}")
            return False
        time.sleep(3)  # Wait for processing to complete
        access_token = obtain_chimbitas_access_token()
        status, response = await poll_status(session_id, access_token, 1)
        print(f"Final polling status: {status}")
        print(f"Final polling response: {response}")
        
        if response == "Polling timed out." or response == "Error fetching task status. Please try again.":
            print("Polling process failed or timed out.")
            return False
        
        if status != "completed":
            print(f"File processing failed with status: {status}")
            return False
        print("File processing completed successfully. Begining with Ingest")
        
        ingest_request_payload = {
            "region": "us-east-1",
            "session_id": int(session_id),
            "company_id": int(config.COMPANY_ID_CHIMBITAS),
            "user_id": int(config.USER_ID_CHIMBITAS),
            "object_prefix": f"{config.COMPANY_ID_CHIMBITAS}/{config.USER_ID_CHIMBITAS}/{session_id}",
            "context": "audit_demo"
        }
        
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        data_ingest_response = requests.post(f"{config.API_CHIMBITAS_URL}/ingest_data", json=ingest_request_payload, headers=headers)
        print("Data Ingest Response Status Code:", data_ingest_response.status_code)
        data_ingest_response.raise_for_status()
        if data_ingest_response.status_code != 200:
            print(f"Failed to ingest data, status code: {data_ingest_response.status_code}")
            return False
        
        print("Data ingestion completed successfully. Initiating polling status for ingestion.")
        data_ingest_session_id = data_ingest_response.json().get("session_id", "")
        status, response = await poll_status(data_ingest_session_id, access_token, 1)
        
        print(f"Final ingestion polling status: {status}")
        print(f"Final ingestion polling response: {response}") 
        if response == "Polling timed out." or response == "Error fetching task status. Please try again.":
            print("Ingestion polling process failed or timed out.")
            return False
        if status != "completed":
            print(f"Data ingestion failed with status: {status}")
            return False
        print("Data ingestion completed successfully.")
        return True            
    except Exception as e:
        print(f"Error processing files: {e}")
    return True


@mcp.tool(
    name="create_audit_process"
)
async def create_audit_process(request: AA_CreateAuditProcessRequest) -> str:
    """
        Creates an Audict process by invoking the Chimbitas Lambda function. This process
        is responsible for managing and storing the information to be used in the audit process.
    """
    access_token = obtain_chimbitas_access_token()
    if not access_token:
        return "Failed to obtain Chimbitas access token."
    
    # Paso #1: Crear sesión en Chimbitas
    session_id = get_chimbitas_session_id(request.titulo_proceso, access_token)
    if not session_id:
        return "Failed to create Chimbitas session."
    
    # Paso #2: Subir archivos relacionados al proceso de auditoría
    upload_success_audict_pro, s3_keys_audict_pro = manage_upload_process(request.urls_planteamiento_proceso_auditoria, session_id, access_token, list_type="audict_process_files")
    if not upload_success_audict_pro:
        return "Failed to upload files to Chimbitas."
    
    # Paso #3: Subir archivos normativos
    upload_success_normatives, s3_keys_normatives = manage_upload_process(request.urls_normativas_proceso, session_id, access_token, list_type="normatives")
    if not upload_success_normatives:
        return "Failed to upload normative files to Chimbitas."
    
    # Paso #4: Subir informes de auditoría
    upload_success_audit_reports, s3_keys_audit_reports = manage_upload_process(request.urls_informes_auditoria, session_id, access_token, list_type="audit_reports")
    if not upload_success_audit_reports:
        return "Failed to upload audit report files to Chimbitas."
    
    # Paso #5:  Crea activity.txt
    activityFileContent = f"1. Nombre de la empresa: {request.nombre_compania}\nNombre del proceso: {request.titulo_proceso}\nDescripcion del proceso: {request.descripcion_proceso}"
    # Crear txt con el contenido
    bytes_content = activityFileContent.encode('utf-8')
    presigned_content_activity = generate_presigned_s3url_chimbitas(session_id, "activity.txt", access_token, f"{config.COMPANY_ID_CHIMBITAS}/{config.USER_ID_CHIMBITAS}/{session_id}")
    if not presigned_content_activity:
        return "Failed to generate presigned URL for activity.txt"
    success_activity = upload_files_to_s3(presigned_content_activity, content_type="text/plain", file_content=bytes_content)
    if not success_activity:
        return "Failed to upload activity.txt to S3"

    s3_keys = s3_keys_audict_pro + s3_keys_normatives + s3_keys_audit_reports + [{'name':"activity.txt", 's3_key': presigned_content_activity.get('fields', {}).get('key', ''), 'description': 'Activity File', 'file_prefix': f"{config.COMPANY_ID_CHIMBITAS}/{config.USER_ID_CHIMBITAS}/{session_id}", 'type': 'file'}]
    print(f"All files including activity.txt uploaded successfully: {s3_keys}")    
    processing_success = await process_files(session_id, s3_keys, request.nombre_compania, request.cargo_usuario, request.descripcion_proceso)
    if not processing_success:
        return "Failed to process files in Chimbitas."
    return "Audit process created and files processed successfully."

@mcp.tool(name="get_parents_sessions_from_user", description="Get parent sessions from user id.")
def get_parents_sessions_from_user(user_id: int) -> AA_GetParentSessionFromUserResponse:
    """
        Retrieves parent sessions for a given user ID from the Chimbitas API.
    """
    try:
        access_token = obtain_chimbitas_access_token()
        if not access_token:
            return {"error": "Failed to obtain Chimbitas access token."}
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.get(f"{config.CHIMBITAS_LAMBDA_URL}/sessions/list?user_id={user_id}&company_id={config.COMPANY_ID_CHIMBITAS}&is_info_source=1", headers=headers)
        response.raise_for_status()
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Failed to retrieve parent sessions, status code: {response.status_code}"}
    except Exception as e:
        return {"error": f"Error retrieving parent sessions: {e}"}
    
@mcp.tool(name="get_child_sessions_from_user", description="Get child sessions from user id and parent session id.")
def get_child_sessions_from_user(user_id: int, parent_session_id: int) -> AA_GetParentSessionFromUserResponse:
    """
        Retrieves child sessions for a given user ID and parent session ID from the Chimbitas API.
    """
    try:
        access_token = obtain_chimbitas_access_token()
        if not access_token:
            return {"error": "Failed to obtain Chimbitas access token."}
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.get(f"{config.CHIMBITAS_LAMBDA_URL}/sessions/list?user_id={user_id}&company_id={config.COMPANY_ID_CHIMBITAS}&parent_session_id={parent_session_id}&is_info_source=0", headers=headers)
        response.raise_for_status()
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Failed to retrieve child sessions, status code: {response.status_code}"}
    except Exception as e:
        return {"error": f"Error retrieving child sessions: {e}"}
    
@mcp.tool(name="create_audit_chat_session", description="Create audit chat session in Chimbitas.")
def create_audit_chat_session(session_name: str, parent_session_id: int) -> dict:
    """
        Creates an audit chat session in Chimbitas.
    """
    try:
        access_token = obtain_chimbitas_access_token()
        if not access_token:
            return {"error": "Failed to obtain Chimbitas access token."}
        sessionid_payload = {
            "company_id": config.COMPANY_ID_CHIMBITAS,
            "user_id": config.USER_ID_CHIMBITAS,
            "name": session_name,
            "parent_session_id": parent_session_id,
            "analysis_type": 1,
            "task": f"Audit Chat Session: {session_name}. Parent Session ID: {parent_session_id}",
            "objective": "Audit Chat Session",
            "process_description": f"Audit chat session created on behalf of user {config.USER_NAME_CHIMBITAS}. Parent Session ID: {parent_session_id}",
            "process_name": session_name,
            "is_info_source": 0
        }
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.post(f"{config.CHIMBITAS_LAMBDA_URL}/sessions/add", json=sessionid_payload, headers=headers)
        response.raise_for_status()
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Failed to create audit chat session, status code: {response.status_code}"}
    except Exception as e:
        return {"error": f"Error creating audit chat session: {e}"}