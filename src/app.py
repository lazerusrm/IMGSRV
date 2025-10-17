"""
FastAPI application with security middleware and API endpoints.

Provides secure web interface for image sequence viewing and management.
"""

import logging
from pathlib import Path
from typing import Optional

import structlog
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import HTTPBearer
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.config import Settings
from src.services.sequence_service import ImageSequenceService

logger = structlog.get_logger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


def create_app(settings: Settings) -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="Image Sequence Server",
        description="Secure IP camera image sequence generator",
        version="1.0.0",
        docs_url="/docs" if settings.log_level == "DEBUG" else None,  # Disable docs in production
        redoc_url="/redoc" if settings.log_level == "DEBUG" else None,
    )
    
    # Security middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    
    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # Initialize service
    sequence_service = ImageSequenceService(settings)
    
    @app.on_event("startup")
    async def startup_event():
        """Startup event handler."""
        try:
            await sequence_service.start()
            app.state.sequence_service = sequence_service
            logger.info("Application started successfully")
        except Exception as e:
            logger.error("Failed to start application", error=str(e))
            raise
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Shutdown event handler."""
        try:
            if hasattr(app.state, 'sequence_service'):
                await app.state.sequence_service.stop()
            logger.info("Application shutdown completed")
        except Exception as e:
            logger.error("Error during shutdown", error=str(e))
    
    @app.get("/", response_class=HTMLResponse)
    @limiter.limit(f"{settings.rate_limit_per_minute}/minute")
    async def root(request: Request):
        """Main page with traffic camera-style interface."""
        try:
            service = app.state.sequence_service
            latest_sequence = await service.get_latest_sequence()
            
            if not latest_sequence or not latest_sequence.exists():
                return HTMLResponse("""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Traffic Camera</title>
                    <meta http-equiv="refresh" content="30">
                    <style>
                        body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
                        .error { color: red; font-size: 18px; }
                    </style>
                </head>
                <body>
                    <h1>Woodland Hills City Center</h1>
                    <h2>Snow Load Monitoring</h2>
                    <div class="error">No image sequence available</div>
                    <p>Please wait for the camera to capture images...</p>
                </body>
                </html>
                """)
            
            return HTMLResponse(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Woodland Hills City Center - Snow Load Monitoring</title>
                <meta http-equiv="refresh" content="300">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 20px;
                        background-color: #f0f0f0;
                    }}
                    .container {{
                        max-width: 1200px;
                        margin: 0 auto;
                        background-color: white;
                        border-radius: 8px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        overflow: hidden;
                    }}
                    .header {{
                        background-color: #2c3e50;
                        color: white;
                        padding: 20px;
                        text-align: center;
                    }}
                    .header h1 {{
                        margin: 0;
                        font-size: 2.5em;
                        font-weight: bold;
                    }}
                    .header h2 {{
                        margin: 10px 0 0 0;
                        font-size: 1.5em;
                        font-weight: normal;
                        opacity: 0.9;
                    }}
                    .content {{
                        padding: 20px;
                        text-align: center;
                    }}
                    .camera-image {{
                        max-width: 100%;
                        height: auto;
                        border: 2px solid #ddd;
                        border-radius: 4px;
                    }}
                    .info {{
                        margin-top: 20px;
                        color: #666;
                        font-size: 14px;
                    }}
                    .refresh-info {{
                        margin-top: 10px;
                        color: #999;
                        font-size: 12px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Woodland Hills City Center</h1>
                        <h2>Snow Load Monitoring</h2>
                    </div>
                    <div class="content">
                        <img src="/sequence/latest" alt="Snow Load Monitoring GIF" class="camera-image">
                        <div class="info">
                            <p>GIF updates every 5 minutes</p>
                            <div class="refresh-info">
                                Page refreshes automatically every 5 minutes
                            </div>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """)
            
        except Exception as e:
            logger.error("Error serving main page", error=str(e))
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.get("/sequence/latest")
    @limiter.limit(f"{settings.rate_limit_per_minute}/minute")
    async def get_latest_sequence(request: Request):
        """Get the latest image sequence."""
        try:
            service = app.state.sequence_service
            latest_sequence = await service.get_latest_sequence()
            
            if not latest_sequence or not latest_sequence.exists():
                raise HTTPException(status_code=404, detail="No sequence available")
            
            return FileResponse(
                latest_sequence,
                media_type="image/gif",
                filename="latest_sequence.gif"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error serving latest sequence", error=str(e))
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.get("/status")
    @limiter.limit("10/minute")
    async def get_status(request: Request):
        """Get service status (for monitoring)."""
        try:
            service = app.state.sequence_service
            status = await service.get_status()
            return status
            
        except Exception as e:
            logger.error("Error getting status", error=str(e))
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "image-sequence-server"}
    
    return app
