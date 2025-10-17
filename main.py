#!/usr/bin/env python3
"""
Image Sequence Server - Production Ready IP Camera Image Sequence Generator

A secure, efficient service for capturing IP camera snapshots and generating
traffic camera-style image sequences for web display.

Features:
- ONVIF camera integration with authentication
- Traffic camera-style image sequences with timestamps
- Secure web server with auto-refresh
- Resource-optimized for Proxmox LXC containers
- Comprehensive security hardening
- Production-ready deployment scripts

Author: AI Assistant
License: MIT
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.app import create_app
from src.config import Settings
from src.utils.logging import setup_logging

logger = logging.getLogger(__name__)

def main():
    """Main application entry point."""
    try:
        # Load configuration
        settings = Settings()
        
        # Setup logging
        setup_logging(settings.log_level)
        
        logger.info("Starting Image Sequence Server")
        logger.info(f"Configuration: {settings.model_dump()}")
        
        # Create FastAPI app
        app = create_app(settings)
        
        # Run server
        import uvicorn
        uvicorn.run(
            app,
            host=settings.host,
            port=settings.port,
            log_level=settings.log_level.lower(),
            access_log=True,
            server_header=False,
            date_header=False,
        )
        
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
