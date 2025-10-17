"""
Logging configuration for Image Sequence Server.

Provides structured logging with security considerations.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

import structlog


def setup_logging(log_level: str = "INFO", log_file: Optional[Path] = None):
    """Configure structured logging with security best practices."""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=getattr(logging, log_level.upper()),
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.handlers.RotatingFileHandler(
                log_file, maxBytes=10*1024*1024, backupCount=5
            ) if log_file else logging.NullHandler()
        ]
    )
    
    # Security: Don't log sensitive information
    logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
    logging.getLogger("onvif").setLevel(logging.WARNING)
    
    # Get logger
    logger = structlog.get_logger()
    logger.info("Logging configured", level=log_level, file=str(log_file) if log_file else None)
    
    return logger
