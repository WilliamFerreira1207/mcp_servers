import contextlib
from fastapi import FastAPI
from app.v1.math_server import mcp as math_mcp
from app.v1.secret_server import mcp as secret_mcp
from app.v1.legaldocs_server import mcp as legaldocs_mcp
from app.v1.audit_agent_server import mcp as audit_agent_mcp
import os
from datetime import datetime

PORT = int(os.environ.get("PORT", 8001))

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(math_mcp.session_manager.run())
        await stack.enter_async_context(secret_mcp.session_manager.run())
        await stack.enter_async_context(legaldocs_mcp.session_manager.run())
        await stack.enter_async_context(audit_agent_mcp.session_manager.run())
        yield

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def root():
    return {"message": "Welcome to the Multi-Model API Server!", "api_version": "1.1.0", "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

app.mount("/math", math_mcp.streamable_http_app())
app.mount("/secret", secret_mcp.streamable_http_app())
app.mount("/legaldocs", legaldocs_mcp.streamable_http_app())
app.mount("/audit_agent", audit_agent_mcp.streamable_http_app())