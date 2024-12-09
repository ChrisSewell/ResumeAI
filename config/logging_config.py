import logging
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

def setup_logging(log_dir: str = "logs") -> logging.Logger:
    """Configure logging with both file and console handlers."""
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Remove any existing handlers
    logger.handlers.clear()
    
    # File handler (detailed logging)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-12s | %(funcName)-22s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    log_file = log_path / "resume_generation.log"
    file_handler = logging.FileHandler(
        filename=log_file,
        mode='w',
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Rich console handler (minimal user output)
    console = Console(theme=Theme({
        "info": "cyan",
        "warning": "yellow",
        "error": "red bold",
        "success": "green bold"
    }))
    
    console_handler = RichHandler(
        console=console,
        show_time=False,
        show_path=False,
        show_level=False,  # Hide log levels in console
        markup=True,
        rich_tracebacks=True
    )
    console_handler.setLevel(logging.WARNING)  # Only show warnings and errors
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger 