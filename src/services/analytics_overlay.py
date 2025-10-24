"""
Snow Load Analytics Overlay System.

Creates mobile-optimized overlays for displaying snow analytics data
on camera images with professional styling and real-time updates.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import structlog

logger = structlog.get_logger(__name__)


class AnalyticsOverlay:
    """Creates analytics overlays for camera images."""
    
    def __init__(self, settings):
        self.settings = settings
        
        # Overlay configuration
        self.overlay_config = {
            "font_size_large": 32,  # Reduced from 48
            "font_size_medium": 24,  # Reduced from 36
            "font_size_small": 18,  # Reduced from 28
            "padding": 15,
            "corner_radius": 8,
            "opacity": 0.85,
            "colors": {
                "background": (0, 0, 0, 200),  # Semi-transparent black
                "text_primary": (255, 255, 255, 255),  # White
                "text_secondary": (200, 200, 200, 255),  # Light gray
                "success": (76, 175, 80, 255),  # Green
                "warning": (255, 152, 0, 255),  # Orange
                "danger": (244, 67, 54, 255),  # Red
                "info": (33, 150, 243, 255),  # Blue
            }
        }
    
    def create_analytics_overlay(self, image: np.ndarray, analytics_data: Dict) -> np.ndarray:
        """
        Create analytics overlay on the image.
        
        Args:
            image: Input image as numpy array
            analytics_data: Analytics data from SnowAnalytics
            
        Returns:
            Image with analytics overlay
        """
        try:
            # Convert numpy array to PIL Image
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            
            # Create overlay
            overlay_image = self._create_overlay_background(pil_image.size)
            draw = ImageDraw.Draw(overlay_image)
            
            # Get font (fallback to default if not available)
            try:
                font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 
                                              self.overlay_config["font_size_large"])
                font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 
                                                self.overlay_config["font_size_medium"])
                font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 
                                              self.overlay_config["font_size_small"])
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Draw analytics data
            self._draw_header(draw, analytics_data, font_large)
            self._draw_snow_data(draw, analytics_data, font_medium, font_small)
            self._draw_weather_data(draw, analytics_data, font_medium, font_small)
            self._draw_predictions(draw, analytics_data, font_medium, font_small)
            self._draw_status(draw, analytics_data, font_medium)
            
            # Position overlay in bottom-right corner
            image_width, image_height = pil_image.size
            overlay_width, overlay_height = overlay_image.size
            x_position = image_width - overlay_width - 20  # 20px margin from right
            y_position = image_height - overlay_height - 20  # 20px margin from bottom
            
            # Composite overlay onto image at bottom-right
            pil_image.paste(overlay_image, (x_position, y_position), overlay_image)
            
            # Convert back to numpy array
            result_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            return result_image
            
        except Exception as e:
            logger.error("Overlay creation failed", error=str(e))
            return image  # Return original image if overlay fails
    
    def _create_overlay_background(self, image_size: Tuple[int, int]) -> Image.Image:
        """Create semi-transparent overlay background."""
        width, height = image_size
        
        # Create larger overlay positioned in bottom-right corner
        overlay_width = min(450, width // 2.5)  # Increased from 350, width//3
        overlay_height = min(500, height // 1.8)  # Increased from 400, height//2
        
        overlay = Image.new('RGBA', (overlay_width, overlay_height), (0, 0, 0, 0))
        
        # Draw rounded rectangle background
        draw = ImageDraw.Draw(overlay)
        
        # Background rectangle
        bg_color = self.overlay_config["colors"]["background"]
        draw.rounded_rectangle(
            [(0, 0), (overlay_width, overlay_height)],
            radius=self.overlay_config["corner_radius"],
            fill=bg_color
        )
        
        return overlay
    
    def _draw_header(self, draw: ImageDraw.Draw, analytics_data: Dict, font_large):
        """Draw header with timestamp and location."""
        try:
            timestamp_str = analytics_data.get("timestamp", "")
            if timestamp_str:
                # Parse and format timestamp
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                formatted_time = dt.strftime("%I:%M %p")
            else:
                formatted_time = "N/A"
            
            # Header text
            header_text = f"Woodland Hills City"
            subheader_text = f"Snow Load Monitoring"
            time_text = f"{formatted_time}"
            
            # Draw header with better spacing
            y_pos = 20
            draw.text((20, y_pos), header_text, 
                     font=font_large, 
                     fill=self.overlay_config["colors"]["text_primary"])
            
            y_pos += 40  # Increased spacing
            draw.text((20, y_pos), subheader_text, 
                     font=font_large, 
                     fill=self.overlay_config["colors"]["info"])
            
            y_pos += 40  # Increased spacing
            draw.text((20, y_pos), time_text, 
                     font=font_large, 
                     fill=self.overlay_config["colors"]["text_secondary"])
            
        except Exception as e:
            logger.warning("Header drawing failed", error=str(e))
    
    def _draw_snow_data(self, draw: ImageDraw.Draw, analytics_data: Dict, font_medium, font_small):
        """Draw snow analysis data - DEPRECATED: Use create_minimal_overlay instead."""
        try:
            # Check if this is the new simplified data structure
            if "road_condition" in analytics_data:
                # New simplified structure - redirect to minimal overlay
                logger.warning("Using deprecated _draw_snow_data with new data structure. Use create_minimal_overlay instead.")
                return
            
            # Old structure (for backward compatibility)
            snow_analysis = analytics_data.get("snow_analysis", {})
            snow_coverage = snow_analysis.get("snow_coverage", 0.0)
            snow_depth = snow_analysis.get("snow_depth_inches", 0.0)
            confidence = snow_analysis.get("confidence", 0.0)
            
            y_pos = 140  # Moved down to avoid covering time
            
            # Snow coverage
            coverage_text = f"Snow Coverage: {snow_coverage:.1%}"
            draw.text((20, y_pos), coverage_text, 
                     font=font_medium, 
                     fill=self.overlay_config["colors"]["text_primary"])
            
            # Snow depth
            y_pos += 35  # Increased spacing
            depth_text = f"Snow Depth: {snow_depth:.1f}\""
            draw.text((20, y_pos), depth_text, 
                     font=font_medium, 
                     fill=self.overlay_config["colors"]["text_primary"])
            
            # Confidence
            y_pos += 35  # Increased spacing
            conf_text = f"Confidence: {confidence:.1%}"
            conf_color = self.overlay_config["colors"]["success"] if confidence > 0.7 else self.overlay_config["colors"]["warning"]
            draw.text((20, y_pos), conf_text, 
                     font=font_small, 
                     fill=conf_color)
            
        except Exception as e:
            logger.warning("Snow data drawing failed", error=str(e))
    
    def _draw_weather_data(self, draw: ImageDraw.Draw, analytics_data: Dict, font_medium, font_small):
        """Draw weather data - DEPRECATED: Use create_minimal_overlay instead."""
        try:
            # Check if this is the new simplified data structure
            if "road_condition" in analytics_data:
                # New simplified structure - redirect to minimal overlay
                logger.warning("Using deprecated _draw_weather_data with new data structure. Use create_minimal_overlay instead.")
                return
            
            # Old structure (for backward compatibility)
            weather_data = analytics_data.get("weather_data", {})
            temperature = weather_data.get("temperature", 32)
            conditions = weather_data.get("conditions", "Unknown")
            humidity = weather_data.get("humidity", 50)
            
            y_pos = 240  # Start after snow data section (moved down)
            
            # Temperature
            temp_text = f"Temperature: {temperature}°F"
            temp_color = self.overlay_config["colors"]["danger"] if temperature < 32 else self.overlay_config["colors"]["info"]
            draw.text((20, y_pos), temp_text, 
                     font=font_medium, 
                     fill=temp_color)
            
            # Conditions
            y_pos += 35  # Increased spacing
            cond_text = f"Conditions: {conditions}"
            draw.text((20, y_pos), cond_text, 
                     font=font_small, 
                     fill=self.overlay_config["colors"]["text_secondary"])
            
            # Humidity
            y_pos += 30  # Increased spacing
            hum_text = f"Humidity: {humidity}%"
            draw.text((20, y_pos), hum_text, 
                     font=font_small, 
                     fill=self.overlay_config["colors"]["text_secondary"])
            
        except Exception as e:
            logger.warning("Weather data drawing failed", error=str(e))
    
    def _draw_predictions(self, draw: ImageDraw.Draw, analytics_data: Dict, font_medium, font_small):
        """Draw predictions - DEPRECATED: Use create_minimal_overlay instead."""
        try:
            # Check if this is the new simplified data structure
            if "road_condition" in analytics_data:
                # New simplified structure - redirect to minimal overlay
                logger.warning("Using deprecated _draw_predictions with new data structure. Use create_minimal_overlay instead.")
                return
            
            # Old structure (for backward compatibility)
            predictions = analytics_data.get("predictions", {})
            accumulation = analytics_data.get("accumulation_rate", {})
            
            y_pos = 330  # Start after weather data section (moved down)
            
            # Accumulation rate
            rate = accumulation.get("rate_per_hour", 0.0)
            trend = accumulation.get("trend", "unknown")
            
            rate_text = f"Accumulation: {rate:+.1f}\"/hr"
            trend_text = f"Trend: {trend.title()}"
            
            draw.text((20, y_pos), rate_text, 
                     font=font_medium, 
                     fill=self.overlay_config["colors"]["text_primary"])
            
            y_pos += 30  # Increased spacing
            trend_color = self.overlay_config["colors"]["success"] if trend == "stable" else self.overlay_config["colors"]["warning"]
            draw.text((20, y_pos), trend_text, 
                     font=font_small, 
                     fill=trend_color)
            
        except Exception as e:
            logger.warning("Predictions drawing failed", error=str(e))
    
    def _draw_status(self, draw: ImageDraw.Draw, analytics_data: Dict, font_medium):
        """Draw road status - DEPRECATED: Use create_minimal_overlay instead."""
        try:
            # Check if this is the new simplified data structure
            if "road_condition" in analytics_data:
                # New simplified structure - redirect to minimal overlay
                logger.warning("Using deprecated _draw_status with new data structure. Use create_minimal_overlay instead.")
                return
            
            # Old structure (for backward compatibility)
            road_status = analytics_data.get("road_status", "Unknown")
            
            y_pos = 400  # Start after predictions section (moved down)
            
            # Clean up road status text and add proper checkmark
            if "Clear" in road_status:
                status_text = f"Road Status: ✓ Clear"
                status_color = self.overlay_config["colors"]["success"]
            elif "Hazardous" in road_status:
                status_text = f"Road Status: ⚠ Hazardous"
                status_color = self.overlay_config["colors"]["danger"]
            elif "Slippery" in road_status:
                status_text = f"Road Status: ⚠ Slippery"
                status_color = self.overlay_config["colors"]["warning"]
            elif "Wet" in road_status:
                status_text = f"Road Status: ⚠ Wet"
                status_color = self.overlay_config["colors"]["warning"]
            else:
                status_text = f"Road Status: ? {road_status}"
                status_color = self.overlay_config["colors"]["text_primary"]
            
            draw.text((20, y_pos), status_text, 
                     font=font_medium, 
                     fill=status_color)
            
        except Exception as e:
            logger.warning("Status drawing failed", error=str(e))
    
    def create_mobile_overlay(self, image: np.ndarray, analytics_data: Dict) -> np.ndarray:
        """Create mobile-optimized overlay - uses minimal overlay for better mobile experience."""
        return self.create_minimal_overlay(image, analytics_data)
    
    def create_minimal_overlay(self, image: np.ndarray, analytics_data: Dict) -> np.ndarray:
        """Create driver-focused minimal overlay with horizontal bottom layout."""
        try:
            # Convert to PIL
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil_image)
            
            # Get image dimensions
            width, height = pil_image.size
            
            # Get road condition and temperature
            condition = analytics_data.get("road_condition", "Unknown")
            temperature = analytics_data.get("temperature", "N/A")
            
            # Color coding for urgency
            color_map = {
                "Clear": (0, 255, 0),      # Green - safe
                "Light": (0, 255, 255),   # Yellow - caution
                "Moderate": (0, 165, 255), # Orange - warning
                "Heavy": (0, 0, 255),     # Red - danger
                "Ice Possible": (255, 0, 255)  # Purple - ice warning
            }
            
            color = color_map.get(condition, (255, 255, 255))
            
            # Load fonts - all the same size for consistency
            font_size = 36  # Uniform font size
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # Helper function to draw text (no individual background boxes)
            def draw_text_simple(text, x, y, font, text_color):
                # Draw text directly
                draw.text((x, y), text, font=font, fill=text_color)
                
                # Return text width for spacing calculations
                bbox = draw.textbbox((0, 0), text, font=font)
                return bbox[2] - bbox[0]
            
            # Draw location name in top-left corner with individual background box
            margin = 30
            location_text = "Woodland Hills City Center"
            
            # Draw location with individual background box (keep this one separate)
            bbox = draw.textbbox((0, 0), location_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            padding = 8
            bg_x1 = margin - padding
            bg_y1 = margin - padding
            bg_x2 = margin + text_width + padding
            bg_y2 = margin + text_height + padding
            draw.rectangle([bg_x1, bg_y1, bg_x2, bg_y2], fill=(0, 0, 0, 200))
            draw.text((margin, margin), location_text, font=font, fill=(255, 255, 255, 255))
            
            # Calculate bottom 1/8th area for continuous black bar
            bottom_area_height = height // 8
            bar_y1 = height - bottom_area_height
            bar_y2 = height
            
            # Draw continuous black bar across entire bottom
            draw.rectangle([0, bar_y1, width, bar_y2], fill=(0, 0, 0, 200))
            
            # Calculate text position (centered vertically in the bar)
            text_y = bar_y1 + (bottom_area_height - text_height) // 2
            
            # Prepare all text elements for horizontal layout
            elements = []
            
            # Road Condition
            road_text = f"Road Condition: {condition}"
            elements.append((road_text, color))
            
            # Forecast alerts (up to 2 to fit horizontally)
            alerts = analytics_data.get("forecast_alerts", [])[:2]
            for alert in alerts:
                alert_text = f"⚠ {alert}"
                elements.append((alert_text, (255, 255, 0, 255)))
            
            # Timestamp
            timestamp_str = analytics_data.get("timestamp", "")
            if timestamp_str:
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                time_text = dt.strftime("%I:%M %p")
            else:
                time_text = "N/A"
            elements.append((time_text, (255, 255, 255, 255)))
            
            # Temperature (on the far right)
            temp_text = f"Temp: {temperature}"
            elements.append((temp_text, (255, 255, 255, 255)))
            
            # Calculate total width needed and spacing
            total_text_width = 0
            for text, _ in elements:
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                total_text_width += text_width + 30  # 30px spacing between elements
            
            # Start position to center the elements horizontally
            start_x = (width - total_text_width) // 2
            start_x = max(margin, start_x)  # Ensure we don't go off-screen
            
            # Draw all elements horizontally on the black bar
            current_x = start_x
            for text, text_color in elements:
                element_width = draw_text_simple(
                    text, current_x, text_y, font, text_color
                )
                current_x += element_width + 30  # 30px spacing between elements
            
            # Convert back to numpy
            result_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            return result_image
            
        except Exception as e:
            logger.error("Minimal overlay creation failed", error=str(e))
            return image
