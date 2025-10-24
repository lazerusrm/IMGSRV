"""
Configuration Management Service for Analytics Settings.

Handles dynamic configuration updates, validation, and persistence
of analytics settings through web interface.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import structlog

from src.config import Settings

logger = structlog.get_logger(__name__)


class ConfigManager:
    """Manages dynamic configuration updates for analytics settings."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.config_file = Path("/etc/imgserv/analytics_config.json")
        self.config_file.parent.mkdir(exist_ok=True)
        
        # Default configuration
        self.default_config = {
            "analytics_enabled": True,
            "analytics_update_interval_minutes": 5,
            "weather_api_enabled": True,
            "weather_latitude": 40.011771,
            "weather_longitude": -111.648000,
            "weather_location_name": "Woodland Hills City, Utah",
            "analytics_overlay_enabled": True,
            "analytics_overlay_style": "minimal",
            "snow_detection_threshold": 0.7,
            "ice_warning_temperature": 32,
            "hazardous_snow_depth": 2.0,
            "sequence_update_interval_minutes": 5,
            "max_images_per_sequence": 10,
            "gif_frame_duration_seconds": 1.0,
            "gif_optimization_level": "balanced",
            "road_roi_points": [],  # List of [x, y] normalized coordinates (0.0-1.0)
            "road_roi_enabled": False,  # Whether to use custom ROI
            "last_updated": None
        }
        
        # Load current configuration
        self.current_config = self._load_config()
        
        logger.info("Configuration manager initialized", 
                   config_file=str(self.config_file))
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    logger.info("Configuration loaded from file")
                    return config
            else:
                logger.info("Using default configuration")
                return self.default_config.copy()
        except Exception as e:
            logger.warning("Failed to load configuration", error=str(e))
            return self.default_config.copy()
    
    def _save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to file."""
        try:
            config["last_updated"] = datetime.now().isoformat()
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info("Configuration saved", config_file=str(self.config_file))
            return True
        except Exception as e:
            logger.error("Failed to save configuration", error=str(e))
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return self.current_config.copy()
    
    def update_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update configuration with validation.
        
        Args:
            updates: Dictionary of configuration updates
            
        Returns:
            Updated configuration or error information
        """
        try:
            # Validate updates
            validated_updates = self._validate_updates(updates)
            
            if "error" in validated_updates:
                return validated_updates
            
            # Apply updates
            self.current_config.update(validated_updates)
            
            # Save to file
            if self._save_config(self.current_config):
                logger.info("Configuration updated successfully", updates=validated_updates)
                return {
                    "status": "success",
                    "message": "Configuration updated successfully",
                    "config": self.current_config
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to save configuration"
                }
                
        except Exception as e:
            logger.error("Configuration update failed", error=str(e))
            return {
                "status": "error",
                "message": f"Update failed: {str(e)}"
            }
    
    def _validate_updates(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration updates."""
        validated = {}
        errors = []
        
        # Define validation rules
        validations = {
            "analytics_enabled": lambda x: isinstance(x, bool),
            "analytics_update_interval_minutes": lambda x: isinstance(x, int) and 1 <= x <= 60,
            "weather_api_enabled": lambda x: isinstance(x, bool),
            "weather_latitude": lambda x: isinstance(x, (int, float)) and -90 <= x <= 90,
            "weather_longitude": lambda x: isinstance(x, (int, float)) and -180 <= x <= 180,
            "weather_location_name": lambda x: isinstance(x, str) and len(x.strip()) > 0,
            "analytics_overlay_enabled": lambda x: isinstance(x, bool),
            "analytics_overlay_style": lambda x: x in ["full", "minimal", "mobile", "none"],
            "snow_detection_threshold": lambda x: isinstance(x, (int, float)) and 0 <= x <= 1,
            "ice_warning_temperature": lambda x: isinstance(x, (int, float)) and -50 <= x <= 100,
            "hazardous_snow_depth": lambda x: isinstance(x, (int, float)) and 0 <= x <= 50,
            "sequence_update_interval_minutes": lambda x: isinstance(x, int) and 1 <= x <= 60,
            "max_images_per_sequence": lambda x: isinstance(x, int) and 1 <= x <= 30,
            "gif_frame_duration_seconds": lambda x: isinstance(x, (int, float)) and 0.1 <= x <= 5.0,
            "gif_optimization_level": lambda x: x in ["low", "balanced", "aggressive"],
            "road_roi_points": lambda x: isinstance(x, list) and all(
                isinstance(p, list) and len(p) == 2 and 
                all(isinstance(c, (int, float)) and 0 <= c <= 1 for c in p) 
                for p in x
            ),
            "road_roi_enabled": lambda x: isinstance(x, bool)
        }
        
        for key, value in updates.items():
            if key in validations:
                if validations[key](value):
                    validated[key] = value
                else:
                    errors.append(f"Invalid value for {key}: {value}")
            else:
                errors.append(f"Unknown configuration key: {key}")
        
        if errors:
            return {
                "status": "error",
                "message": "Validation failed",
                "errors": errors
            }
        
        return validated
    
    def reset_to_defaults(self) -> Dict[str, Any]:
        """Reset configuration to defaults."""
        try:
            self.current_config = self.default_config.copy()
            
            if self._save_config(self.current_config):
                logger.info("Configuration reset to defaults")
                return {
                    "status": "success",
                    "message": "Configuration reset to defaults",
                    "config": self.current_config
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to save default configuration"
                }
                
        except Exception as e:
            logger.error("Configuration reset failed", error=str(e))
            return {
                "status": "error",
                "message": f"Reset failed: {str(e)}"
            }
    
    def get_location_info(self) -> Dict[str, Any]:
        """Get current location information."""
        return {
            "latitude": self.current_config.get("weather_latitude", 40.0),
            "longitude": self.current_config.get("weather_longitude", -111.8),
            "location_name": self.current_config.get("weather_location_name", "Woodland Hills, Utah"),
            "coordinates": f"{self.current_config.get('weather_latitude', 40.0)}, {self.current_config.get('weather_longitude', -111.8)}"
        }
    
    def update_location(self, latitude: float, longitude: float, location_name: str) -> Dict[str, Any]:
        """Update location settings."""
        updates = {
            "weather_latitude": latitude,
            "weather_longitude": longitude,
            "weather_location_name": location_name
        }
        
        return self.update_config(updates)
    
    def get_capture_interval(self) -> float:
        """
        Calculate dynamic capture interval based on update interval and max images.
        
        Returns:
            Capture interval in seconds
        """
        update_interval = self.current_config.get("sequence_update_interval_minutes", 5)
        max_images = self.current_config.get("max_images_per_sequence", 10)
        
        # Formula: capture_interval = (update_interval_minutes * 60) / max_images
        capture_interval = (update_interval * 60) / max_images
        
        return round(capture_interval, 1)
