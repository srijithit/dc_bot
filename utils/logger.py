import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Sets up bot logging to both console and a rotating file."""
    # Resolve the path to discord-bot/logs directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(project_root, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'bot.log')

    # Formatting configuration
    log_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # Console Handler (writes to stdout)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.INFO)

    # File Handler (rotating log files, 5MB max each, keep up to 5 backups)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.INFO)

    # Configure root logger to capture all library warnings and details
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear existing handlers to prevent duplicate logs
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Get customized bot logger
    logger = logging.getLogger('discord_bot')
    logger.setLevel(logging.INFO)
    
    logger.info("Logging system initialized. Writing to console and logs/bot.log")
    return logger
