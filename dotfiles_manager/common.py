"""
Common constants, types and utilities
"""

import os
import sys
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass

# Color constants - Lime theme
LIME_PRIMARY = "#32CD32"    # Main lime green
LIME_SECONDARY = "#9AFF9A"  # Light lime green
LIME_ACCENT = "#00FF00"     # Bright green accent
LIME_DARK = "#228B22"       # Dark forest green

# Material Design color palette - harmonized
MAT_PRIMARY = "#4CAF50"       # Material Green 500
MAT_PRIMARY_LIGHT = "#81C784" # Material Green 300
MAT_PRIMARY_DARK = "#388E3C"  # Material Green 700
MAT_ACCENT = "#00BCD4"        # Material Cyan 500
MAT_ACCENT_LIGHT = "#4DD0E1"  # Material Cyan 300

# Material text colors
MAT_TEXT_PRIMARY = "#212121"   # Material Grey 900
MAT_TEXT_SECONDARY = "#757575" # Material Grey 600
MAT_TEXT_HINT = "#BDBDBD"     # Material Grey 400

# File browser material colors
MAT_DIR_NORMAL = "#2196F3"     # Blue - directories
MAT_DIR_HIDDEN = "#81D4FA"     # Light Blue - hidden directories
MAT_FILE_NORMAL = "#BDBDBD"    # Light Gray - files
MAT_FILE_HIDDEN = "#9E9E9E"    # Gray - hidden files

# Sort mode colors
MAT_SORT_BLUE = "#2196F3"      # Material Blue 500
MAT_SORT_ORANGE = "#FF9800"    # Material Orange 500
MAT_SORT_GREEN = "#4CAF50"     # Material Green 500

# Banana selection color
MAT_BANANA = "#FFD700"         # Gold color for banana/selected items

# Platform detection
UNIX_PLATFORM = sys.platform != 'win32'

# Keyboard constants
class KeyCodes:
    """Centralized key code constants"""
    ESC = '\x1b'
    ENTER = '\r'
    CTRL_C = '\x03'
    BACKSPACE = '\x7f'
    BACKSPACE_ALT = '\x08'

    # Arrow keys (ANSI escape sequences)
    ARROW_UP = '\x1b[A'
    ARROW_DOWN = '\x1b[B'
    ARROW_RIGHT = '\x1b[C'
    ARROW_LEFT = '\x1b[D'

    # Function keys
    F1 = '\x1bOP'
    F2 = '\x1bOQ'
    F3 = '\x1bOR'
    F4 = '\x1bOS'

    # Page navigation keys
    PAGE_UP = '\x1b[5~'
    PAGE_DOWN = '\x1b[6~'

    # Delete key
    DELETE = '\x1b[3~'

# Data structures
@dataclass
class Config:
    """Configuration data structure"""
    git_dir: str = "~/.dotfiles.git"
    work_tree: str = "~"
    remote: str = ""
    enable_logging: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'git_dir': self.git_dir,
            'work_tree': self.work_tree,
            'remote': self.remote,
            'enable_logging': self.enable_logging
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        return cls(**data)

@dataclass
class FileInfo:
    """Information about a tracked file"""
    path: str
    status: str
    size: int
    mtime: float
    is_dir: bool = False

    @property
    def display_name(self) -> str:
        """Display name for UI"""
        return os.path.basename(self.path) if self.path != '.' else '.'

@dataclass
class DirectoryItem:
    """Information about a directory item"""
    path: str
    full_path: str
    type: str  # 'file', 'directory', 'parent'
    size: int = 0
    mtime: float = 0

@dataclass
class GitChange:
    """Information about a git change"""
    file: str
    staged: str
    worktree: str
    status_code: str

# Utility functions
def expand_path(path: str) -> str:
    """Expand user path with proper handling"""
    return os.path.expanduser(path)

def format_file_size(size_bytes: int) -> str:
    """Convert file size to human readable string"""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = int(abs(size_bytes).bit_length() - 1) // 10
    i = min(i, len(size_names) - 1)

    size = size_bytes / (1024 ** i)
    return f"{size:.1f} {size_names[i]}"

def format_file_mtime(mtime: float) -> str:
    """Convert modification time to human readable string"""
    try:
        import datetime
        dt = datetime.datetime.fromtimestamp(mtime)
        now = datetime.datetime.now()

        # If today, show time only
        if dt.date() == now.date():
            return dt.strftime("%H:%M")

        # If this year, show month and day
        if dt.year == now.year:
            return dt.strftime("%b %d")

        # Otherwise show year
        return dt.strftime("%Y")

    except (ValueError, OSError):
        return "Unknown"