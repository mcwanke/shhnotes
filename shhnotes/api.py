"""FastAPI endpoints for ShhNotes service."""

import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .config import Config
from .service import Service

logger = logging.getLogger(__name__)

app = FastAPI(title="ShhNotes")

# Singleton service instance
_service: Service | None = None


def get_service() -> Service:
    """Get or create the service singleton."""
    global _service
    if _service is None:
        _service = Service()
    return _service


class StartRequest(BaseModel):
    """Request body for /start endpoint."""

    label: str = "default"


class StartResponse(BaseModel):
    """Response from /start endpoint."""

    session_id: str


class StatusResponse(BaseModel):
    """Response from /status endpoint."""

    state: str


class StopResponse(BaseModel):
    """Response from /stop endpoint."""

    success: bool


@app.post("/start", response_model=StartResponse)
async def start_session(request: StartRequest) -> StartResponse:
    """Start a new transcription session.

    Args:
        request: JSON body with optional label (default: "default").

    Returns:
        Session ID on success.

    Raises:
        HTTPException: If session fails to start.
    """
    service = get_service()
    session_id = service.start_session(request.label)
    if not session_id:
        logger.error("Failed to start session")
        raise HTTPException(status_code=500, detail="Failed to start session")
    return StartResponse(session_id=session_id)


@app.post("/stop", response_model=StopResponse)
async def stop_session() -> StopResponse:
    """Stop the current session and trigger transcription.

    Returns:
        Success status.

    Raises:
        HTTPException: If no active session.
    """
    service = get_service()
    success = service.stop_session()
    if not success:
        logger.error("No active session to stop")
        raise HTTPException(status_code=400, detail="No active session")
    return StopResponse(success=True)


@app.get("/status", response_model=StatusResponse)
async def get_status() -> StatusResponse:
    """Get current session state.

    Returns:
        Current state: idle | recording | transcribing.
    """
    service = get_service()
    return StatusResponse(state=service.get_status())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=Config.API_HOST, port=Config.API_PORT)
