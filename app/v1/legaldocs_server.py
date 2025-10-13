from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os
import requests
from schemas.response_schemas import LD_GetTemplatesResponse

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


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
