import logging
import sys
from typing import Any

import structlog

from app.config import get_settings

def configure_logging() -> None:
    """
    Set up structlog with environment-appropriate rendering.
    - development: colored console output with key-value pairs
    - production: JSON output for log aggregation (Datadog, Loki, etc.)
    """
    settings = get_settings()
    is_dev = settings.app_env == "development"
    
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]
    
    processors: list[Any]
    if is_dev:
        processors = [
            *shared_processors, 
            structlog.dev.ConsoleRenderer(colors=True)
            ]
    else:
        processors = [
            *shared_processors,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(sys.stdout),
        cache_logger_on_first_use=True
    )