"""
ONVIF camera integration for Image Sequence Server.

Handles camera authentication, snapshot capture, and error handling.
"""

import asyncio
import logging
from datetime import datetime
from io import BytesIO
from typing import Optional, Tuple

import aiohttp
import structlog
from PIL import Image

logger = structlog.get_logger(__name__)


class CameraError(Exception):
    """Camera-related errors."""
    pass


class ONVIFCamera:
    """ONVIF camera client with snapshot capabilities."""
    
    def __init__(
        self,
        ip: str,
        username: str,
        password: str,
        port: int = 80,
        snapshot_path: str = "/snapshot.cgi"
    ):
        self.ip = ip
        self.username = username
        self.password = password
        self.port = port
        self.snapshot_path = snapshot_path
        self.base_url = f"http://{ip}:{port}"
        self.snapshot_url = f"{self.base_url}{snapshot_path}"
        
        # Create auth object
        self.auth = aiohttp.BasicAuth(username, password)
        
        logger.info("Camera initialized", ip=ip, port=port, path=snapshot_path)
    
    async def capture_snapshot(self) -> Tuple[bytes, datetime]:
        """
        Capture a snapshot from the camera.
        
        Returns:
            Tuple of (image_bytes, capture_timestamp)
            
        Raises:
            CameraError: If snapshot capture fails
        """
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    self.snapshot_url,
                    auth=self.auth,
                    headers={"User-Agent": "ImageSequenceServer/1.0"}
                ) as response:
                    
                    if response.status != 200:
                        raise CameraError(f"Camera returned status {response.status}")
                    
                    image_data = await response.read()
                    
                    if not image_data:
                        raise CameraError("Empty image data received")
                    
                    # Validate image
                    try:
                        with Image.open(BytesIO(image_data)) as img:
                            img.verify()
                    except Exception as e:
                        raise CameraError(f"Invalid image data: {e}")
                    
                    capture_time = datetime.now()
                    
                    logger.info(
                        "Snapshot captured",
                        size_bytes=len(image_data),
                        timestamp=capture_time.isoformat()
                    )
                    
                    return image_data, capture_time
                    
        except aiohttp.ClientError as e:
            raise CameraError(f"Network error: {e}")
        except asyncio.TimeoutError:
            raise CameraError("Camera timeout")
        except Exception as e:
            raise CameraError(f"Unexpected error: {e}")
    
    async def test_connection(self) -> bool:
        """Test camera connectivity."""
        try:
            await self.capture_snapshot()
            logger.info("Camera connection test successful")
            return True
        except CameraError as e:
            logger.warning("Camera connection test failed", error=str(e))
            return False
    
    def get_camera_info(self) -> dict:
        """Get camera information."""
        return {
            "ip": self.ip,
            "port": self.port,
            "snapshot_url": self.snapshot_url,
            "username": self.username,
            # Don't log password for security
        }
