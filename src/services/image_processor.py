"""
Image processing service for generating traffic camera-style sequences.

Handles image manipulation, timestamp overlay, and sequence generation.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from io import BytesIO

import structlog
from PIL import Image, ImageDraw, ImageFont

logger = structlog.get_logger(__name__)


class ImageProcessor:
    """Handles image processing and sequence generation."""
    
    def __init__(
        self,
        output_width: int = 1920,
        output_height: int = 1080,
        image_quality: int = 85,
        font_size: int = 24
    ):
        self.output_width = output_width
        self.output_height = output_height
        self.image_quality = image_quality
        self.font_size = font_size
        
        # Try to load a system font, fallback to default
        try:
            self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except OSError:
            try:
                self.font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
            except OSError:
                self.font = ImageFont.load_default()
                logger.warning("Using default font - timestamp may not display optimally")
        
        logger.info("Image processor initialized", width=output_width, height=output_height)
    
    async def add_timestamp_overlay(
        self,
        image_data: bytes,
        timestamp: datetime,
        location: str = "Woodland Hills City Center"
    ) -> bytes:
        """
        Add traffic camera-style timestamp overlay to image.
        
        Args:
            image_data: Raw image bytes
            timestamp: Timestamp to overlay
            location: Location text to display
            
        Returns:
            Modified image bytes
        """
        try:
            # Open image
            with Image.open(BytesIO(image_data)) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize to target dimensions
                img = img.resize((self.output_width, self.output_height), Image.Resampling.LANCZOS)
                
                # Create overlay
                overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
                draw = ImageDraw.Draw(overlay)
                
                # Format timestamp with sanitized time (rounded to nearest 5 minutes)
                # Round timestamp to nearest 5 minutes for security
                rounded_minute = (timestamp.minute // 5) * 5
                sanitized_timestamp = timestamp.replace(minute=rounded_minute, second=0, microsecond=0)
                time_str = sanitized_timestamp.strftime("%A, %B %d, %Y  %I:%M %p")
                
                # Calculate text positions
                margin = 20
                line_height = self.font_size + 5
                
                # Draw background rectangles for text
                location_bbox = draw.textbbox((0, 0), location, font=self.font)
                time_bbox = draw.textbbox((0, 0), time_str, font=self.font)
                
                location_width = location_bbox[2] - location_bbox[0]
                time_width = time_bbox[2] - time_bbox[0]
                
                # Background rectangles
                draw.rectangle([
                    margin, margin,
                    margin + location_width + 10, margin + line_height + 10
                ], fill=(0, 0, 0, 180))
                
                draw.rectangle([
                    margin, margin + line_height + 5,
                    margin + time_width + 10, margin + (line_height * 2) + 15
                ], fill=(0, 0, 0, 180))
                
                # Draw text
                draw.text((margin + 5, margin + 5), location, fill=(255, 255, 255), font=self.font)
                draw.text((margin + 5, margin + line_height + 10), time_str, fill=(255, 255, 255), font=self.font)
                
                # Composite overlay onto image
                img_rgba = img.convert('RGBA')
                final_img = Image.alpha_composite(img_rgba, overlay)
                final_img = final_img.convert('RGB')
                
                # Save to bytes
                output = BytesIO()
                final_img.save(output, format='JPEG', quality=self.image_quality, optimize=True)
                
                logger.info("Timestamp overlay added", timestamp=timestamp.isoformat())
                return output.getvalue()
                
        except Exception as e:
            logger.error("Failed to add timestamp overlay", error=str(e))
            raise
    
    async def create_image_sequence(
        self,
        images: List[Tuple[bytes, datetime]],
        output_path: Path,
        duration_seconds: int = 5
    ) -> Path:
        """
        Create an image sequence (animated GIF) from captured images.
        
        Args:
            images: List of (image_bytes, timestamp) tuples
            output_path: Path to save the sequence
            duration_seconds: Duration to display each frame
            
        Returns:
            Path to the created sequence file
        """
        try:
            if not images:
                raise ValueError("No images provided for sequence")
            
            processed_images = []
            
            # Process each image with timestamp overlay
            for img_data, timestamp in images:
                processed_img = await self.add_timestamp_overlay(img_data, timestamp)
                processed_images.append(processed_img)
            
            # Create animated GIF
            frames = []
            for img_data in processed_images:
                with Image.open(BytesIO(img_data)) as img:
                    frames.append(img.copy())
            
            if frames:
                # Calculate frame duration for 1 FPS (1000ms per frame)
                frame_duration = 1000  # 1 second per frame for 1 FPS
                
                # Save as animated GIF
                frames[0].save(
                    output_path,
                    save_all=True,
                    append_images=frames[1:],
                    duration=frame_duration,
                    loop=0,
                    optimize=True
                )
                
                logger.info(
                    "Image sequence created",
                    frames=len(frames),
                    duration_ms=frame_duration,
                    output_path=str(output_path)
                )
            
            return output_path
            
        except Exception as e:
            logger.error("Failed to create image sequence", error=str(e))
            raise
    
    async def create_image_sequence_with_analytics(
        self,
        images: List[Tuple[bytes, datetime]],
        output_path: Path,
        duration_seconds: int = 5,
        analytics_data: Optional[Dict] = None,
        overlay_style: str = "minimal",
        optimization_level: str = "balanced"
    ) -> Path:
        """
        Create an image sequence with optional analytics overlay and optimization.
        
        Args:
            images: List of (image_bytes, timestamp) tuples
            output_path: Path to save the sequence
            duration_seconds: Duration to display each frame
            analytics_data: Analytics data for overlay
            overlay_style: Style of overlay (full, minimal, mobile, none)
            optimization_level: GIF optimization level (low, balanced, aggressive)
            
        Returns:
            Path to the created sequence file
        """
        try:
            if not images:
                raise ValueError("No images provided for sequence")

            frames = []
            
            for image_data, timestamp in images:
                # Process image with timestamp
                processed_image = await self.add_timestamp_overlay(image_data, timestamp)
                
                # Add analytics overlay if data provided
                if analytics_data and overlay_style != "none":
                    try:
                        import cv2
                        import numpy as np
                        from src.services.analytics_overlay import AnalyticsOverlay
                        
                        # Convert PIL to OpenCV format
                        pil_image = Image.open(BytesIO(processed_image))
                        cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                        
                        # Create overlay
                        overlay = AnalyticsOverlay(None)  # We don't need settings for this
                        
                        if overlay_style == "minimal":
                            cv_image = overlay.create_minimal_overlay(cv_image, analytics_data)
                        else:
                            cv_image = overlay.create_analytics_overlay(cv_image, analytics_data)
                        
                        # Convert back to PIL
                        processed_image = cv2.imencode('.jpg', cv_image)[1].tobytes()
                        
                    except Exception as e:
                        logger.warning("Analytics overlay failed", error=str(e))
                        # Continue without overlay
                
                # Convert to PIL Image and resize for web optimization
                frame = Image.open(BytesIO(processed_image))
                
                # Resize to 1280x720 for web serving (balanced quality/size)
                if frame.size != (1280, 720):
                    frame = frame.resize((1280, 720), Image.Resampling.LANCZOS)
                
                # Apply color quantization based on optimization level
                if optimization_level == "aggressive":
                    frame = frame.convert('P', palette=Image.Palette.ADAPTIVE, colors=128)
                elif optimization_level == "balanced":
                    frame = frame.convert('P', palette=Image.Palette.ADAPTIVE, colors=192)
                else:  # low
                    frame = frame.convert('P', palette=Image.Palette.ADAPTIVE, colors=256)
                
                frames.append(frame)
            
            if frames:
                # Calculate frame duration in milliseconds
                frame_duration = duration_seconds * 1000
                
                # Save as optimized animated GIF
                frames[0].save(
                    output_path,
                    save_all=True,
                    append_images=frames[1:],
                    duration=frame_duration,
                    loop=0,
                    optimize=True,
                    quality=85 if optimization_level != "aggressive" else 75
                )
                
                # Get file size for logging
                file_size_kb = output_path.stat().st_size / 1024 if output_path.exists() else 0
                
                logger.info(
                    "Optimized image sequence created",
                    frames=len(frames),
                    duration_ms=frame_duration,
                    output_path=str(output_path),
                    overlay_style=overlay_style,
                    optimization_level=optimization_level,
                    file_size_kb=round(file_size_kb, 2)
                )
            
            return output_path
            
        except Exception as e:
            logger.error("Failed to create image sequence with analytics", error=str(e))
            raise
    
    async def cleanup_old_images(
        self,
        images_dir: Path,
        max_age_hours: int = 24
    ) -> int:
        """
        Clean up old image files to manage storage.
        
        Args:
            images_dir: Directory containing images
            max_age_hours: Maximum age of images to keep
            
        Returns:
            Number of files deleted
        """
        try:
            if not images_dir.exists():
                return 0
            
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            deleted_count = 0
            
            for file_path in images_dir.glob("*.jpg"):
                if file_path.stat().st_mtime < cutoff_time.timestamp():
                    file_path.unlink()
                    deleted_count += 1
            
            logger.info("Image cleanup completed", deleted_count=deleted_count)
            return deleted_count
            
        except Exception as e:
            logger.error("Failed to cleanup old images", error=str(e))
            return 0
