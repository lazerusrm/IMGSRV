"""
Configuration management for Image Sequence Server.

Handles environment variables, security settings, and application configuration.
"""

import os
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings with security defaults."""
    
    # Server configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8080, description="Server port")
    workers: int = Field(default=1, description="Number of worker processes")
    
    # Security settings
    secret_key: str = Field(default_factory=lambda: os.urandom(32).hex())
    allowed_hosts: List[str] = Field(default=["*"])
    cors_origins: List[str] = Field(default=["*"])
    rate_limit_per_minute: int = Field(default=60)
    
    # Camera configuration (RTSP)
    camera_ip: str = Field(default="192.168.1.110")
    camera_username: str = Field(default="admin")
    camera_password: str = Field(default="123456")
    camera_port: int = Field(default=554)  # RTSP port
    camera_rtsp_path: str = Field(default="/cam/realmonitor?channel=1&subtype=0")
    camera_resolution: str = Field(default="1920x1080")
    
    # Image processing settings
    image_width: int = Field(default=1920)
    image_height: int = Field(default=1080)
    image_quality: int = Field(default=85)
    sequence_duration_minutes: int = Field(default=5)
    sequence_update_interval_minutes: int = Field(default=5)
    max_images_per_sequence: int = Field(default=60)
    
    # Storage settings
    data_dir: Path = Field(default=Path("/var/lib/imgserv"))
    images_dir: Path = Field(default=Path("/var/lib/imgserv/images"))
    sequences_dir: Path = Field(default=Path("/var/lib/imgserv/sequences"))
    max_storage_mb: int = Field(default=1024)  # 1GB max storage
    
    # Logging
    log_level: str = Field(default="INFO")
    log_file: Optional[Path] = Field(default=Path("/var/log/imgserv/app.log"))
    
    # Performance settings
    max_concurrent_captures: int = Field(default=3)
    image_cache_ttl_seconds: int = Field(default=300)
    
    @field_validator("data_dir", "images_dir", "sequences_dir", "log_file")
    @classmethod
    def create_directories(cls, v):
        """Ensure directories exist."""
        if v and isinstance(v, Path):
            v.parent.mkdir(parents=True, exist_ok=True)
        return v
    
    @field_validator("camera_password")
    @classmethod
    def validate_password(cls, v):
        """Ensure password is not default in production."""
        if v == "123456" and os.getenv("ENVIRONMENT") == "production":
            raise ValueError("Default password not allowed in production")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
