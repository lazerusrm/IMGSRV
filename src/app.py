"""
FastAPI application with security middleware and API endpoints.

Provides secure web interface for image sequence viewing and management.
"""

import logging
from datetime import datetime, timedelta
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
from src.services.snow_analytics import SnowAnalytics
from src.services.config_manager import ConfigManager
from src.templates.config_page import create_config_page_html

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
            
            # Get current update interval from config
            from src.services.config_manager import ConfigManager
            config_mgr = ConfigManager(settings)
            config = config_mgr.get_config()
            update_interval = config.get("sequence_update_interval_minutes", 5)
            
            if not latest_sequence or not latest_sequence.exists():
                return HTMLResponse("""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Woodland Hills City Center - Snow Load Monitoring</title>
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
                <meta http-equiv="refresh" content="{update_interval * 60}">
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
                <p>GIF updates every {update_interval} {'minute' if update_interval == 1 else 'minutes'}</p>
                <div class="refresh-info">
                    Page refreshes automatically every {update_interval} {'minute' if update_interval == 1 else 'minutes'}
                </div>
                <div class="config-link">
                    <a href="/config" style="color: #3498db; text-decoration: none; font-size: 0.9em;">
                        ⚙️ Configure Analytics Settings
                    </a>
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
    
    @app.get("/iframe", response_class=HTMLResponse)
    @limiter.limit(f"{settings.rate_limit_per_minute}/minute")
    async def iframe_view(request: Request):
        """Iframe-optimized view without headers/footers."""
        try:
            service = app.state.sequence_service
            latest_sequence = await service.get_latest_sequence()
            
            # Get current update interval from config
            from src.services.config_manager import ConfigManager
            config_mgr = ConfigManager(settings)
            config = config_mgr.get_config()
            update_interval = config.get("sequence_update_interval_minutes", 5)
            
            if not latest_sequence or not latest_sequence.exists():
                return HTMLResponse("""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Snow Load Monitoring</title>
                    <meta http-equiv="refresh" content="30">
                    <style>
                        body { 
                            font-family: Arial, sans-serif; 
                            text-align: center; 
                            margin: 0; 
                            padding: 20px;
                            background-color: #f0f0f0;
                        }
                        .error { color: red; font-size: 18px; }
                        .container {
                            background-color: white;
                            padding: 20px;
                            border-radius: 8px;
                            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h2>Snow Load Monitoring</h2>
                        <div class="error">No image sequence available</div>
                        <p>Please wait for the camera to capture images...</p>
                    </div>
                </body>
                </html>
                """)
            
            return HTMLResponse(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Snow Load Monitoring</title>
                <meta http-equiv="refresh" content="{update_interval * 60}">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 10px;
                        background-color: #f0f0f0;
                    }}
                    .container {{
                        background-color: white;
                        border-radius: 8px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        overflow: hidden;
                    }}
                    .header {{
                        background-color: #2c3e50;
                        color: white;
                        padding: 15px;
                        text-align: center;
                    }}
                    .header h1 {{
                        margin: 0;
                        font-size: 1.8em;
                        font-weight: bold;
                    }}
                    .header h2 {{
                        margin: 5px 0 0 0;
                        font-size: 1.2em;
                        font-weight: normal;
                        opacity: 0.9;
                    }}
                    .content {{
                        padding: 15px;
                        text-align: center;
                    }}
                    .camera-image {{
                        max-width: 100%;
                        height: auto;
                        border: 2px solid #ddd;
                        border-radius: 4px;
                    }}
                    .info {{
                        margin-top: 15px;
                        color: #666;
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
                            <p>GIF updates every {update_interval} {'minute' if update_interval == 1 else 'minutes'}</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """)
            
        except Exception as e:
            logger.error("Error serving iframe view", error=str(e))
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "image-sequence-server"}
    
@app.get("/analytics")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def get_analytics(request: Request):
    """Get current road condition for drivers."""
    try:
        service = app.state.sequence_service
        if not service.analytics:
            return {"error": "Analytics not enabled"}
        
        # Get latest analysis
        if service.analytics.historical_data:
            latest = service.analytics.historical_data[-1]
            
            # Return driver-focused data only
            return {
                "timestamp": latest["timestamp"],
                "road_condition": latest["road_condition"],
                "temperature": latest["temperature"],
                "conditions": latest["conditions"],
                "accumulation_rate": latest.get("accumulation_rate"),
                "forecast_alerts": latest.get("forecast_alerts", []),
                "snow_chart": latest.get("snow_chart", {})
            }
        
        return {"error": "No analytics data available"}
        
    except Exception as e:
        logger.error("Analytics endpoint error", error=str(e))
        return {"error": "Failed to get analytics data"}

    @app.get("/analytics/history")
    @limiter.limit(f"{settings.rate_limit_per_minute}/minute")
    async def get_analytics_history(request: Request, hours: int = 24):
        """Get historical analytics data."""
        try:
            service = app.state.sequence_service
            if not service.analytics:
                return {"error": "Analytics not enabled"}
            
            # Get historical data from analytics service
            historical_data = service.analytics.historical_data
            
            # Filter by time range
            cutoff_time = datetime.now() - timedelta(hours=hours)
            filtered_data = [
                data for data in historical_data
                if datetime.fromisoformat(data["timestamp"]) >= cutoff_time
            ]
            
            return {
                "status": "success",
                "data_points": len(filtered_data),
                "time_range_hours": hours,
                "data": filtered_data
            }
            
        except Exception as e:
            logger.error("Analytics history endpoint error", error=str(e))
            return {"error": "Failed to get analytics history"}
    
    @app.get("/analytics/road-boundaries")
    @limiter.limit(f"{settings.rate_limit_per_minute}/minute")
    async def get_road_boundaries(request: Request, mode: str = "annotated"):
        """
        Debug endpoint to visualize detected road boundaries.
        Returns an annotated image showing the road detection area.
        
        Args:
            mode: "annotated" for visualization with overlay, "raw" for original image
        """
        try:
            service = app.state.sequence_service
            if not service.analytics:
                logger.error("Analytics not enabled for road boundaries endpoint")
                raise HTTPException(status_code=503, detail="Analytics not enabled")
            
            # Capture current frame from camera
            try:
                image_data, timestamp = await service.camera.capture_snapshot()
                logger.info("Captured image for road boundary visualization", size_bytes=len(image_data), timestamp=timestamp.isoformat())
            except Exception as e:
                logger.error("Failed to capture image for road boundary visualization", error=str(e))
                raise HTTPException(status_code=503, detail="Camera not available")
            
            # Convert to OpenCV format
            import cv2
            import numpy as np
            from io import BytesIO
            from PIL import Image
            
            pil_image = Image.open(BytesIO(image_data))
            cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            if mode == "raw":
                # Generate metadata even for raw mode
                _, metadata = service.analytics.road_detector.visualize_road_boundaries(cv_image)
                
                # Return original image without annotations for ROI editor
                img_byte_arr = BytesIO()
                pil_image.save(img_byte_arr, format='JPEG', quality=85)
                img_byte_arr.seek(0)
                
                return Response(
                    content=img_byte_arr.read(),
                    media_type="image/jpeg",
                    headers={
                        "X-Road-Pixels": str(metadata.get("road_pixels", 0)),
                        "X-Road-Percentage": str(metadata.get("road_percentage", 0)),
                        "X-Contours-Detected": str(metadata.get("contours_detected", 0)),
                        "X-Timestamp": timestamp.isoformat()
                    }
                )
            else:
                # Visualize road boundaries
                annotated_image, metadata = service.analytics.road_detector.visualize_road_boundaries(cv_image)
                
                # Convert back to bytes for response
                _, buffer = cv2.imencode('.png', annotated_image)
                image_bytes = buffer.tobytes()
                
                # Return image with metadata in headers
                http_response = Response(
                    content=image_bytes,
                    media_type="image/png",
                    headers={
                        "X-Road-Pixels": str(metadata.get("road_pixels", 0)),
                        "X-Road-Percentage": str(metadata.get("road_percentage", 0)),
                        "X-Contours-Detected": str(metadata.get("contours_detected", 0)),
                        "X-Timestamp": timestamp.isoformat()
                    }
                )
                
                logger.info("Road boundary visualization generated", metadata=metadata)
                return http_response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Road boundaries endpoint error", error=str(e))
            raise HTTPException(status_code=500, detail="Failed to generate road boundary visualization")
    
    # Configuration endpoints (CAMERA SERVER ONLY - NOT EXPOSED TO VPS)
    @app.get("/config", response_class=HTMLResponse)
    @limiter.limit(f"{settings.rate_limit_per_minute}/minute")
    async def config_page(request: Request):
        """
        Analytics configuration page - CAMERA SERVER ONLY.
        
        SECURITY NOTE: This endpoint is only accessible on the camera server
        (internal network) and is NOT exposed to the public VPS.
        """
        try:
            # Log configuration access for security monitoring
            client_ip = request.client.host if request.client else "unknown"
            logger.info("Configuration page accessed", client_ip=client_ip)
            
            # Initialize config manager
            config_manager = ConfigManager(settings)
            config_data = config_manager.get_config()
            
            # Generate HTML page
            html_content = create_config_page_html(config_data)
            return HTMLResponse(content=html_content)
            
        except Exception as e:
            logger.error("Configuration page error", error=str(e))
            return HTMLResponse(
                content="<h1>Configuration Error</h1><p>Failed to load configuration page.</p>",
                status_code=500
            )
    
    @app.post("/config/analytics")
    @limiter.limit(f"{settings.rate_limit_per_minute}/minute")
    async def update_analytics_config(request: Request):
        """
        Update analytics configuration - CAMERA SERVER ONLY.
        
        SECURITY NOTE: This endpoint is only accessible on the camera server
        (internal network) and is NOT exposed to the public VPS.
        """
        try:
            # Log configuration update for security monitoring
            client_ip = request.client.host if request.client else "unknown"
            logger.info("Configuration update attempted", client_ip=client_ip)
            
            # Get request data
            config_data = await request.json()
            
            # Initialize config manager
            config_manager = ConfigManager(settings)
            
            # Update configuration
            result = config_manager.update_config(config_data)
            
            if result.get("status") == "success":
                logger.info("Configuration updated successfully", client_ip=client_ip)
                
                # Reload service configuration to apply new settings immediately
                try:
                    await sequence_service.reload_config()
                    result["message"] = "Configuration updated and service reloaded successfully"
                    logger.info("Service configuration reloaded", client_ip=client_ip)
                except Exception as reload_error:
                    logger.error("Failed to reload service config", error=str(reload_error))
                    result["warning"] = "Configuration saved but service reload failed. Restart service manually."
            else:
                logger.warning("Configuration update failed", client_ip=client_ip, error=result.get("message"))
            
            return result
            
        except Exception as e:
            logger.error("Configuration update error", error=str(e))
            return {
                "status": "error",
                "message": f"Update failed: {str(e)}"
            }
    
    @app.post("/config/analytics/reset")
    @limiter.limit(f"{settings.rate_limit_per_minute}/minute")
    async def reset_analytics_config(request: Request):
        """Reset analytics configuration to defaults."""
        try:
            # Initialize config manager
            config_manager = ConfigManager(settings)
            
            # Reset configuration
            result = config_manager.reset_to_defaults()
            
            return result
            
        except Exception as e:
            logger.error("Configuration reset error", error=str(e))
            return {
                "status": "error",
                "message": f"Reset failed: {str(e)}"
            }
    
    @app.get("/config/analytics")
    @limiter.limit(f"{settings.rate_limit_per_minute}/minute")
    async def get_analytics_config(request: Request):
        """Get current analytics configuration."""
        try:
            # Initialize config manager
            config_manager = ConfigManager(settings)
            config_data = config_manager.get_config()
            
            return {
                "status": "success",
                "config": config_data
            }
            
        except Exception as e:
            logger.error("Configuration get error", error=str(e))
            return {
                "status": "error",
                "message": f"Failed to get configuration: {str(e)}"
            }
    
    return app
