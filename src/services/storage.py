"""
Storage management service for Image Sequence Server.

Handles file storage, cleanup, and storage monitoring.
"""

import asyncio
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple

import structlog

logger = structlog.get_logger(__name__)


class StorageManager:
    """Manages file storage and cleanup operations."""
    
    def __init__(
        self,
        images_dir: Path,
        sequences_dir: Path,
        max_storage_mb: int = 1024
    ):
        self.images_dir = images_dir
        self.sequences_dir = sequences_dir
        self.max_storage_mb = max_storage_mb
        
        # Ensure directories exist
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.sequences_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Storage manager initialized", max_storage_mb=max_storage_mb)
    
    async def save_image(
        self,
        image_data: bytes,
        timestamp: datetime,
        prefix: str = "snapshot"
    ) -> Path:
        """
        Save image data to storage.
        
        Args:
            image_data: Raw image bytes
            timestamp: Image timestamp
            prefix: Filename prefix
            
        Returns:
            Path to saved image
        """
        try:
            # Generate filename
            filename = f"{prefix}_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
            file_path = self.images_dir / filename
            
            # Save image
            with open(file_path, 'wb') as f:
                f.write(image_data)
            
            logger.info("Image saved", path=str(file_path), size_bytes=len(image_data))
            return file_path
            
        except Exception as e:
            logger.error("Failed to save image", error=str(e))
            raise
    
    async def get_recent_images(
        self,
        minutes: int = 5,
        max_images: int = 60
    ) -> List[Tuple[Path, datetime]]:
        """
        Get recent images within specified time window.
        
        Args:
            minutes: Time window in minutes
            max_images: Maximum number of images to return
            
        Returns:
            List of (file_path, timestamp) tuples
        """
        try:
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            images = []
            
            for file_path in self.images_dir.glob("*.jpg"):
                if file_path.stat().st_mtime >= cutoff_time.timestamp():
                    # Extract timestamp from filename
                    try:
                        timestamp_str = file_path.stem.split('_', 1)[1]
                        timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                        images.append((file_path, timestamp))
                    except (ValueError, IndexError):
                        # Fallback to file modification time
                        timestamp = datetime.fromtimestamp(file_path.stat().st_mtime)
                        images.append((file_path, timestamp))
            
            # Sort by timestamp (oldest first) and limit
            images.sort(key=lambda x: x[1], reverse=False)
            images = images[:max_images]
            
            logger.info("Recent images retrieved", count=len(images), minutes=minutes)
            return images
            
        except Exception as e:
            logger.error("Failed to get recent images", error=str(e))
            return []
    
    async def cleanup_old_files(
        self,
        max_age_hours: int = 24
    ) -> Tuple[int, int]:
        """
        Clean up old files to manage storage.
        
        Args:
            max_age_hours: Maximum age of files to keep
            
        Returns:
            Tuple of (images_deleted, sequences_deleted)
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            images_deleted = 0
            sequences_deleted = 0
            
            # Clean up old images
            for file_path in self.images_dir.glob("*.jpg"):
                if file_path.stat().st_mtime < cutoff_time.timestamp():
                    file_path.unlink()
                    images_deleted += 1
            
            # Clean up old sequences
            for file_path in self.sequences_dir.glob("*.gif"):
                if file_path.stat().st_mtime < cutoff_time.timestamp():
                    file_path.unlink()
                    sequences_deleted += 1
            
            logger.info(
                "File cleanup completed",
                images_deleted=images_deleted,
                sequences_deleted=sequences_deleted
            )
            
            return images_deleted, sequences_deleted
            
        except Exception as e:
            logger.error("Failed to cleanup old files", error=str(e))
            return 0, 0
    
    async def get_storage_usage(self) -> dict:
        """
        Get current storage usage statistics.
        
        Returns:
            Dictionary with storage statistics
        """
        try:
            def get_dir_size(path: Path) -> int:
                """Calculate directory size in bytes."""
                total = 0
                for file_path in path.rglob("*"):
                    if file_path.is_file():
                        total += file_path.stat().st_size
                return total
            
            images_size = get_dir_size(self.images_dir)
            sequences_size = get_dir_size(self.sequences_dir)
            total_size = images_size + sequences_size
            
            # Count files
            image_count = len(list(self.images_dir.glob("*.jpg")))
            sequence_count = len(list(self.sequences_dir.glob("*.gif")))
            
            usage = {
                "images_size_mb": round(images_size / (1024 * 1024), 2),
                "sequences_size_mb": round(sequences_size / (1024 * 1024), 2),
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "max_storage_mb": self.max_storage_mb,
                "usage_percent": round((total_size / (1024 * 1024)) / self.max_storage_mb * 100, 2),
                "image_count": image_count,
                "sequence_count": sequence_count
            }
            
            logger.info("Storage usage calculated", **usage)
            return usage
            
        except Exception as e:
            logger.error("Failed to calculate storage usage", error=str(e))
            return {}
    
    async def enforce_storage_limits(self) -> bool:
        """
        Enforce storage limits by cleaning up old files.
        
        Returns:
            True if cleanup was performed
        """
        try:
            usage = await self.get_storage_usage()
            
            if usage.get("usage_percent", 0) > 90:  # Cleanup at 90% usage
                logger.warning("Storage usage high, performing cleanup")
                await self.cleanup_old_files(max_age_hours=12)  # More aggressive cleanup
                return True
            
            return False
            
        except Exception as e:
            logger.error("Failed to enforce storage limits", error=str(e))
            return False
