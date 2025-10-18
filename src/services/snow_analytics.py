"""
Snow Load Analytics Service for Image Sequence Server.

Implements computer vision-based snow load detection and analysis using:
- Edge detection for road boundary identification
- Color temperature analysis for snow coverage detection
- Weather data integration for context and predictions
- Accumulation rate tracking over time
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import structlog
import aiohttp

from src.config import Settings

logger = structlog.get_logger(__name__)


class SnowAnalyticsError(Exception):
    """Snow analytics related errors."""
    pass


class WeatherDataClient:
    """Client for fetching weather data from public APIs."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.cache_duration = 300  # 5 minutes
        self._cache = {}
    
    async def get_current_weather(self, lat: float = 40.0, lon: float = -74.0) -> Dict:
        """Get current weather data from NOAA API."""
        cache_key = f"weather_{lat}_{lon}"
        now = datetime.now()
        
        # Check cache
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if (now - timestamp).seconds < self.cache_duration:
                return cached_data
        
        try:
            # Use NOAA API for weather data
            url = f"https://api.weather.gov/points/{lat},{lon}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract current conditions from NOAA API
                        weather_data = {
                            "temperature": 45,  # More realistic default for Utah
                            "precipitation_rate": 0.0,
                            "humidity": 45,
                            "conditions": "Clear",
                            "timestamp": now.isoformat()
                        }
                        
                        # Try to extract real weather data from NOAA response
                        try:
                            if "properties" in data and "forecast" in data["properties"]:
                                forecast_url = data["properties"]["forecast"]
                                async with session.get(forecast_url) as forecast_response:
                                    if forecast_response.status == 200:
                                        forecast_data = await forecast_response.json()
                                        if "properties" in forecast_data and "periods" in forecast_data["properties"]:
                                            current_period = forecast_data["properties"]["periods"][0]
                                            weather_data.update({
                                                "temperature": current_period.get("temperature", 45),
                                                "conditions": current_period.get("shortForecast", "Clear"),
                                                "humidity": current_period.get("relativeHumidity", {}).get("value", 45)
                                            })
                        except Exception as e:
                            logger.debug("Could not parse detailed weather data", error=str(e))
                        
                        # Cache the result
                        self._cache[cache_key] = (weather_data, now)
                        return weather_data
                    else:
                        logger.warning("Weather API request failed", status=response.status)
                        return self._get_fallback_weather()
        
        except Exception as e:
            logger.warning("Weather data fetch failed", error=str(e))
            return self._get_fallback_weather()
    
    def _get_fallback_weather(self) -> Dict:
        """Return fallback weather data when API fails."""
        return {
            "temperature": 45,  # More realistic for Utah
            "precipitation_rate": 0.0,
            "humidity": 45,
            "conditions": "Clear",
            "timestamp": datetime.now().isoformat(),
            "source": "fallback"
        }


class RoadDetector:
    """Detects road boundaries using edge detection."""
    
    def __init__(self):
        self.roi_points = None  # Region of Interest points
        self.roi_mask = None
    
    def detect_road_boundaries(self, image: np.ndarray) -> np.ndarray:
        """
        Detect road boundaries using edge detection.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Binary mask of road area
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Edge detection using Canny
            edges = cv2.Canny(blurred, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Create road mask (simplified approach)
            height, width = image.shape[:2]
            road_mask = np.zeros((height, width), dtype=np.uint8)
            
            # Assume road is in the center-bottom area of the image
            # This is a simplified approach - in production, you'd use more sophisticated methods
            road_region = np.array([
                [width * 0.1, height * 0.7],  # Bottom left
                [width * 0.9, height * 0.7],  # Bottom right
                [width * 0.8, height * 0.9],  # Bottom right corner
                [width * 0.2, height * 0.9],  # Bottom left corner
            ], np.int32)
            
            cv2.fillPoly(road_mask, [road_region], 255)
            
            return road_mask
            
        except Exception as e:
            logger.error("Road detection failed", error=str(e))
            # Return a default mask covering bottom half of image
            height, width = image.shape[:2]
            mask = np.zeros((height, width), dtype=np.uint8)
            mask[height//2:, :] = 255
            return mask


class SnowDetector:
    """Detects snow coverage using color temperature analysis."""
    
    def __init__(self):
        self.snow_threshold = 0.7  # Threshold for snow detection
        self.baseline_image = None
        self.baseline_timestamp = None
    
    def analyze_snow_coverage(self, image: np.ndarray, road_mask: np.ndarray) -> Dict:
        """
        Analyze snow coverage in the road area.
        
        Args:
            image: Input image as numpy array
            road_mask: Binary mask of road area
            
        Returns:
            Dictionary with snow analysis results
        """
        try:
            # Convert to HSV for better color analysis
            hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
            
            # Apply road mask
            masked_hsv = cv2.bitwise_and(hsv, hsv, mask=road_mask)
            
            # Define snow color range (white/light colors)
            # Snow typically has high value (brightness) and low saturation
            lower_snow = np.array([0, 0, 200])  # Low hue, low sat, high value
            upper_snow = np.array([180, 30, 255])  # High hue, low sat, high value
            
            # Create snow mask
            snow_mask = cv2.inRange(masked_hsv, lower_snow, upper_snow)
            
            # Calculate snow coverage percentage
            road_pixels = np.sum(road_mask > 0)
            snow_pixels = np.sum(snow_mask > 0)
            
            if road_pixels > 0:
                snow_coverage = snow_pixels / road_pixels
            else:
                snow_coverage = 0.0
            
            # Analyze snow depth (simplified)
            snow_depth = self._estimate_snow_depth(snow_mask, road_mask)
            
            return {
                "snow_coverage": snow_coverage,
                "snow_depth_inches": snow_depth,
                "road_pixels": int(road_pixels),
                "snow_pixels": int(snow_pixels),
                "confidence": min(snow_coverage * 2, 1.0)  # Simple confidence metric
            }
            
        except Exception as e:
            logger.error("Snow analysis failed", error=str(e))
            return {
                "snow_coverage": 0.0,
                "snow_depth_inches": 0.0,
                "road_pixels": 0,
                "snow_pixels": 0,
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _estimate_snow_depth(self, snow_mask: np.ndarray, road_mask: np.ndarray) -> float:
        """Estimate snow depth based on snow pixel intensity."""
        try:
            # This is a simplified depth estimation
            # In production, you'd use more sophisticated methods
            snow_intensity = np.mean(snow_mask[snow_mask > 0]) if np.any(snow_mask) else 0
            
            # Convert intensity to estimated depth (more conservative approach)
            # Only show significant depth for very bright snow pixels
            depth_factor = snow_intensity / 255.0
            
            # More conservative depth estimation
            if depth_factor > 0.9:  # Very bright snow
                estimated_depth = depth_factor * 2.0  # Max 2 inches
            elif depth_factor > 0.7:  # Bright snow
                estimated_depth = depth_factor * 1.0  # Max 1 inch
            elif depth_factor > 0.5:  # Moderate snow
                estimated_depth = depth_factor * 0.5  # Max 0.5 inches
            else:  # Light snow
                estimated_depth = depth_factor * 0.2  # Max 0.2 inches
            
            return round(estimated_depth, 1)
            
        except Exception:
            return 0.0


class SnowAnalytics:
    """Main snow analytics service."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.weather_client = WeatherDataClient(settings)
        self.road_detector = RoadDetector()
        self.snow_detector = SnowDetector()
        
        # Analytics data storage
        self.analytics_dir = Path(settings.data_dir) / "analytics"
        self.analytics_dir.mkdir(exist_ok=True)
        
        # Historical data
        self.historical_data = []
        self.max_history = 100  # Keep last 100 measurements
        
        logger.info("Snow analytics service initialized")
    
    async def analyze_image(self, image_path: Path, timestamp: datetime) -> Dict:
        """
        Analyze a single image for snow load data.
        
        Args:
            image_path: Path to the image file
            timestamp: When the image was captured
            
        Returns:
            Dictionary with complete analysis results
        """
        try:
            # Load image
            image = cv2.imread(str(image_path))
            if image is None:
                raise SnowAnalyticsError(f"Could not load image: {image_path}")
            
            # Convert BGR to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Detect road boundaries
            road_mask = self.road_detector.detect_road_boundaries(image_rgb)
            
            # Analyze snow coverage
            snow_analysis = self.snow_detector.analyze_snow_coverage(image_rgb, road_mask)
            
            # Get weather data
            weather_data = await self.weather_client.get_current_weather()
            
            # Calculate accumulation rate
            accumulation_rate = self._calculate_accumulation_rate(snow_analysis)
            
            # Generate predictions
            predictions = self._generate_predictions(snow_analysis, weather_data)
            
            # Compile results
            analysis_result = {
                "timestamp": timestamp.isoformat(),
                "image_path": str(image_path),
                "snow_analysis": snow_analysis,
                "weather_data": weather_data,
                "accumulation_rate": accumulation_rate,
                "predictions": predictions,
                "road_status": self._determine_road_status(snow_analysis, weather_data)
            }
            
            # Store historical data
            self._store_historical_data(analysis_result)
            
            logger.info("Image analysis completed", 
                       snow_coverage=snow_analysis["snow_coverage"],
                       snow_depth=snow_analysis["snow_depth_inches"])
            
            return analysis_result
            
        except Exception as e:
            logger.error("Image analysis failed", error=str(e), image_path=str(image_path))
            raise SnowAnalyticsError(f"Analysis failed: {e}")
    
    def _calculate_accumulation_rate(self, snow_analysis: Dict) -> Dict:
        """Calculate snow accumulation rate based on historical data."""
        if len(self.historical_data) < 2:
            return {"rate_per_hour": 0.0, "trend": "insufficient_data"}
        
        try:
            # Get last two measurements
            recent_data = self.historical_data[-2:]
            
            # Calculate time difference
            time1 = datetime.fromisoformat(recent_data[0]["timestamp"])
            time2 = datetime.fromisoformat(recent_data[1]["timestamp"])
            time_diff_hours = (time2 - time1).total_seconds() / 3600
            
            if time_diff_hours <= 0:
                return {"rate_per_hour": 0.0, "trend": "no_change"}
            
            # Calculate depth difference
            depth1 = recent_data[0]["snow_analysis"]["snow_depth_inches"]
            depth2 = recent_data[1]["snow_analysis"]["snow_depth_inches"]
            depth_diff = depth2 - depth1
            
            # Calculate rate
            rate_per_hour = depth_diff / time_diff_hours
            
            # Determine trend
            if rate_per_hour > 0.1:
                trend = "increasing"
            elif rate_per_hour < -0.1:
                trend = "decreasing"
            else:
                trend = "stable"
            
            return {
                "rate_per_hour": round(rate_per_hour, 2),
                "trend": trend,
                "time_diff_hours": round(time_diff_hours, 2)
            }
            
        except Exception as e:
            logger.warning("Accumulation rate calculation failed", error=str(e))
            return {"rate_per_hour": 0.0, "trend": "error"}
    
    def _generate_predictions(self, snow_analysis: Dict, weather_data: Dict) -> Dict:
        """Generate snow/ice predictions based on current conditions."""
        try:
            temperature = weather_data.get("temperature", 32)
            precipitation_rate = weather_data.get("precipitation_rate", 0.0)
            current_depth = snow_analysis["snow_depth_inches"]
            
            predictions = {
                "1_hour": {"snow_depth": current_depth, "ice_risk": "low"},
                "3_hour": {"snow_depth": current_depth, "ice_risk": "low"},
                "5_hour": {"snow_depth": current_depth, "ice_risk": "low"}
            }
            
            # Simple prediction logic (would be more sophisticated in production)
            if temperature < 32 and precipitation_rate > 0:
                # Snow conditions
                for period in ["1_hour", "3_hour", "5_hour"]:
                    hours = int(period.split("_")[0])
                    predicted_depth = current_depth + (precipitation_rate * hours * 0.1)
                    predictions[period]["snow_depth"] = round(predicted_depth, 1)
            
            if temperature < 28:
                # Ice risk
                for period in predictions:
                    predictions[period]["ice_risk"] = "high"
            elif temperature < 32:
                predictions["3_hour"]["ice_risk"] = "medium"
                predictions["5_hour"]["ice_risk"] = "medium"
            
            return predictions
            
        except Exception as e:
            logger.warning("Prediction generation failed", error=str(e))
            return {"1_hour": {"snow_depth": 0, "ice_risk": "unknown"}}
    
    def _determine_road_status(self, snow_analysis: Dict, weather_data: Dict) -> str:
        """Determine road status based on snow and weather conditions."""
        snow_coverage = snow_analysis["snow_coverage"]
        snow_depth = snow_analysis["snow_depth_inches"]
        temperature = weather_data.get("temperature", 32)
        
        if snow_coverage > 0.8 and snow_depth > 2.0:
            return "⚠️ Hazardous"
        elif snow_coverage > 0.5 and snow_depth > 1.0:
            return "⚠️ Slippery"
        elif snow_coverage > 0.2:
            return "⚠️ Wet"
        elif temperature < 32:
            return "⚠️ Cold"
        else:
            return "✅ Clear"
    
    def _store_historical_data(self, analysis_result: Dict):
        """Store analysis result in historical data."""
        self.historical_data.append(analysis_result)
        
        # Keep only recent data
        if len(self.historical_data) > self.max_history:
            self.historical_data = self.historical_data[-self.max_history:]
        
        # Save to file periodically
        if len(self.historical_data) % 10 == 0:
            self._save_historical_data()
    
    def _save_historical_data(self):
        """Save historical data to file."""
        try:
            data_file = self.analytics_dir / "historical_data.json"
            with open(data_file, 'w') as f:
                json.dump(self.historical_data, f, indent=2)
        except Exception as e:
            logger.warning("Failed to save historical data", error=str(e))
    
    def get_analytics_summary(self) -> Dict:
        """Get summary of current analytics data."""
        if not self.historical_data:
            return {"status": "no_data", "message": "No analytics data available"}
        
        latest = self.historical_data[-1]
        
        return {
            "status": "active",
            "latest_analysis": latest,
            "data_points": len(self.historical_data),
            "last_updated": latest["timestamp"]
        }
