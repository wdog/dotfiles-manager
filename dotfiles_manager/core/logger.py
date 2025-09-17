"""
Logger
Handles error logging for the dotfiles manager application.
"""

import os
import datetime
import traceback
from typing import Optional
from ..common import Config

class Logger:
    """Simple logger for error tracking"""

    def __init__(self, config: Config):
        self.config = config
        self.log_file = os.path.expanduser("~/.local/share/dotfiles-manager/error.log")

        # Create log directory if it doesn't exist
        if self.config.enable_logging:
            log_dir = os.path.dirname(self.log_file)
            os.makedirs(log_dir, exist_ok=True)

    def log_error(self, error: Exception, context: str = ""):
        """Log an error with timestamp and context"""
        if not self.config.enable_logging:
            return

        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"TIMESTAMP: {timestamp}\n")
                f.write(f"CONTEXT: {context}\n")
                f.write(f"ERROR: {str(error)}\n")
                f.write(f"TYPE: {type(error).__name__}\n")
                f.write("TRACEBACK:\n")
                f.write(traceback.format_exc())
                f.write(f"{'='*60}\n")

        except Exception:
            # If logging fails, don't crash the app
            pass

    def log_info(self, message: str, context: str = ""):
        """Log informational message"""
        if not self.config.enable_logging:
            return

        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"\n[{timestamp}] INFO ({context}): {message}\n")

        except Exception:
            # If logging fails, don't crash the app
            pass

    def get_log_path(self) -> str:
        """Get the path to the log file"""
        return self.log_file

    def clear_log(self) -> bool:
        """Clear the log file"""
        if not self.config.enable_logging:
            return False

        try:
            with open(self.log_file, "w", encoding="utf-8") as f:
                f.write(f"# Dotfiles Manager Log - Cleared {datetime.datetime.now()}\n")
            return True
        except Exception:
            return False

    def get_log_size(self) -> int:
        """Get log file size in bytes"""
        try:
            if os.path.exists(self.log_file):
                return os.path.getsize(self.log_file)
            return 0
        except Exception:
            return 0