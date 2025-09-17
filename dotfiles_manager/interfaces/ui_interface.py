"""
UI Interface
Abstract interface for user interface implementations.
This allows easy swapping between different UI frameworks (Rich, Textual, Curses, etc.).
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..common import FileInfo, DirectoryItem, GitChange

class UIInterface(ABC):
    """Abstract interface for user interface implementations"""

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the UI system"""
        pass

    @abstractmethod
    def cleanup(self):
        """Clean up UI resources"""
        pass

    @abstractmethod
    def show_error(self, message: str):
        """Display error message"""
        pass

    @abstractmethod
    def show_success(self, message: str):
        """Display success message"""
        pass

    @abstractmethod
    def show_info(self, message: str):
        """Display informational message"""
        pass

    @abstractmethod
    def confirm(self, message: str, default: bool = False) -> bool:
        """Show confirmation dialog"""
        pass

    @abstractmethod
    def get_input(self, prompt: str, default: str = "") -> str:
        """Get text input from user"""
        pass

    # Main menu
    @abstractmethod
    def show_main_menu(self) -> str:
        """Display main menu and return user choice"""
        pass

    # File browser
    @abstractmethod
    def show_file_browser(self, start_directory: str = "~") -> List[str]:
        """Display file browser and return selected files"""
        pass

    @abstractmethod
    def show_directory_contents(self, items: List[DirectoryItem], current_dir: str) -> Optional[str]:
        """Display directory contents and return selected action"""
        pass

    # File listings
    @abstractmethod
    def show_tracked_files(self, files: List[FileInfo]):
        """Display tracked files"""
        pass

    @abstractmethod
    def show_modified_files(self, changes: List[GitChange]) -> Optional[Dict[str, Any]]:
        """Display modified files and return user action"""
        pass

    # Settings
    @abstractmethod
    def show_settings_menu(self) -> str:
        """Display settings menu and return choice"""
        pass

    @abstractmethod
    def edit_settings(self, current_config: Dict[str, str]) -> Optional[Dict[str, str]]:
        """Edit settings and return new configuration or None if cancelled"""
        pass

    # Progress and feedback
    @abstractmethod
    def show_progress(self, message: str, progress: float = -1):
        """Show progress indicator (progress -1 means indeterminate)"""
        pass

    @abstractmethod
    def hide_progress(self):
        """Hide progress indicator"""
        pass

    @abstractmethod
    def initialize_git_repo_detailed(self, config: Dict[str, str]) -> bool:
        """Show detailed git repository initialization interface"""
        pass

    @abstractmethod
    def edit_gitignore(self) -> bool:
        """Show .gitignore editing interface"""
        pass