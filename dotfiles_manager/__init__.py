"""
Dotfiles Manager - Modular Architecture
A clean, extensible dotfiles management application with separated concerns.
"""

__version__ = "2.0.0"
__author__ = "Dotfiles Manager"

from .core.config_manager import ConfigManager
from .core.git_manager import GitManager
from .core.file_manager import FileManager
from .interfaces.ui_interface import UIInterface
from .ui.rich_ui import RichUI

__all__ = [
    'ConfigManager',
    'GitManager',
    'FileManager',
    'UIInterface',
    'RichUI'
]