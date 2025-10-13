import contextlib
from fastapi import FastAPI
from app.v1.math_server import mcp as math_mcp
from app.v1.secret_server import mcp as secret_mcp
from app.v1.legaldocs_server import mcp as legaldocs_mcp
import os
PORT = os.environ.get("PORT", 8000)
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(math_mcp.session_manager.run())
        await stack.enter_async_context(secret_mcp.session_manager.run())
        await stack.enter_async_context(legaldocs_mcp.session_manager.run())
        yield
        
app = FastAPI(lifespan=lifespan)
app.mount("/math", math_mcp.streamable_http_app())
app.mount("/secret", secret_mcp.streamable_http_app())
app.mount("/legaldocs", legaldocs_mcp.streamable_http_app())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)