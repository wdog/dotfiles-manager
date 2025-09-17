"""
File Manager
Handles file system operations and directory browsing.
"""

import os
import shutil
import stat
from typing import List, Optional, Tuple

from .config_manager import ConfigManager
from ..common import Config, DirectoryItem, format_file_size, format_file_mtime

class FileManager:
    """Manages file system operations and directory browsing"""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager

    @property
    def config(self) -> Config:
        """Get current configuration"""
        return self.config_manager.config

    def get_directory_contents(self, directory: str) -> List[DirectoryItem]:
        """Get contents of a directory for browsing"""
        items = []
        directory = os.path.expanduser(directory)

        try:
            # Add parent directory entry if not at root
            parent_dir = os.path.dirname(directory)
            if parent_dir != directory:  # Not at filesystem root
                items.append(DirectoryItem(
                    path="..",
                    full_path=parent_dir,
                    type="parent"
                ))

            # Get directory contents
            try:
                entries = os.listdir(directory)
            except PermissionError:
                return items  # Return just parent dir if can't read

            # Sort entries: directories first, then files
            entries.sort(key=lambda x: (not os.path.isdir(os.path.join(directory, x)), x.lower()))

            for entry in entries:
                full_path = os.path.join(directory, entry)

                try:
                    stat_info = os.stat(full_path)
                    is_dir = stat.S_ISDIR(stat_info.st_mode)
                    is_hidden = entry.startswith('.')

                    # Determine item type based on directory status and hidden status
                    if is_dir:
                        item_type = "hidden_directory" if is_hidden else "directory"
                    else:
                        item_type = "hidden_file" if is_hidden else "file"

                    items.append(DirectoryItem(
                        path=entry,
                        full_path=full_path,
                        type=item_type,
                        size=stat_info.st_size if not is_dir else 0,
                        mtime=stat_info.st_mtime
                    ))

                except (OSError, IOError):
                    # Skip files we can't access
                    continue

        except (OSError, IOError):
            # Return empty list if directory is inaccessible
            pass

        return items

    def is_protected_file(self, file_path: str) -> bool:
        """Check if file is protected from operations (like the script itself)"""
        current_script = os.path.abspath(__file__)
        config_file = os.path.abspath(self.config_manager.config_path)
        abs_path = os.path.abspath(file_path)

        protected_files = {current_script, config_file}
        return abs_path in protected_files

    def copy_file_to_dotfiles(self, source_path: str, target_base_dir: str) -> Optional[str]:
        """Copy a file to dotfiles directory, preserving relative structure"""
        home_dir = os.path.expanduser('~')

        # Calculate relative path from home
        if source_path.startswith(home_dir):
            rel_path = os.path.relpath(source_path, home_dir)
        else:
            # For files outside home, use basename
            rel_path = os.path.basename(source_path)

        # Target path in dotfiles directory
        target_path = os.path.join(target_base_dir, rel_path)

        try:
            # Create target directory if needed
            target_dir = os.path.dirname(target_path)
            if target_dir and not os.path.exists(target_dir):
                os.makedirs(target_dir)

            # Copy file
            if os.path.isdir(source_path):
                shutil.copytree(source_path, target_path, dirs_exist_ok=True)
            else:
                shutil.copy2(source_path, target_path)

            return target_path

        except (OSError, IOError):
            return None

    def get_file_size_str(self, size_bytes: int) -> str:
        """Convert file size to human readable string"""
        return format_file_size(size_bytes)

    def get_file_mtime_str(self, mtime: float) -> str:
        """Convert modification time to human readable string"""
        return format_file_mtime(mtime)

    def is_text_file(self, file_path: str) -> bool:
        """Check if file is likely a text file"""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)

            # Check for null bytes (common in binary files)
            if b'\x00' in chunk:
                return False

            # Try to decode as UTF-8
            try:
                chunk.decode('utf-8')
                return True
            except UnicodeDecodeError:
                return False

        except (OSError, IOError):
            return False

    def get_file_icon(self, item: DirectoryItem) -> str:
        """Get appropriate icon for file/directory"""
        if item.type == "parent":
            return "⬅️"
        elif item.type == "directory":
            return "📂"
        else:
            # Determine icon based on file extension
            _, ext = os.path.splitext(item.path.lower())

            icon_map = {
                '.py': '🐍', '.js': '📜', '.ts': '📘', '.json': '📋',
                '.md': '📄', '.txt': '📄', '.yml': '⚙️', '.yaml': '⚙️',
                '.ini': '⚙️', '.conf': '⚙️', '.cfg': '⚙️',
                '.sh': '📜', '.bash': '📜', '.zsh': '📜',
                '.png': '🖼️', '.jpg': '🖼️', '.jpeg': '🖼️', '.gif': '🖼️',
                '.zip': '📦', '.tar': '📦', '.gz': '📦',
            }

            return icon_map.get(ext, '📄')

    def validate_file_path(self, file_path: str) -> Tuple[bool, str]:
        """Validate file path and return (is_valid, error_message)"""
        try:
            expanded_path = os.path.expanduser(file_path)

            if not os.path.exists(expanded_path):
                return False, "Path does not exist"

            if not os.access(expanded_path, os.R_OK):
                return False, "Path is not readable"

            if self.is_protected_file(expanded_path):
                return False, "Path is protected from modification"

            return True, ""

        except Exception as e:
            return False, f"Path validation error: {e}"