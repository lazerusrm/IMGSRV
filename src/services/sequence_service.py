"""
Main application service for Image Sequence Server.

Coordinates camera capture, image processing, and sequence generation.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import structlog

from src.config import Settings
from src.services.camera import ONVIFCamera, CameraError
from src.services.image_processor import ImageProcessor
from src.services.storage import StorageManager
from src.services.vps_sync import VPSSynchronizer

logger = structlog.get_logger(__name__)


class ImageSequenceService:
    """Main service for managing image sequences."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        
        # Initialize components
        self.camera = ONVIFCamera(
            ip=settings.camera_ip,
            username=settings.camera_username,
            password=settings.camera_password,
            port=settings.camera_port,
            rtsp_path=settings.camera_rtsp_path,
            resolution=settings.camera_resolution
        )
        
        self.image_processor = ImageProcessor(
            output_width=settings.image_width,
            output_height=settings.image_height,
            image_quality=settings.image_quality
        )
        
        self.storage = StorageManager(
            images_dir=settings.images_dir,
            sequences_dir=settings.sequences_dir,
            max_storage_mb=settings.max_storage_mb
        )
        
        self.vps_sync = VPSSynchronizer(settings)
        
        # State management
        self.is_running = False
        self.last_sequence_update = None
        self.capture_task: Optional[asyncio.Task] = None
        
        logger.info("Image sequence service initialized")
    
    async def start(self):
        """Start the image sequence service."""
        try:
            self.is_running = True
            
            # Test camera connection (non-blocking)
            camera_available = await self.camera.test_connection()
            if camera_available:
                logger.info("Camera connection test successful")
            else:
                logger.warning("Camera connection test failed - service will start without camera")
            
            # Start background tasks
            self.capture_task = asyncio.create_task(self._capture_loop())
            
            logger.info("Image sequence service started")
            
        except Exception as e:
            logger.error("Failed to start service", error=str(e))
            raise
    
    async def stop(self):
        """Stop the image sequence service."""
        try:
            self.is_running = False
            
            if self.capture_task:
                self.capture_task.cancel()
                try:
                    await self.capture_task
                except asyncio.CancelledError:
                    pass
            
            logger.info("Image sequence service stopped")
            
        except Exception as e:
            logger.error("Failed to stop service", error=str(e))
    
    async def _capture_loop(self):
        """Background task for continuous image capture."""
        consecutive_failures = 0
        max_consecutive_failures = 5
        
        while self.is_running:
            try:
                # Capture snapshot
                image_data, timestamp = await self.camera.capture_snapshot()
                
                # Save image
                await self.storage.save_image(image_data, timestamp)
                
                # Reset failure counter on success
                consecutive_failures = 0
                
                # Check if we need to update sequence
                await self._check_sequence_update()
                
                # Enforce storage limits
                await self.storage.enforce_storage_limits()
                
                # Wait before next capture (every 30-60 seconds for 5-10 image sequence)
                await asyncio.sleep(45)  # Capture every 45 seconds
                
            except CameraError as e:
                consecutive_failures += 1
                logger.warning("Camera error in capture loop", error=str(e), failures=consecutive_failures)
                
                if consecutive_failures >= max_consecutive_failures:
                    logger.error("Too many consecutive camera failures, reducing capture frequency")
                    await asyncio.sleep(300)  # Wait 5 minutes
                else:
                    await asyncio.sleep(60)  # Wait 1 minute
                    
            except Exception as e:
                consecutive_failures += 1
                logger.error("Unexpected error in capture loop", error=str(e), failures=consecutive_failures)
                await asyncio.sleep(30)
    
    async def _check_sequence_update(self):
        """Check if sequence needs to be updated."""
        try:
            now = datetime.now()
            
            # Check if it's time to update sequence
            if (self.last_sequence_update is None or 
                now - self.last_sequence_update >= timedelta(minutes=self.settings.sequence_update_interval_minutes)):
                
                await self.generate_sequence()
                self.last_sequence_update = now
                
        except Exception as e:
            logger.error("Failed to check sequence update", error=str(e))
    
    async def generate_sequence(self) -> Optional[Path]:
        """
        Generate a new image sequence from recent images.
        
        Returns:
            Path to generated sequence file, or None if failed
        """
        try:
            # Get recent images
            recent_images = await self.storage.get_recent_images(
                minutes=self.settings.sequence_duration_minutes,
                max_images=self.settings.max_images_per_sequence
            )
            
            if not recent_images:
                logger.warning("No recent images available for sequence")
                return None
            
            # Load image data
            images_with_data = []
            for file_path, timestamp in recent_images:
                try:
                    with open(file_path, 'rb') as f:
                        image_data = f.read()
                    images_with_data.append((image_data, timestamp))
                except Exception as e:
                    logger.warning("Failed to load image", path=str(file_path), error=str(e))
            
            if not images_with_data:
                logger.warning("No valid images loaded for sequence")
                return None
            
            # Generate sequence filename
            sequence_filename = f"sequence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.gif"
            sequence_path = self.settings.sequences_dir / sequence_filename
            
            # Create sequence
            await self.image_processor.create_image_sequence(
                images_with_data,
                sequence_path,
                duration_seconds=5
            )
            
            # Clean up old sequences (keep only the latest 3)
            await self._cleanup_old_sequences()
            
            # Sync to VPS if enabled
            if self.vps_sync.enabled:
                sync_success = await self.vps_sync.sync_to_vps(self.settings.sequences_dir)
                if sync_success:
                    logger.info("Sequence synchronized to VPS")
                else:
                    logger.warning("VPS synchronization failed")
            
            logger.info("Image sequence generated", path=str(sequence_path))
            return sequence_path
            
        except Exception as e:
            logger.error("Failed to generate sequence", error=str(e))
            return None
    
    async def _cleanup_old_sequences(self):
        """Clean up old sequence files, keeping only the latest ones."""
        try:
            sequence_files = list(self.settings.sequences_dir.glob("*.gif"))
            sequence_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Keep only the latest 3 sequences
            for old_sequence in sequence_files[3:]:
                old_sequence.unlink()
                logger.info("Old sequence deleted", path=str(old_sequence))
                
        except Exception as e:
            logger.error("Failed to cleanup old sequences", error=str(e))
    
    async def get_latest_sequence(self) -> Optional[Path]:
        """Get the path to the latest sequence file."""
        try:
            sequence_files = list(self.settings.sequences_dir.glob("*.gif"))
            if not sequence_files:
                return None
            
            # Return the most recent sequence
            latest = max(sequence_files, key=lambda x: x.stat().st_mtime)
            return latest
            
        except Exception as e:
            logger.error("Failed to get latest sequence", error=str(e))
            return None
    
    async def get_status(self) -> dict:
        """Get service status information."""
        try:
            storage_usage = await self.storage.get_storage_usage()
            latest_sequence = await self.get_latest_sequence()
            
            status = {
                "is_running": self.is_running,
                "last_sequence_update": self.last_sequence_update.isoformat() if self.last_sequence_update else None,
                "camera_info": self.camera.get_camera_info(),
                "storage_usage": storage_usage,
                "latest_sequence": str(latest_sequence) if latest_sequence else None,
                "settings": {
                    "sequence_duration_minutes": self.settings.sequence_duration_minutes,
                    "sequence_update_interval_minutes": self.settings.sequence_update_interval_minutes,
                    "max_images_per_sequence": self.settings.max_images_per_sequence
                },
                "vps_sync_status": self.vps_sync.get_sync_status()
            }
            
            return status
            
        except Exception as e:
            logger.error("Failed to get status", error=str(e))
            return {"error": str(e)}
