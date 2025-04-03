import logging
import os
from datetime import datetime
import pytz

def setup_logger(name: str):
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Configure logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Create formatter with IST timezone
    ist = pytz.timezone('Asia/Kolkata')
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S %Z'
    )
    formatter.converter = lambda *args: datetime.now(ist).timetuple()

    # File handler - create new log file for each run
    timestamp = datetime.now(ist).strftime('%Y%m%d_%H%M%S')
    file_handler = logging.FileHandler(f'logs/sre_bot_{timestamp}.log')
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger 