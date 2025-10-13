# main.py
from mcp.server.fastmcp import FastMCP
import math, sys
import os
mcp = FastMCP(name="secrets-mcp", host="0.0.0.0", stateless_http=True)

def my_secrets_function(secret_number: int) -> str:
    # Just a dummy implementation for demonstration purposes
    secrets = {
        1: "The sky is blue.",
        2: "The grass is green.",
        3: "The sun is yellow.",
        4: "The ocean is deep.",
        5: "The stars are bright.",
        6: "The mountains are tall.",
        7: "The desert is hot.",
        8: "The forest is dense.",
        9: "The river is wide.",
        10: "The snow is cold."
    }
    return secrets.get(secret_number, "Unknown secret")

@mcp.tool()  # ← sin kwargs; el schema sale de las anotaciones
def get_secret(secret_number: int) -> str:
    """
        Return a secret based on the provided secret number. Example: get_secret(1) -> "The sky is blue."
    """
    return my_secrets_function(secret_number)  # → output_schema = {"result": {"type": "string"}}

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
