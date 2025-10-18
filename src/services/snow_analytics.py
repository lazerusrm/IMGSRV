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
        """Get current weather data from NOAA API with snow depth and accumulation."""
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
                            "snow_depth_inches": 0.0,
                            "snow_accumulation_1hr": 0.0,
                            "snow_accumulation_3hr": 0.0,
                            "snow_accumulation_6hr": 0.0,
                            "humidity": 45,
                            "conditions": "Clear",
                            "wind_speed": 0,
                            "wind_direction": "N",
                            "timestamp": now.isoformat(),
                            "source": "NOAA"
                        }
                        
                        # Try to extract real weather data from NOAA response
                        try:
                            # Get forecast data
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
                                                "wind_speed": current_period.get("windSpeed", "0 mph").split()[0],
                                                "wind_direction": current_period.get("windDirection", "N")
                                            })
                            
                            # Get observation station data for current conditions
                            if "properties" in data and "observationStations" in data["properties"]:
                                stations_url = data["properties"]["observationStations"]
                                async with session.get(stations_url) as stations_response:
                                    if stations_response.status == 200:
                                        stations_data = await stations_response.json()
                                        if "features" in stations_data and len(stations_data["features"]) > 0:
                                            # Get the closest station
                                            station_id = stations_data["features"][0]["properties"]["stationIdentifier"]
                                            obs_url = f"https://api.weather.gov/stations/{station_id}/observations/latest"
                                            
                                            async with session.get(obs_url) as obs_response:
                                                if obs_response.status == 200:
                                                    obs_data = await obs_response.json()
                                                    if "properties" in obs_data:
                                                        props = obs_data["properties"]
                                                        
                                                        # Extract temperature (in Celsius, convert to Fahrenheit)
                                                        if props.get("temperature", {}).get("value"):
                                                            temp_c = props["temperature"]["value"]
                                                            weather_data["temperature"] = round((temp_c * 9/5) + 32, 1)
                                                        
                                                        # Extract humidity
                                                        if props.get("relativeHumidity", {}).get("value"):
                                                            weather_data["humidity"] = round(props["relativeHumidity"]["value"], 0)
                                                        
                                                        # Extract snow depth (in meters, convert to inches)
                                                        if props.get("snowDepth", {}).get("value"):
                                                            depth_m = props["snowDepth"]["value"]
                                                            weather_data["snow_depth_inches"] = round(depth_m * 39.3701, 1)
                                                        
                                                        # Extract precipitation
                                                        if props.get("precipitationLastHour", {}).get("value"):
                                                            precip_mm = props["precipitationLastHour"]["value"]
                                                            weather_data["precipitation_rate"] = round(precip_mm * 0.0393701, 2)
                                                        
                                                        # Extract wind speed (m/s to mph)
                                                        if props.get("windSpeed", {}).get("value"):
                                                            wind_ms = props["windSpeed"]["value"]
                                                            weather_data["wind_speed"] = round(wind_ms * 2.23694, 1)
                                                        
                                                        # Extract wind direction
                                                        if props.get("windDirection", {}).get("value"):
                                                            weather_data["wind_direction"] = self._degrees_to_cardinal(
                                                                props["windDirection"]["value"]
                                                            )
                                                        
                                                        # Extract conditions
                                                        if props.get("textDescription"):
                                                            weather_data["conditions"] = props["textDescription"]
                        
                        except Exception as e:
                            logger.debug("Could not parse detailed weather data", error=str(e))
                        
                        # Estimate snow accumulation based on precipitation and temperature
                        if weather_data["temperature"] <= 32 and weather_data["precipitation_rate"] > 0:
                            # Rough estimation: 1 inch of rain = ~10 inches of snow
                            weather_data["snow_accumulation_1hr"] = round(weather_data["precipitation_rate"] * 10, 1)
                            weather_data["snow_accumulation_3hr"] = round(weather_data["snow_accumulation_1hr"] * 3, 1)
                            weather_data["snow_accumulation_6hr"] = round(weather_data["snow_accumulation_1hr"] * 6, 1)
                        
                        # Cache the result
                        self._cache[cache_key] = (weather_data, now)
                        return weather_data
                    else:
                        logger.warning("Weather API request failed", status=response.status)
                        return self._get_fallback_weather()
        
        except Exception as e:
            logger.warning("Weather data fetch failed", error=str(e))
            return self._get_fallback_weather()
    
    def _degrees_to_cardinal(self, degrees: float) -> str:
        """Convert degrees to cardinal direction."""
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                     "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        index = round(degrees / 22.5) % 16
        return directions[index]
    
    def _get_fallback_weather(self) -> Dict:
        """Return fallback weather data when API fails."""
        return {
            "temperature": 45,  # More realistic for Utah
            "precipitation_rate": 0.0,
            "snow_depth_inches": 0.0,
            "snow_accumulation_1hr": 0.0,
            "snow_accumulation_3hr": 0.0,
            "snow_accumulation_6hr": 0.0,
            "humidity": 45,
            "conditions": "Clear",
            "wind_speed": 0,
            "wind_direction": "N",
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


class RoadSurfaceAnalyzer:
    """Analyzes road surface conditions using computer vision."""
    
    def __init__(self):
        self.snow_threshold = 0.7  # Threshold for snow detection
        self.baseline_image = None
        self.baseline_timestamp = None
    
    def analyze_road_surface(self, image: np.ndarray, road_mask: np.ndarray) -> Dict:
        """
        Analyze road surface conditions (coverage, wetness, ice risk).
        
        Args:
            image: Input image as numpy array
            road_mask: Binary mask of road area
            
        Returns:
            Dictionary with road surface analysis results
        """
        try:
            # Convert to HSV for better color analysis
            hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
            
            # Apply road mask
            masked_hsv = cv2.bitwise_and(hsv, hsv, mask=road_mask)
            masked_rgb = cv2.bitwise_and(image, image, mask=road_mask)
            
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
            
            # Analyze wetness (darker, more saturated road surface)
            lower_wet = np.array([0, 20, 40])
            upper_wet = np.array([180, 100, 150])
            wet_mask = cv2.inRange(masked_hsv, lower_wet, upper_wet)
            wet_pixels = np.sum(wet_mask > 0)
            wet_coverage = wet_pixels / road_pixels if road_pixels > 0 else 0.0
            
            # Analyze ice potential (very bright, low saturation, specific reflectivity)
            lower_ice = np.array([0, 0, 180])
            upper_ice = np.array([180, 15, 220])
            ice_mask = cv2.inRange(masked_hsv, lower_ice, upper_ice)
            ice_pixels = np.sum(ice_mask > 0)
            ice_coverage = ice_pixels / road_pixels if road_pixels > 0 else 0.0
            
            # Analyze overall road brightness (cleanliness indicator)
            gray = cv2.cvtColor(masked_rgb, cv2.COLOR_RGB2GRAY)
            road_brightness = np.mean(gray[road_mask > 0]) if np.any(road_mask) else 0
            
            return {
                "snow_coverage": round(snow_coverage, 3),
                "wet_coverage": round(wet_coverage, 3),
                "ice_coverage": round(ice_coverage, 3),
                "road_brightness": round(road_brightness, 1),
                "road_pixels": int(road_pixels),
                "snow_pixels": int(snow_pixels),
                "wet_pixels": int(wet_pixels),
                "ice_pixels": int(ice_pixels),
                "surface_condition": self._classify_surface_condition(
                    snow_coverage, wet_coverage, ice_coverage, road_brightness
                ),
                "confidence": min(max(snow_coverage, wet_coverage, ice_coverage) * 2, 1.0)
            }
            
        except Exception as e:
            logger.error("Road surface analysis failed", error=str(e))
            return {
                "snow_coverage": 0.0,
                "wet_coverage": 0.0,
                "ice_coverage": 0.0,
                "road_brightness": 0.0,
                "road_pixels": 0,
                "snow_pixels": 0,
                "wet_pixels": 0,
                "ice_pixels": 0,
                "surface_condition": "unknown",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _classify_surface_condition(self, snow: float, wet: float, ice: float, brightness: float) -> str:
        """Classify road surface condition based on coverage analysis."""
        if snow > 0.7:
            return "snow_covered"
        elif snow > 0.4:
            return "partial_snow"
        elif ice > 0.3:
            return "icy"
        elif wet > 0.5:
            return "wet"
        elif wet > 0.2:
            return "damp"
        elif brightness > 150:
            return "clean_dry"
        else:
            return "dry"


class SnowAnalytics:
    """Main snow analytics service."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.weather_client = WeatherDataClient(settings)
        self.road_detector = RoadDetector()
        self.road_analyzer = RoadSurfaceAnalyzer()
        
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
            
            # Analyze road surface conditions (from camera image)
            road_analysis = self.road_analyzer.analyze_road_surface(image_rgb, road_mask)
            
            # Get weather data (includes real snow depth and temperature)
            weather_data = await self.weather_client.get_current_weather(
                lat=self.settings.weather_latitude,
                lon=self.settings.weather_longitude
            )
            
            # Calculate accumulation rate from weather data
            accumulation_rate = self._calculate_accumulation_rate(weather_data)
            
            # Generate predictions
            predictions = self._generate_predictions(weather_data)
            
            # Compile results
            analysis_result = {
                "timestamp": timestamp.isoformat(),
                "image_path": str(image_path),
                "road_analysis": road_analysis,  # Camera-based road surface analysis
                "weather_data": weather_data,     # Real weather data (temp, snow depth, etc.)
                "snow_analysis": {                # Combined data for backward compatibility
                    "snow_coverage": road_analysis["snow_coverage"],
                    "snow_depth_inches": weather_data["snow_depth_inches"],  # From weather API
                    "surface_condition": road_analysis["surface_condition"],
                    "confidence": road_analysis["confidence"]
                },
                "accumulation_rate": accumulation_rate,
                "predictions": predictions,
                "road_status": self._determine_road_status(road_analysis, weather_data)
            }
            
            # Store historical data
            self._store_historical_data(analysis_result)
            
            logger.info("Image analysis completed", 
                       surface_condition=road_analysis["surface_condition"],
                       snow_depth=weather_data["snow_depth_inches"],
                       temperature=weather_data["temperature"])
            
            return analysis_result
            
        except Exception as e:
            logger.error("Image analysis failed", error=str(e), image_path=str(image_path))
            raise SnowAnalyticsError(f"Analysis failed: {e}")
    
    def _calculate_accumulation_rate(self, weather_data: Dict) -> Dict:
        """Calculate snow accumulation rate based on weather data and historical measurements."""
        # Use weather API data for accumulation if available
        if "snow_accumulation_1hr" in weather_data:
            rate_per_hour = weather_data["snow_accumulation_1hr"]
            
            # Determine trend based on rate
            if rate_per_hour > 0.1:
                trend = "increasing"
            elif rate_per_hour < -0.1:
                trend = "decreasing"
            else:
                trend = "stable"
            
            return {
                "rate_per_hour": round(rate_per_hour, 2),
                "trend": trend,
                "accumulation_1hr": weather_data.get("snow_accumulation_1hr", 0.0),
                "accumulation_3hr": weather_data.get("snow_accumulation_3hr", 0.0),
                "accumulation_6hr": weather_data.get("snow_accumulation_6hr", 0.0),
                "source": "weather_api"
            }
        
        # Fallback to historical data comparison if weather data unavailable
        if len(self.historical_data) < 2:
            return {
                "rate_per_hour": 0.0,
                "trend": "insufficient_data",
                "source": "historical"
            }
        
        try:
            # Get last two measurements
            recent_data = self.historical_data[-2:]
            
            # Calculate time difference
            time1 = datetime.fromisoformat(recent_data[0]["timestamp"])
            time2 = datetime.fromisoformat(recent_data[1]["timestamp"])
            time_diff_hours = (time2 - time1).total_seconds() / 3600
            
            if time_diff_hours <= 0:
                return {"rate_per_hour": 0.0, "trend": "no_change", "source": "historical"}
            
            # Calculate depth difference from weather data
            depth1 = recent_data[0]["weather_data"].get("snow_depth_inches", 0.0)
            depth2 = recent_data[1]["weather_data"].get("snow_depth_inches", 0.0)
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
                "time_diff_hours": round(time_diff_hours, 2),
                "source": "historical"
            }
            
        except Exception as e:
            logger.warning("Accumulation rate calculation failed", error=str(e))
            return {"rate_per_hour": 0.0, "trend": "error", "source": "error"}
    
    def _generate_predictions(self, weather_data: Dict) -> Dict:
        """Generate snow/ice predictions based on weather data."""
        try:
            temperature = weather_data.get("temperature", 45)
            precipitation_rate = weather_data.get("precipitation_rate", 0.0)
            current_depth = weather_data.get("snow_depth_inches", 0.0)
            snow_1hr = weather_data.get("snow_accumulation_1hr", 0.0)
            
            predictions = {
                "1_hour": {"snow_depth": current_depth, "ice_risk": "low", "accumulation": snow_1hr},
                "3_hour": {"snow_depth": current_depth, "ice_risk": "low", "accumulation": snow_1hr * 3},
                "6_hour": {"snow_depth": current_depth, "ice_risk": "low", "accumulation": snow_1hr * 6}
            }
            
            # Predict snow depth based on accumulation
            if snow_1hr > 0:
                predictions["1_hour"]["snow_depth"] = round(current_depth + snow_1hr, 1)
                predictions["3_hour"]["snow_depth"] = round(current_depth + (snow_1hr * 3), 1)
                predictions["6_hour"]["snow_depth"] = round(current_depth + (snow_1hr * 6), 1)
            
            # Predict ice risk based on temperature
            if temperature < 28:
                # High ice risk below 28°F
                for period in predictions:
                    predictions[period]["ice_risk"] = "high"
            elif temperature < 32:
                # Medium ice risk at freezing
                predictions["3_hour"]["ice_risk"] = "medium"
                predictions["6_hour"]["ice_risk"] = "medium"
            elif temperature < 35 and current_depth > 0:
                # Low ice risk with existing snow near freezing
                for period in predictions:
                    predictions[period]["ice_risk"] = "medium"
            
            return predictions
            
        except Exception as e:
            logger.warning("Prediction generation failed", error=str(e))
            return {"1_hour": {"snow_depth": 0, "ice_risk": "unknown", "accumulation": 0}}
    
    def _determine_road_status(self, road_analysis: Dict, weather_data: Dict) -> str:
        """Determine road status based on road surface analysis and weather conditions."""
        # Get road surface analysis
        surface_condition = road_analysis.get("surface_condition", "unknown")
        snow_coverage = road_analysis.get("snow_coverage", 0.0)
        ice_coverage = road_analysis.get("ice_coverage", 0.0)
        wet_coverage = road_analysis.get("wet_coverage", 0.0)
        
        # Get weather data
        temperature = weather_data.get("temperature", 45)
        snow_depth = weather_data.get("snow_depth_inches", 0.0)
        
        # Determine status based on combined analysis
        if surface_condition == "snow_covered" or snow_coverage > 0.7:
            if snow_depth > 2.0 or temperature < 28:
                return "Hazardous"  # Removed emoji for cleaner text
            else:
                return "Slippery"
        
        elif surface_condition == "partial_snow" or snow_coverage > 0.3:
            return "Slippery"
        
        elif surface_condition == "icy" or ice_coverage > 0.3:
            return "Icy - Hazardous"
        
        elif ice_coverage > 0.1 and temperature < 32:
            return "Ice Possible"
        
        elif surface_condition == "wet" or wet_coverage > 0.5:
            if temperature < 35:
                return "Wet - Ice Risk"
            else:
                return "Wet"
        
        elif surface_condition == "damp" or wet_coverage > 0.2:
            return "Damp"
        
        elif temperature < 32 and wet_coverage > 0.1:
            return "Freezing Conditions"
        
        elif surface_condition == "clean_dry" or (snow_coverage < 0.1 and wet_coverage < 0.1):
            return "Clear"
        
        else:
            return "Clear"
    
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
