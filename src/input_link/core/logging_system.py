"""Comprehensive logging system for Input Link."""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, Union
from enum import Enum

from ..models import ConfigModel


class LogLevel(Enum):
    """Log levels with proper ordering."""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class InputLinkLogger:
    """Centralized logging system for Input Link applications."""
    
    def __init__(
        self,
        name: str,
        config: Optional[ConfigModel] = None,
        log_callback: Optional[Callable[[str, str], None]] = None,
        log_file: Optional[Path] = None,
        level: Union[str, LogLevel] = LogLevel.INFO,
    ):
        """Initialize the logger.
        
        Args:
            name: Logger name (typically module name)
            config: Application configuration
            log_callback: Optional callback for GUI integration
            log_file: Optional file path for log output
            level: Logging level
        """
        self.name = name
        self.config = config
        self.log_callback = log_callback
        self.log_file = log_file
        
        # Set up Python logging
        self.logger = logging.getLogger(name)
        self._setup_logger(level)
        
    def _setup_logger(self, level: Union[str, LogLevel]):
        """Setup the Python logger with appropriate handlers."""
        # Convert level to logging level
        if isinstance(level, LogLevel):
            log_level = level.value
        elif isinstance(level, str):
            log_level = getattr(logging, level.upper(), logging.INFO)
        else:
            log_level = logging.INFO
            
        self.logger.setLevel(log_level)
        
        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
            
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (if specified)
        if self.log_file:
            try:
                self.log_file.parent.mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(self.log_file)
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                file_handler.setFormatter(file_formatter)
                self.logger.addHandler(file_handler)
            except Exception as e:
                self.logger.warning(f"Could not create log file {self.log_file}: {e}")
                
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log(LogLevel.DEBUG, message, **kwargs)
        
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log(LogLevel.INFO, message, **kwargs)
        
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log(LogLevel.WARNING, message, **kwargs)
        
    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log(LogLevel.ERROR, message, **kwargs)
        
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._log(LogLevel.CRITICAL, message, **kwargs)
        
    def _log(self, level: LogLevel, message: str, **kwargs):
        """Internal logging method."""
        # Format message with context
        if kwargs:
            try:
                formatted_message = message.format(**kwargs)
            except (KeyError, ValueError):
                formatted_message = f"{message} | Context: {kwargs}"
        else:
            formatted_message = message
            
        # Log to Python logger
        self.logger.log(level.value, formatted_message)
        
        # Call GUI callback if available
        if self.log_callback:
            try:
                self.log_callback(level.name.lower(), formatted_message)
            except Exception as e:
                # Avoid infinite recursion - just print to console
                print(f"Error in log callback: {e}")
                
    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        import traceback
        tb_str = traceback.format_exc()
        full_message = f"{message}\nTraceback:\n{tb_str}"
        self._log(LogLevel.ERROR, full_message, **kwargs)
        
    def set_level(self, level: Union[str, LogLevel]):
        """Change logging level."""
        if isinstance(level, LogLevel):
            log_level = level.value
        elif isinstance(level, str):
            log_level = getattr(logging, level.upper(), logging.INFO)
        else:
            log_level = logging.INFO
            
        self.logger.setLevel(log_level)
        
    def add_context(self, **context):
        """Add context to all subsequent log messages."""
        # Create a new logger with context
        return ContextLogger(self, context)


class ContextLogger:
    """Logger wrapper that automatically adds context to messages."""
    
    def __init__(self, base_logger: InputLinkLogger, context: dict):
        self.base_logger = base_logger
        self.context = context
        
    def debug(self, message: str, **kwargs):
        """Log debug message with context."""
        self.base_logger.debug(message, **{**self.context, **kwargs})
        
    def info(self, message: str, **kwargs):
        """Log info message with context."""
        self.base_logger.info(message, **{**self.context, **kwargs})
        
    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        self.base_logger.warning(message, **{**self.context, **kwargs})
        
    def error(self, message: str, **kwargs):
        """Log error message with context."""
        self.base_logger.error(message, **{**self.context, **kwargs})
        
    def critical(self, message: str, **kwargs):
        """Log critical message with context."""
        self.base_logger.critical(message, **{**self.context, **kwargs})
        
    def exception(self, message: str, **kwargs):
        """Log exception with context."""
        self.base_logger.exception(message, **{**self.context, **kwargs})


def get_logger(
    name: str,
    config: Optional[ConfigModel] = None,
    log_callback: Optional[Callable[[str, str], None]] = None,
    level: Union[str, LogLevel] = LogLevel.INFO,
) -> InputLinkLogger:
    """Get or create a logger instance.
    
    Args:
        name: Logger name
        config: Application configuration
        log_callback: Optional callback for GUI integration
        level: Logging level
        
    Returns:
        InputLinkLogger instance
    """
    # Determine log file path
    log_file = None
    if config:
        log_dir = Path.home() / ".input-link" / "logs"
        log_file = log_dir / f"{name}.log"
    
    return InputLinkLogger(
        name=name,
        config=config,
        log_callback=log_callback,
        log_file=log_file,
        level=level,
    )


def setup_application_logging(
    app_name: str,
    config: Optional[ConfigModel] = None,
    verbose: bool = False,
    log_callback: Optional[Callable[[str, str], None]] = None,
) -> InputLinkLogger:
    """Setup logging for an entire application.
    
    Args:
        app_name: Application name (sender, receiver, gui)
        config: Application configuration
        verbose: Enable verbose (DEBUG) logging
        log_callback: Optional callback for GUI integration
        
    Returns:
        Main application logger
    """
    level = LogLevel.DEBUG if verbose else LogLevel.INFO
    
    # Create main application logger
    main_logger = get_logger(
        name=app_name,
        config=config,
        log_callback=log_callback,
        level=level,
    )
    
    # Log startup information
    main_logger.info(f"Starting {app_name} application")
    main_logger.info(f"Logging level: {level.name}")
    
    if config:
        main_logger.debug("Configuration loaded successfully")
    
    return main_logger