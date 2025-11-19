"""
AxProtocol Sentinel API - FastAPI REST API for AxProtocol

Provides HTTP endpoints for running AxProtocol chains and accessing results.

Usage:
    uvicorn sentinel_api:app --host 0.0.0.0 --port 8000

Endpoints:
    POST /run - Execute AxProtocol chain
    GET /health - Health check
    GET /version - API version
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
from pathlib import Path
import traceback

try:
    from axprotocol import run_chain
    from axprotocol import __version__ as axprotocol_version
except ImportError:
    # Fallback for development (when axprotocol not installed)
    try:
        from axp.orchestration import run_chain
        axprotocol_version = "2.4.0-dev"
    except ImportError:
        raise ImportError(
            "AxProtocol not found. Install with: pip install axprotocol"
        )

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sentinel_api")

# Initialize FastAPI app
app = FastAPI(
    title="AxProtocol Sentinel API",
    description="REST API for AxProtocol multi-role reasoning chain",
    version=axprotocol_version,
    docs_url="/docs",
    redoc_url="/redoc",
)


# Request/Response Models
class RunRequest(BaseModel):
    """Request model for /run endpoint."""
    objective: str = Field(..., description="Objective specification for the chain")
    # PHASE 1: Domain parameter removed - Creative domain only
    # domain: Optional[str] = Field(
    #     None,
    #     description="Domain override (marketing, technical, ops, creative, education, product, strategy, research)"
    # )
    session_id: Optional[str] = Field(
        None,
        description="Optional session ID (auto-generated if not provided)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "objective": "Book 5 local jobs in 7 days for a tree service in Omaha",
                "domain": "marketing",
                "session_id": "optional-session-id"
            }
        }


class RunResponse(BaseModel):
    """Response model for /run endpoint."""
    success: bool
    session_id: str
    results: Dict[str, Any]
    strategist: str
    analyst: str
    producer: str
    courier: str
    critic: str
    message: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    service: str


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    traceback: Optional[str] = None


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "traceback": traceback.format_exc() if logger.level == logging.DEBUG else None
        }
    )


# Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns:
        Health status and version information
    """
    return HealthResponse(
        status="healthy",
        version=axprotocol_version,
        service="AxProtocol Sentinel API"
    )


@app.get("/version")
async def get_version():
    """
    Get API version.

    Returns:
        Version string
    """
    return {"version": axprotocol_version}


@app.post("/run", response_model=RunResponse)
async def run_chain_endpoint(request: RunRequest):
    """
    Execute AxProtocol multi-role reasoning chain.

    Args:
        request: RunRequest with objective, optional domain, and optional session_id

    Returns:
        RunResponse with chain results

    Raises:
        HTTPException: If chain execution fails
    """
    try:
        # PHASE 1: Domain parameter removed - Creative domain only
        logger.info(f"Received run request: objective={request.objective[:100]}...")

        # Determine base_dir (current working directory or package root)
        base_dir = Path.cwd()

        # Execute chain
        # PHASE 1: Always uses creative domain (domain parameter removed)
        strategist, analyst, producer, courier, critic, results = run_chain(
            objective=request.objective,
            session_id=request.session_id,
            base_dir=base_dir,
        )

        # Extract session_id from results if not provided
        session_id = request.session_id or results.get("session_id", "unknown")

        logger.info(f"Chain execution successful: session_id={session_id}")

        return RunResponse(
            success=True,
            session_id=session_id,
            results=results,
            strategist=strategist,
            analyst=analyst,
            producer=producer,
            courier=courier,
            critic=critic,
            message="Chain execution completed successfully"
        )

    except ValueError as e:
        # Validation errors (400)
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # Internal errors (500)
        error_trace = traceback.format_exc()
        logger.error(f"Chain execution failed: {e}\n{error_trace}")
        raise HTTPException(
            status_code=500,
            detail=f"Chain execution failed: {str(e)}"
        )


@app.get("/domains")
async def list_domains():
    """
    List available domains.

    Returns:
        List of available domain names
    """
    domains = [
        "marketing",
        "technical",
        "ops",
        "creative",
        "education",
        "product",
        "strategy",
        "research",
    ]
    return {"domains": domains, "count": len(domains)}


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "AxProtocol Sentinel API",
        "version": axprotocol_version,
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "POST /run": "Execute AxProtocol chain",
            "GET /health": "Health check",
            "GET /version": "API version",
            "GET /domains": "List available domains",
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "sentinel_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload in development
        log_level="info"
    )

