"""
Security utilities and middleware for Image Sequence Server.

Provides additional security measures and input validation.
"""

import hashlib
import hmac
import logging
import re
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)


class SecurityUtils:
    """Security utility functions."""
    
    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """Validate IP address format."""
        pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        return bool(re.match(pattern, ip))
    
    @staticmethod
    def validate_filename(filename: str) -> bool:
        """Validate filename to prevent path traversal."""
        # Check for path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
        
        # Check for dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*']
        if any(char in filename for char in dangerous_chars):
            return False
        
        # Check length
        if len(filename) > 255:
            return False
        
        return True
    
    @staticmethod
    def sanitize_input(input_str: str, max_length: int = 1000) -> str:
        """Sanitize user input."""
        if not isinstance(input_str, str):
            return ""
        
        # Limit length
        input_str = input_str[:max_length]
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
        for char in dangerous_chars:
            input_str = input_str.replace(char, '')
        
        return input_str.strip()
    
    @staticmethod
    def generate_secure_token(data: str, secret: str) -> str:
        """Generate secure HMAC token."""
        return hmac.new(
            secret.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
    
    @staticmethod
    def verify_token(data: str, token: str, secret: str) -> bool:
        """Verify HMAC token."""
        expected_token = SecurityUtils.generate_secure_token(data, secret)
        return hmac.compare_digest(token, expected_token)


class SecurityHeaders:
    """Security headers middleware."""
    
    @staticmethod
    def get_security_headers() -> dict:
        """Get security headers for responses."""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }


class InputValidator:
    """Input validation utilities."""
    
    @staticmethod
    def validate_camera_config(ip: str, username: str, password: str, port: int) -> tuple[bool, str]:
        """Validate camera configuration."""
        if not SecurityUtils.validate_ip_address(ip):
            return False, "Invalid IP address format"
        
        if not username or len(username) > 50:
            return False, "Invalid username"
        
        if not password or len(password) > 100:
            return False, "Invalid password"
        
        if not isinstance(port, int) or port < 1 or port > 65535:
            return False, "Invalid port number"
        
        return True, "Valid"
    
    @staticmethod
    def validate_image_settings(width: int, height: int, quality: int) -> tuple[bool, str]:
        """Validate image processing settings."""
        if not isinstance(width, int) or width < 100 or width > 4000:
            return False, "Invalid image width"
        
        if not isinstance(height, int) or height < 100 or height > 4000:
            return False, "Invalid image height"
        
        if not isinstance(quality, int) or quality < 10 or quality > 100:
            return False, "Invalid image quality"
        
        return True, "Valid"
