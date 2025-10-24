# main.py
from mcp.server.fastmcp import FastMCP
from config import config
import requests
import math, sys
import os
mcp = FastMCP(name="secrets-mcp", host="0.0.0.0", stateless_http=True)

def get_chimbitas_session_id() -> str:
    """
        Obtains a session ID from the Chimbitas API using the provided credentials.
    """
    try:
        # Login into Chimbitas to get acccess token
        login_payload = {
            "username": config.USER_NAME_CHIMBITAS,
            "password": config.PASSWORD_CHIMBITAS,
            "grant_type": "password"
        }
        response = requests.post(f"{config.API_CHIMBITAS_URL}token", data=login_payload)
        response.raise_for_status()
        if response.status_code == 200:
            return str(response.json())
    except Exception as e:
        print(f"Error obtaining Chimbitas session ID: {e}")
        return ""

@mcp.tool(name="create_audit_process")
def create_audit_process() -> str:
    """
        Creates an Audict process by invoking the Chimbitas Lambda function. This process
        is responsible for managing and storing the information to be used in the audit process.
    """
    return get_chimbitas_session_id()  # → output_schema = {"result": {"type": "string"}}
    # Dummy implementation for demonstration purposes