"""
RTSP camera integration for Image Sequence Server using ffmpeg.

Handles RTSP stream capture, frame extraction, and error handling.
"""

import asyncio
import subprocess
import tempfile
import os
from datetime import datetime
from typing import Tuple, Optional
import structlog
from PIL import Image
from io import BytesIO

logger = structlog.get_logger(__name__)


class CameraError(Exception):
    """Camera-related errors."""
    pass


class RTSPCamera:
    """RTSP camera client using ffmpeg for frame capture."""
    
    def __init__(
        self,
        ip: str,
        username: str,
        password: str,
        port: int = 554,
        rtsp_path: str = "/cam/realmonitor?channel=1&subtype=0",
        resolution: str = "1920x1080"
    ):
        self.ip = ip
        self.username = username
        self.password = password
        self.port = port
        self.rtsp_path = rtsp_path
        self.resolution = resolution
        
        # Build RTSP URL
        self.rtsp_url = f"rtsp://{username}:{password}@{ip}:{port}{rtsp_path}"
        
        logger.info("RTSP camera initialized", ip=ip, port=port, path=rtsp_path)
    
    async def capture_snapshot(self) -> Tuple[bytes, datetime]:
        """
        Capture a snapshot from the RTSP stream using ffmpeg.
        
        Returns:
            Tuple of (image_bytes, capture_timestamp)
            
        Raises:
            CameraError: If snapshot capture fails
        """
        try:
            # Create temporary file for the image
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Build ffmpeg command
            cmd = [
                'ffmpeg',
                '-y',  # Overwrite output file
                '-rtsp_transport', 'tcp',  # Use TCP for reliability
                '-i', self.rtsp_url,
                '-vframes', '1',  # Capture only 1 frame
                '-q:v', '2',  # High quality
                '-s', self.resolution,  # Set resolution
                '-f', 'image2',  # Output format
                temp_path
            ]
            
            # Run ffmpeg command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8') if stderr else "Unknown ffmpeg error"
                raise CameraError(f"ffmpeg failed: {error_msg}")
            
            # Read the captured image
            if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                raise CameraError("No image data captured")
            
            with open(temp_path, 'rb') as f:
                image_data = f.read()
            
            # Validate image
            try:
                with Image.open(BytesIO(image_data)) as img:
                    img.verify()
            except Exception as e:
                raise CameraError(f"Invalid image data: {e}")
            
            capture_time = datetime.now()
            
            logger.info(
                "RTSP snapshot captured",
                size_bytes=len(image_data),
                timestamp=capture_time.isoformat()
            )
            
            return image_data, capture_time
            
        except asyncio.TimeoutError:
            raise CameraError("ffmpeg timeout")
        except FileNotFoundError:
            raise CameraError("ffmpeg not found - please install ffmpeg")
        except Exception as e:
            raise CameraError(f"Unexpected error: {e}")
        finally:
            # Clean up temporary file
            try:
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception:
                pass  # Ignore cleanup errors
    
    async def test_connection(self) -> bool:
        """Test RTSP stream connectivity."""
        try:
            # Test with a very short timeout and single frame
            cmd = [
                'ffmpeg',
                '-y',
                '-rtsp_transport', 'tcp',
                '-i', self.rtsp_url,
                '-vframes', '1',
                '-t', '5',  # 5 second timeout
                '-f', 'null',  # Don't save output
                '-'
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10)
            
            if process.returncode == 0:
                logger.info("RTSP connection test successful")
                return True
            else:
                logger.warning("RTSP connection test failed", 
                             returncode=process.returncode,
                             stderr=stderr.decode('utf-8') if stderr else "")
                return False
                
        except asyncio.TimeoutError:
            logger.warning("RTSP connection test timeout")
            return False
        except FileNotFoundError:
            logger.warning("ffmpeg not found for connection test")
            return False
        except Exception as e:
            logger.warning("RTSP connection test failed", error=str(e))
            return False
    
    def get_camera_info(self) -> dict:
        """Get camera information."""
        return {
            "ip": self.ip,
            "port": self.port,
            "rtsp_url": f"rtsp://{self.username}:***@{self.ip}:{self.port}{self.rtsp_path}",
            "username": self.username,
            "resolution": self.resolution,
            "method": "rtsp_ffmpeg"
        }


# Backward compatibility alias
ONVIFCamera = RTSPCamera