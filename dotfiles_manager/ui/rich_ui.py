"""
Rich UI Implementation
User interface implementation using the Rich library.
"""

import os
import sys
import time
from typing import List, Optional, Dict, Any

# Platform-specific imports for keyboard input
try:
    import termios
    import tty
    UNIX_PLATFORM = True
except ImportError:
    import msvcrt
    UNIX_PLATFORM = False

from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.prompt import Prompt

from ..interfaces.ui_interface import UIInterface
from ..common import LIME_PRIMARY, LIME_SECONDARY, LIME_ACCENT, LIME_DARK, KeyCodes
from ..common import MAT_PRIMARY, MAT_PRIMARY_LIGHT, MAT_PRIMARY_DARK, MAT_ACCENT, MAT_ACCENT_LIGHT
from ..common import MAT_TEXT_PRIMARY, MAT_TEXT_SECONDARY, MAT_TEXT_HINT
from ..common import MAT_DIR_NORMAL, MAT_DIR_HIDDEN, MAT_FILE_NORMAL, MAT_FILE_HIDDEN
from ..common import MAT_SORT_BLUE, MAT_SORT_ORANGE, MAT_SORT_GREEN, MAT_BANANA
from ..common import FileInfo, DirectoryItem, GitChange

# Initialize Rich console
console = Console()

def get_key():
    """Cross-platform single key input function with fallback"""
    try:
        if os.name == 'nt':  # Windows
            import msvcrt
            return msvcrt.getch().decode('utf-8')
        else:  # Unix/Linux/MacOS
            # Check if stdin is a terminal
            if not sys.stdin.isatty():
                # For non-interactive environments, try to read piped input
                try:
                    line = sys.stdin.readline().strip()
                    return line[0] if line else KeyCodes.ENTER
                except (EOFError, IndexError):
                    # If no input available, return 'y' as default for automation
                    return 'y'

            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                key = sys.stdin.read(1)

                # Handle ESC sequences - improved approach
                if key == KeyCodes.ESC:  # ESC sequences (arrows, function keys, etc.)
                    try:
                        # Read first part of escape sequence
                        next_char = sys.stdin.read(1)
                        if next_char == '[':
                            # Could be arrow keys or page up/down
                            third_char = sys.stdin.read(1)
                            full_sequence = key + next_char + third_char

                            # Check for arrow keys
                            if full_sequence in [KeyCodes.ARROW_UP, KeyCodes.ARROW_DOWN,
                                               KeyCodes.ARROW_LEFT, KeyCodes.ARROW_RIGHT]:
                                return full_sequence

                            # Check for page up/down (need one more character)
                            if third_char in ['5', '6']:
                                fourth_char = sys.stdin.read(1)
                                full_sequence = key + next_char + third_char + fourth_char
                                if full_sequence in [KeyCodes.PAGE_UP, KeyCodes.PAGE_DOWN]:
                                    return full_sequence

                            # Return whatever sequence we got
                            return full_sequence
                        elif len(next_char) == 0:
                            return KeyCodes.ESC  # Standalone ESC
                        else:
                            return key + next_char
                    except:
                        return KeyCodes.ESC  # Standalone ESC on error

                return key
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except Exception:
        # Ultimate fallback - return 'y' for automation environments
        return 'y'

class RichUI(UIInterface):
    """Rich-based user interface implementation"""

    def __init__(self):
        self.console = console
        self._progress = None

    def initialize(self) -> bool:
        """Initialize the UI system"""
        try:
            # Test console capabilities
            self.console.print("", end="")
            return True
        except Exception:
            return False

    def cleanup(self):
        """Clean up UI resources"""
        if self._progress:
            self.hide_progress()

    def show_error(self, message: str):
        """Display error message"""
        self.console.print(f"[red]❌ {message}[/]")

    def show_success(self, message: str):
        """Display success message"""
        self.console.print(f"[{LIME_PRIMARY}]✅ {message}[/]")

    def show_info(self, message: str):
        """Display informational message"""
        self.console.print(f"[{LIME_SECONDARY}]ℹ️ {message}[/]")

    def confirm(self, message: str, default: bool = False) -> bool:
        """Show compact confirmation dialog"""
        default_text = "Yes" if default else "No"

        while True:
            # Compact confirmation panel
            confirm_content = Group(
                Text(message, style="white", justify="center"),
                Text(""),
                Text.assemble(
                    ("(y) Yes  (n) No  ", "white"),
                    (f"[Enter={default_text}]", MAT_TEXT_HINT)
                )
            )

            confirm_panel = Panel(
                confirm_content,
                title="❓ Confirm",
                title_align="center",
                border_style=MAT_ACCENT,
                padding=(0, 1)
            )

            self.console.print(confirm_panel)

            key = get_key()

            if key == KeyCodes.ENTER or key == '\n':
                return default
            elif key.lower() == 'y':
                return True
            elif key.lower() == 'n':
                return False
            else:
                self.console.print(f"[red]Usa: y/n/Enter[/]")
                continue

    def get_input(self, prompt: str, default: str = "") -> str:
        """Get text input from user"""
        return Prompt.ask(f"[{LIME_ACCENT}]{prompt}[/]", default=default)

    def _display_header(self):
        """Display application header"""
        header_content = Group(
            Text("🐉 DOTFILES MANAGER", style=f"bold {LIME_PRIMARY}", justify="center"),
            Text("Manage your configuration files", style=f"{LIME_SECONDARY}", justify="center"),
            Text("")
        )

        header_panel = Panel(
            header_content,
            border_style=LIME_PRIMARY,
            padding=(0, 2)
        )

        self.console.print(header_panel)

    def show_main_menu(self) -> str:
        """Display main menu and return user choice"""
        menu_options = [
            ("1", "🐙  Browse Files", "Browse and add files to repository"),
            ("2", "🍻  Modified Files", "View current changes and commit"),
            ("3", "📋  Tracked Files", "List all tracked files"),
            ("4", "🐒  Settings", "Configure paths and options"),
            ("5", "💀  Exit", "Exit the dotfiles manager")
        ]

        current_selection = 0

        while True:
            self.console.clear()

            # Create menu lines
            menu_lines = []
            for i, (num, title, desc) in enumerate(menu_options):
                if i == current_selection:
                    if num == "5":  # Exit option
                        menu_lines.append(Text(f"        ► [{num}] {title}", style="bold red"))
                    else:
                        menu_lines.append(Text(f"        ► [{num}] {title}", style=f"bold {MAT_ACCENT}"))
                else:
                    menu_lines.append(Text(f"        · [{num}] {title}", style="dim white"))

            # Create header as a single centered block
            header_ascii = """╔═══════════════════════════════════════╗
║  🐉  D O T F I L E S   M A N A G E R  ║
║    Manage your configuration files    ║
╚═══════════════════════════════════════╝"""

            header_content = [Text(header_ascii, style=f"bold {MAT_ACCENT}", justify="center")]

            # Create footer with helpful information
            footer_info = Text("💡 Tip: Use shortcuts [1-5] for quick navigation", style=MAT_TEXT_HINT, justify="center")
            footer_controls = Text("[↑↓]: navigate • [Enter]: select • [q]: quit", style=MAT_TEXT_SECONDARY, justify="center")

            # Create complete menu content
            menu_content = Group(
                *header_content,
                Text(""),
                *menu_lines,
                Text(""),
                footer_info,
                footer_controls
            )

            # Display menu panel
            menu_panel = Panel(
                menu_content,
                style="#F8FFF8",
                border_style=MAT_ACCENT,
                box=box.ROUNDED,
                padding=(1, 1)
            )

            self.console.print(menu_panel)

            # Get user input
            key = get_key()

            if key == KeyCodes.ARROW_UP or key.lower() == 'k':
                current_selection = (current_selection - 1) % len(menu_options)
            elif key == KeyCodes.ARROW_DOWN or key.lower() == 'j':
                current_selection = (current_selection + 1) % len(menu_options)
            elif key == KeyCodes.ENTER or key == '\n':
                return str(current_selection + 1)
            elif key.lower() == 'q' or key == KeyCodes.ESC:
                return "5"  # Exit
            elif key in ['1', '2', '3', '4', '5']:  # Direct selection
                return key

    def show_file_browser(self, start_directory: str = "~") -> List[str]:
        """Enhanced file browser with Material Design colors, single-column layout, and sort functionality"""
        from ..core.file_manager import FileManager
        from ..core.config_manager import ConfigManager
        from rich.columns import Columns

        # Create temporary instances for file browsing
        config_manager = ConfigManager()
        file_manager = FileManager(config_manager)

        current_dir = os.path.expanduser(start_directory)
        selected_items = set()
        current_selection = 0
        scroll_offset_row = 0
        last_items = []
        need_refresh = True
        search_term = ""
        search_mode = False
        last_terminal_size = None
        sort_mode = 0  # 0: dirs->files, 1: mixed (alphabetical), 2: files->dirs

        def sort_items(items, sort_mode):
            """Sort items based on sort mode"""
            if not items:
                return items

            # Always keep parent directory at the top
            parent_items = [item for item in items if item.type == 'parent']
            other_items = [item for item in items if item.type != 'parent']

            if sort_mode == 0:  # Directories first
                dirs = [item for item in other_items if item.type in ['directory', 'hidden_directory']]
                files = [item for item in other_items if item.type in ['file', 'hidden_file']]
                dirs.sort(key=lambda x: x.path.lower())
                files.sort(key=lambda x: x.path.lower())
                return parent_items + dirs + files
            elif sort_mode == 1:  # Mixed (alphabetical)
                other_items.sort(key=lambda x: x.path.lower())
                return parent_items + other_items
            else:  # sort_mode == 2: Files first
                files = [item for item in other_items if item.type in ['file', 'hidden_file']]
                dirs = [item for item in other_items if item.type in ['directory', 'hidden_directory']]
                files.sort(key=lambda x: x.path.lower())
                dirs.sort(key=lambda x: x.path.lower())
                return parent_items + files + dirs

        def filter_items(items, search):
            """Filter items based on search term"""
            if not search:
                return items
            search_lower = search.lower()
            return [item for item in items if search_lower in item.path.lower()]

        def create_compact_options_section(sort_mode, selected_count, items_count):
            """Create a compact options section with Material Design colors"""
            sort_modes = ["dirs→files", "mixed", "files→dirs"]

            # Material design controls line with consistent colors
            controls_line = Text.assemble(
                ("Navigate ", MAT_TEXT_HINT), ("[", MAT_PRIMARY), ("↑↓", MAT_PRIMARY), ("]", MAT_PRIMARY), ("  ", ""),
                ("FastScroll ", MAT_TEXT_HINT), ("[", MAT_PRIMARY), ("PgUp/Dn", MAT_PRIMARY), ("]", MAT_PRIMARY), ("  ", ""),
                ("Open ", MAT_TEXT_HINT), ("[", MAT_ACCENT), ("Enter", MAT_ACCENT), ("]", MAT_ACCENT), ("  ", ""),
                ("Select ", MAT_TEXT_HINT), ("[", MAT_ACCENT), ("Space", MAT_ACCENT), ("]", MAT_ACCENT), ("  ", ""),
                ("Search ", MAT_TEXT_HINT), ("[", MAT_PRIMARY_LIGHT), ("/", MAT_PRIMARY_LIGHT), ("]", MAT_PRIMARY_LIGHT), ("  ", ""),
                ("Sort ", MAT_TEXT_HINT), ("[", MAT_PRIMARY_LIGHT), ("s", MAT_PRIMARY_LIGHT), ("]", MAT_PRIMARY_LIGHT), ("  ", ""),
                ("Add ", MAT_TEXT_HINT), ("[", MAT_PRIMARY_DARK), ("Tab", MAT_PRIMARY_DARK), ("]", MAT_PRIMARY_DARK), ("  ", ""),
                ("Exit ", MAT_TEXT_HINT), ("[", "#F44336"), ("q", "#F44336"), ("]", "#F44336")  # Material Red 500
            )

            # Material status line
            sort_colors = [MAT_SORT_BLUE, MAT_SORT_ORANGE, MAT_SORT_GREEN]
            status_line = Text.assemble(
                ("Selected ", MAT_TEXT_HINT), (f"{selected_count}", MAT_PRIMARY),
                (" • Total ", MAT_TEXT_HINT), (f"{items_count}", MAT_PRIMARY),
                (" • Sort ", MAT_TEXT_HINT), (sort_modes[sort_mode], sort_colors[sort_mode])
            )

            return [controls_line, status_line]

        while True:
            all_items = file_manager.get_directory_contents(current_dir)
            sorted_items = sort_items(all_items, sort_mode)
            items = filter_items(sorted_items, search_term)

            # Get terminal size
            terminal_size = self.console.size
            terminal_height = terminal_size.height

            # Calculate visible area (always available for navigation)
            visible_height = max(1, terminal_height - 15)
            visible_rows = visible_height

            # Only refresh if items changed, terminal resized, or explicit refresh needed
            terminal_changed = last_terminal_size != terminal_size
            items_changed = items != last_items

            if items_changed or need_refresh or terminal_changed:
                last_items = items[:]
                last_terminal_size = terminal_size
                need_refresh = False

                # Ensure current_selection is within bounds
                if current_selection >= len(items):
                    current_selection = len(items) - 1 if items else 0

                # Single-column layout
                columns = 1
                max_item_width = (terminal_size.width - 10) // columns

                # Calculate current row and column
                if items:
                    current_row = current_selection // columns

                    # Adjust vertical scroll offset to keep current selection visible
                    if current_row < scroll_offset_row:
                        scroll_offset_row = current_row
                    elif current_row >= scroll_offset_row + visible_rows:
                        scroll_offset_row = current_row - visible_rows + 1
                else:
                    current_row = 0

                # Prepare file list content
                file_content = []

                if not items:
                    file_content.append(Text("Empty directory or no accessible items", style="red"))
                else:
                    # Create single column layout
                    for row in range(visible_rows):
                        actual_row = row + scroll_offset_row

                        if actual_row < len(items):
                            item = items[actual_row]
                            item_path = item.full_path if item.type != 'parent' else item.path
                            item_type = item.type
                            display_name = item.path

                            # Truncate long names
                            if len(display_name) > max_item_width - 8:
                                display_name = display_name[:max_item_width - 11] + "..."

                            # Show banana for selected files, space for others
                            if item_type == 'parent':
                                checkbox = " "
                            else:
                                checkbox = "🍌" if item_path in selected_items else "　"

                            # Highlight current selection
                            is_current = actual_row == current_selection

                            if is_current:
                                style = f"bold {MAT_BANANA}"  # Current selection in banana color
                                prefix = "►"
                            elif item_path in selected_items and item_type != 'parent':
                                style = f"bold {MAT_BANANA}"  # Selected items in banana color
                                prefix = " "
                            else:
                                # Apply new color scheme based on item type
                                if item_type == 'directory':
                                    style = f"bold {MAT_DIR_NORMAL}"  # Blue for directories
                                elif item_type == 'hidden_directory':
                                    style = f"bold {MAT_DIR_HIDDEN}"  # Light blue for hidden directories
                                elif item_type == 'file':
                                    style = MAT_FILE_NORMAL  # Light gray for files
                                elif item_type == 'hidden_file':
                                    style = MAT_FILE_HIDDEN  # Gray for hidden files
                                else:
                                    style = MAT_TEXT_SECONDARY
                                prefix = " "

                            # Format item with fixed width (no icon)
                            item_display = f"{prefix}{checkbox} {display_name}"
                            item_display = item_display.ljust(max_item_width)
                            file_content.append(Text(item_display, style=style))

                    # Add scroll indicator if needed
                    total_rows = len(items)
                    if total_rows > visible_rows:
                        file_content.append(Text(""))  # Empty line
                        scroll_info = Text(f"Showing rows {scroll_offset_row + 1}-{min(scroll_offset_row + visible_rows, total_rows)} of {total_rows}", style=MAT_TEXT_HINT)
                        file_content.append(scroll_info)

                # Add search line with material colors
                if search_mode:
                    search_display = f"Search: {search_term}_"
                    search_style = f"bold {MAT_ACCENT}"
                elif search_term:
                    search_display = f"Filter: {search_term} (showing {len(items)}/{len(all_items)})"
                    search_style = MAT_PRIMARY
                else:
                    search_display = "Press / to search"
                    search_style = MAT_TEXT_HINT

                file_content.append(Text(""))  # Empty line
                file_content.append(Text(search_display, style=search_style))

                # Header with current directory
                current_dir_display = current_dir.replace(os.path.expanduser('~'), '~')

                # Clear screen and display panel
                self.console.clear()

                # Add compact options at the bottom
                options_lines = create_compact_options_section(sort_mode, len(selected_items), len(items))

                # Add separator and options to file content with material colors
                file_content.append(Text(""))
                file_content.append(Text("─" * 60, style=MAT_TEXT_HINT))
                file_content.extend(options_lines)

                self.console.print(Panel(
                    Group(*file_content),
                    title=f"📁 FILE BROWSER - {current_dir_display}",
                    title_align="left",
                    border_style=MAT_ACCENT,
                    padding=(0, 1)
                ))

            # Handle input
            key = get_key()

            if search_mode:
                # Search mode input handling
                if key == KeyCodes.ENTER or key == '\n':
                    # Confirm search (Enter key)
                    search_mode = False
                    need_refresh = True
                elif key == KeyCodes.ESC:
                    # Cancel search (Escape key)
                    search_mode = False
                    search_term = ""
                    need_refresh = True
                elif key == KeyCodes.BACKSPACE or key == '\b':
                    # Remove character from search (Backspace key)
                    if search_term:
                        search_term = search_term[:-1]
                        need_refresh = True
                elif len(key) == 1 and key.isprintable():
                    # Add character to search term (printable characters)
                    search_term += key
                    current_selection = 0  # Reset selection when searching
                    need_refresh = True
            else:
                # Normal navigation mode
                if key == KeyCodes.ARROW_UP or key.lower() == 'k':
                    # Navigate up in single column (Arrow Up or K key)
                    if items:
                        current_selection = (current_selection - 1) % len(items)
                        need_refresh = True
                elif key == KeyCodes.ARROW_DOWN or key.lower() == 'j':
                    # Navigate down in single column (Arrow Down or J key)
                    if items:
                        current_selection = (current_selection + 1) % len(items)
                        need_refresh = True
                elif key == KeyCodes.PAGE_UP:
                    # Page up navigation
                    if items:
                        current_selection = max(0, current_selection - visible_rows)
                        need_refresh = True
                elif key == KeyCodes.PAGE_DOWN:
                    # Page down navigation
                    if items:
                        current_selection = min(len(items) - 1, current_selection + visible_rows)
                        need_refresh = True
                elif key == KeyCodes.ENTER or key == '\n':
                    # Enter directory or select file (Enter key)
                    if items and current_selection < len(items):
                        current_item = items[current_selection]
                        if current_item.type in ['directory', 'hidden_directory', 'parent']:
                            current_dir = current_item.full_path
                            current_selection = 0
                            scroll_offset_row = 0
                            search_term = ""  # Clear search when navigating
                            need_refresh = True
                elif key == ' ':  # Space - toggle selection (not for parent dir)
                    if items and current_selection < len(items):
                        current_item = items[current_selection]
                        if current_item.type != 'parent':
                            item_path = current_item.full_path
                            if item_path in selected_items:
                                selected_items.remove(item_path)
                            else:
                                selected_items.add(item_path)
                            need_refresh = True
                elif key == '/':  # Start search
                    search_mode = True
                    search_term = ""
                    need_refresh = True
                elif key == '\t':  # Tab - confirm selection and add to git
                    return list(selected_items)
                elif key.lower() == 's':  # Sort mode toggle
                    sort_mode = (sort_mode + 1) % 3
                    need_refresh = True
                elif key.lower() == 'q' or key == KeyCodes.ESC:
                    # Quit file browser (Q key or Escape)
                    return []

    def show_directory_contents(self, items: List[DirectoryItem], current_dir: str) -> Optional[str]:
        """Display directory contents and return selected action"""
        # This method is used by the file browser internally
        return None

    def show_tracked_files(self, files: List[FileInfo]) -> Optional[Dict[str, Any]]:
        """Display tracked files with scrollable table and file browser style controls"""
        current_selection = 0
        scroll_offset = 0
        search_term = ""
        search_mode = False

        def filter_files(files_list, search):
            """Filter files based on search term"""
            if not search:
                return files_list

            search_lower = search.lower()
            filtered = []

            for file_info in files_list:
                # Search in file path
                if search_lower in file_info.path.lower():
                    filtered.append(file_info)

            return filtered

        def create_compact_options_section(total_count, has_files):
            """Create compact options section for tracked files"""

            # Basic controls always available
            controls = [
                ("Navigate ", MAT_TEXT_HINT), ("[", MAT_PRIMARY), ("↑↓", MAT_PRIMARY), ("]", MAT_PRIMARY), ("  ", ""),
                ("FastScroll ", MAT_TEXT_HINT), ("[", MAT_PRIMARY), ("PgUp/Dn", MAT_PRIMARY), ("]", MAT_PRIMARY), ("  ", ""),
                ("Search ", MAT_TEXT_HINT), ("[", MAT_ACCENT), ("/", MAT_ACCENT), ("]", MAT_ACCENT), ("  ", "")
            ]

            # Add view control if there are files
            if has_files:
                controls.extend([("View History ", MAT_TEXT_HINT), ("[", MAT_PRIMARY_LIGHT), ("Enter", MAT_PRIMARY_LIGHT), ("]", MAT_PRIMARY_LIGHT), ("  ", "")])

            # Exit always available
            controls.extend([("Exit ", MAT_TEXT_HINT), ("[", "#F44336"), ("q", "#F44336"), ("]", "#F44336")])

            controls_line = Text.assemble(*controls)

            status_line = Text.assemble(
                ("Total ", MAT_TEXT_HINT), (f"{total_count}", MAT_PRIMARY),
                (" • Files ", MAT_TEXT_HINT), ("tracked", MAT_ACCENT)
            )

            return [controls_line, status_line]

        while True:
            self.console.clear()

            # Get terminal size for scrolling
            terminal_size = self.console.size
            terminal_height = terminal_size.height

            # Calculate available space for table
            visible_height = max(1, terminal_height - 17)  # Extra space for search line

            # Apply search filter
            filtered_files = filter_files(files, search_term)

            file_content = []

            # Add search line with material colors
            if search_mode:
                search_display = f"Search: {search_term}_"
                search_style = f"bold {MAT_ACCENT}"
            elif search_term:
                search_display = f"Filter: {search_term} (showing {len(filtered_files)}/{len(files)})"
                search_style = MAT_PRIMARY
            else:
                search_display = "Press '/' to search"
                search_style = MAT_TEXT_HINT

            search_line = Text(search_display, style=search_style)
            file_content.append(search_line)
            file_content.append(Text(""))  # Empty line for spacing

            if not filtered_files:
                if search_term:
                    file_content.append(Text("No files found with search term", style=f"{MAT_PRIMARY}"))
                    file_content.append(Text(f"Search among {len(files)} tracked files", style=f"{MAT_TEXT_SECONDARY}"))
                else:
                    file_content.append(Text("No files tracked in repository", style=f"{MAT_PRIMARY}"))
                    file_content.append(Text("Use 'Browse Files' to add files to repository", style=f"{MAT_TEXT_SECONDARY}"))
            else:
                # Ensure current_selection is within bounds
                if current_selection >= len(filtered_files):
                    current_selection = len(filtered_files) - 1 if filtered_files else 0

                # Adjust scroll offset to keep current selection visible
                current_row = current_selection
                if current_row < scroll_offset:
                    scroll_offset = current_row
                elif current_row >= scroll_offset + visible_height:
                    scroll_offset = current_row - visible_height + 1

                from ..common import format_file_size, format_file_mtime

                # Display visible rows with elegant formatting
                for row in range(visible_height):
                    actual_row = row + scroll_offset

                    if actual_row < len(filtered_files):
                        file_info = filtered_files[actual_row]

                        # File info
                        file_path = file_info.path
                        file_name = os.path.basename(file_path)
                        file_dir = os.path.dirname(file_path)

                        # Selection and current indicators
                        is_current = actual_row == current_selection

                        # Row styling
                        if is_current:
                            prefix = "►"
                            base_style = f"bold {MAT_BANANA}"
                            filename_style = f"bold {MAT_BANANA}"
                            dir_style = f"dim {MAT_BANANA}"
                            info_style = f"dim {MAT_BANANA}"
                        else:
                            prefix = " "
                            base_style = MAT_PRIMARY
                            filename_style = MAT_PRIMARY
                            dir_style = f"dim {MAT_TEXT_SECONDARY}"
                            info_style = f"dim {MAT_TEXT_SECONDARY}"

                        # Format file info
                        size_str = format_file_size(file_info.size)
                        mtime_str = format_file_mtime(file_info.mtime)

                        # Calculate available width for file path
                        available_width = terminal_size.width - 30  # Reserve space for info

                        # Format file path elegantly
                        if file_dir and file_dir != ".":
                            # Show directory in dim style + filename in normal
                            if len(file_path) > available_width:
                                # Truncate directory if too long
                                truncated_dir = "..." + file_dir[-(available_width - len(file_name) - 10):]
                                display_path = f"{truncated_dir}/{file_name}"
                            else:
                                display_path = file_path

                            file_text = Text.assemble(
                                (f"{prefix} ", base_style),
                                (os.path.dirname(display_path) + "/", dir_style),
                                (os.path.basename(display_path), filename_style),
                                (f" • {size_str} • {mtime_str}", info_style)
                            )
                        else:
                            # Just filename
                            if len(file_name) > available_width:
                                display_name = file_name[:available_width - 3] + "..."
                            else:
                                display_name = file_name

                            file_text = Text.assemble(
                                (f"{prefix} ", base_style),
                                (display_name, filename_style),
                                (f" • {size_str} • {mtime_str}", info_style)
                            )

                        file_content.append(file_text)

                # Add scroll indicator if needed
                if len(filtered_files) > visible_height:
                    file_content.append(Text(""))
                    scroll_info = Text(
                        f"Showing {scroll_offset + 1}-{min(scroll_offset + visible_height, len(filtered_files))} of {len(filtered_files)}",
                        style=MAT_TEXT_HINT
                    )
                    file_content.append(scroll_info)

            # Add options section
            options_lines = create_compact_options_section(len(files), bool(files))
            file_content.append(Text(""))
            file_content.append(Text("─" * 60, style=MAT_TEXT_HINT))
            file_content.extend(options_lines)

            # Display panel
            panel = Panel(
                Group(*file_content),
                title="📋 TRACKED FILES",
                title_align="left",
                border_style=MAT_ACCENT,
                padding=(0, 1)
            )

            self.console.print(panel)

            # Get user input
            key = get_key()

            # Handle search mode input
            if search_mode:
                if key == KeyCodes.ENTER:
                    # Confirm search (Enter key)
                    search_mode = False
                elif key == KeyCodes.ESC:
                    # Cancel search (Escape key)
                    search_mode = False
                    search_term = ""
                    current_selection = 0
                elif key == KeyCodes.BACKSPACE or key == '\b':
                    # Remove character from search (Backspace key)
                    if search_term:
                        search_term = search_term[:-1]
                        current_selection = 0
                elif len(key) == 1 and key.isprintable():
                    # Add character to search term (printable characters)
                    search_term += key
                    current_selection = 0  # Reset selection when searching
                continue

            # Navigation
            if key == KeyCodes.ARROW_UP or key.lower() == 'k':
                if filtered_files:
                    current_selection = (current_selection - 1) % len(filtered_files)
            elif key == KeyCodes.ARROW_DOWN or key.lower() == 'j':
                if filtered_files:
                    current_selection = (current_selection + 1) % len(filtered_files)
            elif key == KeyCodes.PAGE_UP:
                if filtered_files:
                    current_selection = max(0, current_selection - visible_height)
            elif key == KeyCodes.PAGE_DOWN:
                if filtered_files:
                    current_selection = min(len(filtered_files) - 1, current_selection + visible_height)

            # Actions
            elif key == KeyCodes.ENTER:
                # Future: View file history across commits
                if filtered_files and current_selection < len(filtered_files):
                    current_file = filtered_files[current_selection]
                    # TODO: Implement file history viewer
                    self.show_info(f"File history '{current_file.path}' - Feature in development")
                    self.console.print(f"\n[{MAT_TEXT_SECONDARY}]Press any key to continue...[/]")
                    get_key()

            elif key == '/':  # Start search
                search_mode = True
                search_term = ""
                current_selection = 0

            elif key.lower() == 'q' or key == KeyCodes.ESC:
                if search_term:  # Clear search first if active
                    search_term = ""
                    current_selection = 0
                else:
                    return None

    def show_modified_files(self, changes: List[GitChange]) -> Optional[Dict[str, Any]]:
        """Display modified files with scrollable table and file browser style controls"""
        current_selection = 0
        scroll_offset = 0
        selected_files = set()
        search_term = ""
        search_mode = False

        from ..core.git_manager import GitManager
        from ..core.config_manager import ConfigManager

        # Create temporary instances for parsing
        config_manager = ConfigManager()
        git_manager = GitManager(config_manager)

        def filter_changes(changes_list, search):
            """Filter changes based on search term"""
            if not search:
                return changes_list

            search_lower = search.lower()
            filtered = []

            for change in changes_list:
                # Search in file path (both filename and directory)
                if search_lower in change.file.lower():
                    filtered.append(change)

            return filtered

        def create_compact_options_section(selected_count, total_count, has_changes, has_commits_to_push, has_commits_to_pull):
            """Create compact options section similar to file browser"""

            # First line - Navigation and search controls
            controls_line1 = [
                ("Navigate ", MAT_TEXT_HINT), ("[", MAT_PRIMARY), ("↑↓", MAT_PRIMARY), ("]", MAT_PRIMARY), ("  ", ""),
                ("FastScroll ", MAT_TEXT_HINT), ("[", MAT_PRIMARY), ("PgUp/Dn", MAT_PRIMARY), ("]", MAT_PRIMARY), ("  ", ""),
                ("Search ", MAT_TEXT_HINT), ("[", MAT_ACCENT), ("/", MAT_ACCENT), ("]", MAT_ACCENT), ("  ", ""),
                ("Refresh ", MAT_TEXT_HINT), ("[", MAT_ACCENT), ("r", MAT_ACCENT), ("]", MAT_ACCENT)
            ]

            # Second line - Action controls
            controls_line2 = []

            # Add selection controls only if there are changes
            if has_changes:
                controls_line2.extend([("Select ", MAT_TEXT_HINT), ("[", MAT_ACCENT), ("Space", MAT_ACCENT), ("]", MAT_ACCENT), ("  ", "")])

                # Add commit action only if there are changes
                controls_line2.extend([("Commit ", MAT_TEXT_HINT), ("[", MAT_PRIMARY_LIGHT), ("c", MAT_PRIMARY_LIGHT), ("]", MAT_PRIMARY_LIGHT), ("  ", "")])

                # Add unstage options based on selection and total changes
                if selected_count > 0:
                    # Show unstage selection only if files are selected
                    controls_line2.extend([("Unstage ", MAT_TEXT_HINT), ("[", MAT_PRIMARY_DARK), ("r", MAT_PRIMARY_DARK), ("]", MAT_PRIMARY_DARK), ("  ", "")])

                if total_count > 0:
                    # Show empty staging if there are any changes
                    controls_line2.extend([("Empty ", MAT_TEXT_HINT), ("[", "bold red"), ("e", "bold red"), ("]", "bold red"), ("  ", "")])

            # Add git sync options - always show but with different colors based on availability
            if has_commits_to_push:
                controls_line2.extend([("Push ", MAT_TEXT_HINT), ("[", MAT_PRIMARY_LIGHT), ("p", MAT_PRIMARY_LIGHT), ("]", MAT_PRIMARY_LIGHT), ("  ", "")])
            else:
                controls_line2.extend([("Push ", MAT_TEXT_HINT), ("[", MAT_TEXT_HINT), ("p", MAT_TEXT_HINT), ("]", MAT_TEXT_HINT), ("  ", "")])

            # Pull is always available
            controls_line2.extend([("Pull ", MAT_TEXT_HINT), ("[", MAT_PRIMARY_LIGHT), ("g", MAT_PRIMARY_LIGHT), ("]", MAT_PRIMARY_LIGHT), ("  ", "")])

            # Exit always available
            controls_line2.extend([("Exit ", MAT_TEXT_HINT), ("[", "#F44336"), ("q", "#F44336"), ("]", "#F44336")])

            controls_line = [Text.assemble(*controls_line1), Text.assemble(*controls_line2)]

            status_line = Text.assemble(
                ("Selected ", MAT_TEXT_HINT), (f"{selected_count}", MAT_PRIMARY),
                (" • Total ", MAT_TEXT_HINT), (f"{total_count}", MAT_PRIMARY),
                (" • Changes ", MAT_TEXT_HINT), ("detected", MAT_ACCENT)
            )

            return controls_line + [status_line]

        # Static push/pull status - load once at entry and update only on manual refresh
        push_pull_status = {
            'has_remote': False,
            'commits_ahead': 0,
            'commits_behind': 0,
            'loaded': False
        }

        def load_push_pull_status():
            """Load push/pull status once - called on entry and manual refresh"""
            has_remote, commits_ahead, _ = git_manager.get_push_status()
            _, commits_behind, _ = git_manager.get_pull_status()
            push_pull_status.update({
                'has_remote': has_remote,
                'commits_ahead': commits_ahead,
                'commits_behind': commits_behind,
                'loaded': True
            })

        # Load status once on page entry
        load_push_pull_status()

        while True:
            self.console.clear()

            # Get terminal size for scrolling
            terminal_size = self.console.size
            terminal_height = terminal_size.height

            # Calculate available space for table
            visible_height = max(1, terminal_height - 17)  # Extra space for search line

            # Apply search filter
            filtered_changes = filter_changes(changes, search_term)

            # Use static push/pull status
            has_commits_to_push = push_pull_status['has_remote'] and push_pull_status['commits_ahead'] > 0
            has_commits_to_pull = push_pull_status['has_remote'] and push_pull_status['commits_behind'] > 0

            file_content = []

            # Add search line with material colors
            if search_mode:
                search_display = f"Search: {search_term}_"
                search_style = f"bold {MAT_ACCENT}"
            elif search_term:
                search_display = f"Filter: {search_term} (showing {len(filtered_changes)}/{len(changes)})"
                search_style = MAT_PRIMARY
            else:
                search_display = "Press '/' to search"
                search_style = MAT_TEXT_HINT

            search_line = Text(search_display, style=search_style)
            file_content.append(search_line)
            file_content.append(Text(""))  # Empty line for spacing

            if not filtered_changes:
                if search_term:
                    file_content.append(Text("No files found with search term", style=f"{MAT_PRIMARY}"))
                    file_content.append(Text(f"Search among {len(changes)} modified files", style=f"{MAT_TEXT_SECONDARY}"))
                else:
                    file_content.append(Text("No changes detected", style=f"{MAT_PRIMARY}"))

                    sync_messages = []
                    if has_commits_to_push:
                        sync_messages.append(f"🚀 {push_pull_status['commits_ahead']} commit{'s' if push_pull_status['commits_ahead'] > 1 else ''} to push - press 'p'")
                    if has_commits_to_pull:
                        sync_messages.append(f"📥 {push_pull_status['commits_behind']} commit{'s' if push_pull_status['commits_behind'] > 1 else ''} to pull - press 'g'")

                    if sync_messages:
                        for msg in sync_messages:
                            file_content.append(Text(msg, style=f"{MAT_ACCENT}"))
                    else:
                        file_content.append(Text("All tracked files are up to date", style=f"{MAT_TEXT_SECONDARY}"))
            else:
                # Ensure current_selection is within bounds
                if current_selection >= len(filtered_changes):
                    current_selection = len(filtered_changes) - 1 if filtered_changes else 0

                # Adjust scroll offset to keep current selection visible
                current_row = current_selection
                if current_row < scroll_offset:
                    scroll_offset = current_row
                elif current_row >= scroll_offset + visible_height:
                    scroll_offset = current_row - visible_height + 1

                # Display visible rows with elegant formatting
                for row in range(visible_height):
                    actual_row = row + scroll_offset

                    if actual_row < len(filtered_changes):
                        change = filtered_changes[actual_row]

                        # File info
                        file_path = change.file
                        file_name = os.path.basename(file_path)
                        file_dir = os.path.dirname(file_path)

                        # Selection and current indicators
                        is_selected = change.file in selected_files
                        is_current = actual_row == current_selection

                        # Selection indicator
                        if is_selected:
                            selection_icon = "🍌"  # Selected (banana emoji)
                        else:
                            selection_icon = "　"  # Unselected (wide space)

                        # Git status with colors
                        status_char, status_color = self._get_status_char_and_color(change.staged, change.worktree)

                        # Row styling
                        if is_current:
                            prefix = "►"
                            base_style = f"bold {MAT_BANANA}"
                            filename_style = f"bold {MAT_BANANA}"
                            dir_style = f"dim {MAT_BANANA}"
                        elif is_selected:
                            prefix = " "
                            base_style = f"bold {MAT_BANANA}"
                            filename_style = f"bold {MAT_BANANA}"
                            dir_style = f"dim {MAT_BANANA}"
                        else:
                            prefix = " "
                            base_style = MAT_PRIMARY
                            filename_style = MAT_PRIMARY
                            dir_style = f"dim {MAT_TEXT_SECONDARY}"

                        # Calculate available width for file path
                        available_width = terminal_size.width - 20  # Reserve space for status and selection

                        # Format file path elegantly
                        if file_dir and file_dir != ".":
                            # Show directory in dim style + filename in normal
                            if len(file_path) > available_width:
                                # Truncate directory if too long
                                truncated_dir = "..." + file_dir[-(available_width - len(file_name) - 10):]
                                display_path = f"{truncated_dir}/{file_name}"
                            else:
                                display_path = file_path

                            file_text = Text.assemble(
                                (f"{prefix} {selection_icon} ", base_style),
                                (f"{status_char} ", status_color),
                                (os.path.dirname(display_path) + "/", dir_style),
                                (os.path.basename(display_path), filename_style)
                            )
                        else:
                            # Just filename
                            if len(file_name) > available_width:
                                display_name = file_name[:available_width - 3] + "..."
                            else:
                                display_name = file_name

                            file_text = Text.assemble(
                                (f"{prefix} {selection_icon} ", base_style),
                                (f"{status_char} ", status_color),
                                (display_name, filename_style)
                            )

                        file_content.append(file_text)

                # Add scroll indicator if needed
                if len(filtered_changes) > visible_height:
                    file_content.append(Text(""))
                    scroll_info = Text(
                        f"Showing {scroll_offset + 1}-{min(scroll_offset + visible_height, len(filtered_changes))} of {len(filtered_changes)}",
                        style=MAT_TEXT_HINT
                    )
                    file_content.append(scroll_info)

            # Add options section
            options_lines = create_compact_options_section(len(selected_files), len(changes), bool(changes), has_commits_to_push, has_commits_to_pull)
            file_content.append(Text(""))
            file_content.append(Text("─" * 60, style=MAT_TEXT_HINT))
            file_content.extend(options_lines)

            # Display panel
            panel = Panel(
                Group(*file_content),
                title="📝 MODIFIED FILES",
                title_align="left",
                border_style=MAT_ACCENT,
                padding=(0, 1)
            )

            self.console.print(panel)

            # Get user input
            key = get_key()

            # Handle search mode input
            if search_mode:
                if key == KeyCodes.ENTER:
                    # Confirm search (Enter key)
                    search_mode = False
                elif key == KeyCodes.ESC:
                    # Cancel search (Escape key)
                    search_mode = False
                    search_term = ""
                    current_selection = 0
                elif key == KeyCodes.BACKSPACE or key == '\b':
                    # Remove character from search (Backspace key)
                    if search_term:
                        search_term = search_term[:-1]
                        current_selection = 0
                elif len(key) == 1 and key.isprintable():
                    # Add character to search term (printable characters)
                    search_term += key
                    current_selection = 0  # Reset selection when searching
                continue

            # Navigation
            if key == KeyCodes.ARROW_UP or key.lower() == 'k':
                if filtered_changes:
                    current_selection = (current_selection - 1) % len(filtered_changes)
            elif key == KeyCodes.ARROW_DOWN or key.lower() == 'j':
                if filtered_changes:
                    current_selection = (current_selection + 1) % len(filtered_changes)
            elif key == KeyCodes.PAGE_UP:
                if filtered_changes:
                    current_selection = max(0, current_selection - visible_height)
            elif key == KeyCodes.PAGE_DOWN:
                if filtered_changes:
                    current_selection = min(len(filtered_changes) - 1, current_selection + visible_height)
            elif key == ' ':  # Space - toggle selection
                if filtered_changes and current_selection < len(filtered_changes):
                    current_file = filtered_changes[current_selection].file
                    if current_file in selected_files:
                        selected_files.remove(current_file)
                    else:
                        selected_files.add(current_file)

            # Actions
            elif key.lower() == 'c':
                # Commit changes
                if not changes:
                    self.show_info("No changes to commit")
                    self.console.print(f"\n[{MAT_TEXT_SECONDARY}]Press any key to continue...[/]")
                    get_key()
                    continue
                message = git_manager.generate_commit_message(changes)
                self.console.print(f"\n[{MAT_ACCENT}]Generated commit message:[/] {message}")

                if self.confirm("Confirm commit?", True):
                    # Refresh push/pull status after commit since it changes push status
                    return {"action": "commit", "message": message, "refresh_status": True}

            elif key.lower() == 'p':
                # Push changes
                return {"action": "push", "refresh_status": True}

            elif key.lower() == 'g':
                # Pull changes
                return {"action": "pull", "refresh_status": True}

            elif key.lower() == 'r':
                if selected_files:
                    # Unstage only selected files - when files are selected
                    if self.confirm(f"Remove {len(selected_files)} files from staging?", False):
                        return {"action": "unstage_files", "files": list(selected_files)}
                else:
                    # Refresh push/pull status when no files are selected
                    load_push_pull_status()
                    continue

            elif key.lower() == 'e' and changes:  # E for "empty" staging - only if there are changes
                # Unstage all
                staged_count = len([c for c in changes if c.staged and c.staged != ' '])
                if staged_count == 0:
                    info_panel = Panel(
                        Text("No files in staging to clear", style="white"),
                        title="ℹ️ Info",
                        border_style=MAT_PRIMARY,
                        padding=(0, 1)
                    )
                    self.console.print(info_panel)
                    get_key()
                else:
                    if self.confirm(f"Clear staging? ({staged_count} changes)", False):
                        return {"action": "unstage_all"}

            elif key == '/':  # Start search
                search_mode = True
                search_term = ""
                current_selection = 0

            elif key.lower() == 'q' or key == KeyCodes.ESC:
                if search_term:  # Clear search first if active
                    search_term = ""
                    current_selection = 0
                else:
                    return None

    def _get_status_char_and_color(self, staged: str, worktree: str) -> tuple[str, str]:
        """Get appropriate character and color for git status"""
        # Priority: staged status first, then worktree
        if staged and staged != ' ':
            if staged == 'A':
                return 'A', "bold green"      # Added/New file
            elif staged == 'M':
                return 'M', "bold blue"       # Modified
            elif staged == 'D':
                return 'D', "bold red"        # Deleted
            elif staged == 'R':
                return 'R', "bold magenta"    # Renamed
            elif staged == 'C':
                return 'C', "bold cyan"       # Copied

        if worktree and worktree != ' ':
            if worktree == 'M':
                return 'M', "bold yellow"     # Modified in worktree
            elif worktree == 'D':
                return 'D', "bold red"        # Deleted in worktree
            elif worktree == '?':
                return '?', "bold white"      # Untracked

        return ' ', MAT_TEXT_HINT  # No status

    def show_settings_menu(self) -> str:
        """Display settings menu and return choice"""
        from ..core.config_manager import ConfigManager

        # Check if logging is enabled to show log viewer option
        config_manager = ConfigManager()
        logging_enabled = config_manager.config.enable_logging

        menu_options = [
            ("1", "✏️  Edit Settings", "Edit configuration settings"),
            ("2", "🚀  Initialize Git Repo", "Initialize bare git repository"),
            ("3", "📝  Edit .gitignore", "Edit .gitignore patterns"),
            ("4", "🗑️  Manage Backups", "Manage backup files")
        ]

        if logging_enabled:
            menu_options.append(("5", "📋  View Logs", "View application logs"))
            menu_options.append(("6", "🔙  Back to Menu", "Return to main menu"))
        else:
            menu_options.append(("5", "🔙  Back to Menu", "Return to main menu"))

        current_selection = 0

        while True:
            self.console.clear()

            # Get current config for display
            from ..core.config_manager import ConfigManager
            config_manager = ConfigManager()
            config = config_manager.config

            # Create menu lines
            menu_lines = []
            for i, (num, title, desc) in enumerate(menu_options):
                if i == current_selection:
                    menu_lines.append(Text(f"        ► [{num}] {title}", style=f"bold {MAT_ACCENT}"))
                else:
                    menu_lines.append(Text(f"        · [{num}] {title}", style="dim white"))

            # Create config info
            config_info = Group(
                Text(f"Git Directory: {config.git_dir}", style=MAT_TEXT_SECONDARY),
                Text(f"Work Tree: {config.work_tree}", style=MAT_TEXT_SECONDARY),
                Text(f"Remote: {config.remote or 'Not configured'}", style=MAT_TEXT_SECONDARY)
            )

            # Create complete menu content
            menu_content = Group(
                config_info,
                Text(""),
                *menu_lines,
                Text(""),
                Text(f"[↑↓/hjkl]: navigate • [Enter]: select • [1-{len(menu_options)}]: direct • [q]: back", style=MAT_TEXT_SECONDARY, justify="center")
            )

            # Display menu panel
            menu_panel = Panel(
                menu_content,
                title="🐒 SETTINGS",
                title_align="center",
                style="#F8FFF8",
                border_style=MAT_ACCENT,
                box=box.ROUNDED,
                padding=(1, 1)
            )

            self.console.print(menu_panel)

            # Get user input
            key = get_key()

            if key == KeyCodes.ARROW_UP or key.lower() == 'k':
                current_selection = (current_selection - 1) % len(menu_options)
            elif key == KeyCodes.ARROW_DOWN or key.lower() == 'j':
                current_selection = (current_selection + 1) % len(menu_options)
            elif key == KeyCodes.ENTER or key == '\n':
                return str(current_selection + 1)
            elif key.lower() == 'q' or key == KeyCodes.ESC:
                return str(len(menu_options))  # Last option (return to menu)
            elif key in [str(i) for i in range(1, len(menu_options) + 1)]:  # Direct selection
                return key

    def edit_settings(self, current_config: Dict[str, str]) -> Optional[Dict[str, str]]:
        """Edit all configuration settings in a compact form interface"""
        # Create a copy of current config to edit
        temp_config = current_config.copy()

        # Form fields configuration
        fields = [
            {'key': 'git_dir', 'label': 'Git Directory', 'icon': '📁', 'placeholder': '~/.dotfiles.git'},
            {'key': 'work_tree', 'label': 'Work Tree', 'icon': '🌳', 'placeholder': '~'},
            {'key': 'remote', 'label': 'Remote URL', 'icon': '🌐', 'placeholder': 'https://github.com/user/dotfiles.git'},
            {'key': 'enable_logging', 'label': 'Enable Logging', 'icon': '📝', 'placeholder': 'false', 'type': 'bool'}
        ]

        current_field = 0
        editing_mode = False
        edit_value = ""

        while True:
            self.console.clear()

            # Build compact form content
            form_content = []
            form_content.append(Text("⚙️ CONFIGURATION", style=f"bold {LIME_PRIMARY}"))
            form_content.append(Text("↑↓: navigate  Enter: edit  s: save  r: reset field  q: exit", style=f"{LIME_SECONDARY}"))
            form_content.append(Text(""))

            # Display all fields in compact form
            for i, field in enumerate(fields):
                value = temp_config.get(field['key'], '')
                is_active = (i == current_field)
                is_editing = (is_active and editing_mode)
                is_bool = field.get('type') == 'bool'

                # Determine display value
                if is_editing and not is_bool:
                    display_value = edit_value
                    cursor = "█"  # Cursor block
                elif is_bool:
                    # Boolean field - show as toggle
                    bool_value = value if isinstance(value, bool) else str(value).lower() == 'true'
                    display_value = "✅ Enabled" if bool_value else "❌ Disabled"
                    cursor = " [Space: toggle]" if is_active else ""
                else:
                    display_value = str(value) if value else f"({field['placeholder']})"
                    cursor = ""

                # Field styling
                if is_active:
                    if is_editing:
                        # Field being edited - green background
                        field_style = f"bold white on {LIME_ACCENT}"
                        value_style = f"bold black on white"
                        prefix = "✏️ "
                    else:
                        # Active field - highlighted
                        field_style = f"bold {LIME_PRIMARY}"
                        value_style = f"bold {LIME_PRIMARY}"
                        prefix = "► "
                else:
                    # Inactive field - dimmed
                    field_style = f"dim {LIME_SECONDARY}"
                    value_style = "dim white"
                    prefix = "  "

                # Compact single-line display
                line = f"{prefix}{field['icon']} {field['label']:<12}: {display_value}{cursor}"
                form_content.append(Text(line, style=field_style if not is_editing else value_style))

            form_content.append(Text(""))
            form_content.append(Text("─────────────────────────────────────", style=LIME_SECONDARY))

            # Status message
            if editing_mode:
                form_content.append(Text(f"✏️ Editing {fields[current_field]['label']} (Enter: confirm, Esc: cancel)", style=f"bold {LIME_ACCENT}"))
            else:
                form_content.append(Text("Controls: ↑↓ navigate, Enter edit, s save all, r reset current field", style="white"))

            # Display compact panel
            form_panel = Panel(
                Group(*form_content),
                title="📝 FORM SETTINGS",
                title_align="center",
                border_style=LIME_ACCENT if not editing_mode else LIME_PRIMARY,
                padding=(1, 1)
            )

            self.console.print(form_panel)

            # Handle input
            try:
                if editing_mode:
                    # In editing mode - handle text input
                    key = get_key()

                    if key == KeyCodes.ESC:
                        # Cancel editing (Escape key)
                        editing_mode = False
                        edit_value = ""

                    elif key == KeyCodes.ENTER:
                        # Confirm editing (Enter/Return key)
                        temp_config[fields[current_field]['key']] = edit_value
                        editing_mode = False
                        edit_value = ""

                    elif key == KeyCodes.BACKSPACE or key == KeyCodes.BACKSPACE_ALT:
                        # Remove character (Backspace key)
                        if edit_value:
                            edit_value = edit_value[:-1]

                    elif len(key) == 1 and key.isprintable():
                        # Add character (printable characters only)
                        edit_value += key

                else:
                    # Navigation mode
                    key = get_key()

                    if key == KeyCodes.ARROW_UP or key.lower() == 'k':
                        # Navigate up
                        current_field = (current_field - 1) % len(fields)

                    elif key == KeyCodes.ARROW_DOWN or key.lower() == 'j':
                        # Navigate down
                        current_field = (current_field + 1) % len(fields)

                    elif key == KeyCodes.ENTER or key == ' ':
                        # Handle field interaction
                        field = fields[current_field]
                        if field.get('type') == 'bool':
                            # Toggle boolean field with Enter or Space
                            current_value = temp_config.get(field['key'], False)
                            if isinstance(current_value, str):
                                current_value = current_value.lower() == 'true'
                            temp_config[field['key']] = not current_value
                        elif key == KeyCodes.ENTER:
                            # Start editing text field with Enter
                            edit_value = str(temp_config.get(field['key'], ''))
                            editing_mode = True

                    elif key.lower() == 's':
                        # Save and exit
                        return temp_config

                    elif key.lower() == 'r':
                        # Reset current field to default
                        field = fields[current_field]
                        self.console.print()

                        # Show reset confirmation
                        current_value = temp_config.get(field['key'], '')
                        default_value = field['placeholder']

                        reset_panel = Panel(
                            Group(
                                Text(f"🔄 Reset Field: {field['label']}", style=f"bold {LIME_ACCENT}"),
                                Text(""),
                                Text(f"Current value: {current_value or '(empty)'}", style="white"),
                                Text(f"Default value: {default_value}", style=LIME_SECONDARY),
                                Text(""),
                                Text("Confirm reset of this field? (y/n)", style=f"bold {LIME_PRIMARY}")
                            ),
                            title="⚠️ CONFIRM RESET",
                            border_style="yellow",
                            padding=(1, 1)
                        )
                        self.console.print(reset_panel)

                        confirm_key = get_key()
                        if confirm_key.lower() == 'y':
                            temp_config[field['key']] = field['placeholder']

                    elif key.lower() == 'q' or key == KeyCodes.ESC:
                        # Exit without saving
                        return None

            except KeyboardInterrupt:
                # Handle Ctrl+C gracefully
                return None

    def show_progress(self, message: str, progress: float = -1):
        """Show progress indicator"""
        if progress >= 0:
            self.console.print(f"[{LIME_SECONDARY}]{message} ({progress:.1f}%)[/]")
        else:
            self.console.print(f"[{LIME_SECONDARY}]{message}...[/]")

    def hide_progress(self):
        """Hide progress indicator"""
        # Rich doesn't need explicit hiding for simple progress messages
        pass

    def initialize_git_repo_detailed(self, config: Dict[str, str]) -> bool:
        """Show detailed git repository initialization interface"""
        self.console.clear()

        # Get settings
        git_dir = os.path.expanduser(config.get('git_dir', '~/.dotfiles.git'))
        work_tree = os.path.expanduser(config.get('work_tree', '~'))
        remote_url = config.get('remote', '')

        # Display initialization info
        init_content = Group(
            Text("✨ DOTFILES REPOSITORY INITIALIZATION ✨", style=f"bold {LIME_PRIMARY}", justify="center"),
            Text(""),
            Text("🎯 Current Configuration", style=f"bold {LIME_ACCENT}", justify="center"),
            Text(""),
            Text(f"📁 Git Directory: {git_dir}", style=f"{LIME_SECONDARY}"),
            Text(f"🌳 Work Tree:     {work_tree}", style=f"{LIME_SECONDARY}"),
            Text(f"🌐 Remote URL:    {remote_url if remote_url else '❌ Not configured'}", style=f"{LIME_SECONDARY}"),
            Text(""),
            Text("🚀 Operations to Perform", style=f"bold {LIME_ACCENT}", justify="center"),
            Text(""),
            Text("✅ Will create a bare repository in Git Directory", style="white"),
            Text("✅ Will configure work tree for dotfiles", style="white"),
            Text("✅ Will create .gitignore in ~/.config/dotfiles-manager/", style="white"),
            Text("✅ Will add remote if configured", style="white"),
            Text("✅ Will create commands to manage dotfiles", style="white"),
            Text("✅ Will configure optimal settings", style="white")
        )

        init_panel = Panel(
            init_content,
            title="🎨 REPOSITORY INITIALIZATION",
            title_align="center",
            border_style=LIME_PRIMARY,
            padding=(1, 2)
        )

        self.console.print(init_panel)

        # Pause to let user read the information
        self.console.print(f"\n[{LIME_SECONDARY}]📖 Read the information above and press any key to continue...[/]")
        get_key()

        # Clear screen after user reads the information
        self.console.clear()

        # Check if git directory already exists
        if os.path.exists(git_dir):
            self.console.print()

            warning_content = Group(
                Text("🚨 EXISTING REPOSITORY DETECTED", style="bold red", justify="center"),
                Text(""),
                Text(f"📁 {git_dir}", style="bold yellow", justify="center"),
                Text("already exists and contains data!", style="yellow", justify="center"),
                Text(""),
                Text("⚠️  DESTRUCTIVE OPERATION ⚠️", style="bold red", justify="center"),
                Text(""),
                Text("Choose how to proceed:", style=f"bold {LIME_PRIMARY}"),
                Text(""),
                Text("🔥 [s] REPLACE", style="bold red"),
                Text("   └─ Completely removes existing repository", style="red"),
                Text("   └─ Creates a new empty repository", style="red"),
                Text("   └─ ALL EXISTING DATA WILL BE LOST!", style="bold red"),
                Text(""),
                Text("🛡️  [n] CANCEL", style="bold green"),
                Text("   └─ Keep existing repository", style="green"),
                Text("   └─ No changes will be made", style="green"),
                Text("   └─ Safe option - no data lost", style="green"),
                Text(""),
                Text("⚠️  REPLACEMENT IS IRREVERSIBLE! ⚠️", style="bold red", justify="center")
            )

            warning_panel = Panel(
                warning_content,
                title="💥 WARNING - EXISTING DATA",
                title_align="center",
                border_style="red",
                padding=(1, 2)
            )

            self.console.print(warning_panel)
            self.console.print()
            self.console.print("🎯 Choice (y/n): ", end="")

            choice = get_key()
            self.console.print(f"[bold]{choice}[/bold]")

            if choice.lower() == 'y':
                # Show final confirmation
                self.console.print()

                final_confirm = Group(
                    Text("💀 CONFIRM PERMANENT DELETION 💀", style="bold red", justify="center"),
                    Text(""),
                    Text("You are about to PERMANENTLY DELETE:", style="red", justify="center"),
                    Text(f"📁 {git_dir}", style="bold yellow", justify="center"),
                    Text(""),
                    Text("Are you ABSOLUTELY SURE you want to proceed?", style="bold red", justify="center")
                )

                final_panel = Panel(
                    final_confirm,
                    title="🚨 ULTIMA POSSIBILITÀ DI FERMARTI",
                    title_align="center",
                    border_style="red",
                    padding=(1, 2)
                )

                self.console.print(final_panel)
                self.console.print()
                self.console.print("💀 Final confirmation (y/n): ", end="")

                final_choice = get_key()
                self.console.print(f"[bold]{final_choice}[/bold]")

                if final_choice.lower() != 's':
                    self.show_info("Initialization cancelled.")
                    return False
            else:
                self.show_info("Initialization cancelled.")
                return False
        else:
            # No existing repository - show confirmation
            self.console.print()
            proceed_content = Group(
                Text("✨ EVERYTHING READY FOR INITIALIZATION", style=f"bold {LIME_PRIMARY}", justify="center"),
                Text(""),
                Text("No existing repository found.", style=f"{LIME_SECONDARY}"),
                Text("A new clean repository will be created.", style=f"{LIME_SECONDARY}"),
                Text(""),
                Text("Proceed with initialization?", style=f"bold {LIME_ACCENT}", justify="center")
            )

            proceed_panel = Panel(
                proceed_content,
                title="🚀 CONFIRM INITIALIZATION",
                title_align="center",
                border_style=LIME_PRIMARY,
                padding=(1, 2)
            )

            self.console.print(proceed_panel)
            self.console.print()
            self.console.print("🎯 Proceed? (y/n): ", end="")

            choice = get_key()
            self.console.print(f"[bold]{choice}[/bold]")

            if choice.lower() != 'y':
                self.show_info("Initialization cancelled.")
                return False

        return True  # Proceed with initialization

    def show_backup_manager(self):
        """Show backup management interface"""
        from ..core.git_manager import GitManager
        from ..core.config_manager import ConfigManager

        config_manager = ConfigManager()
        git_manager = GitManager(config_manager)

        current_selection = 0
        scroll_offset = 0

        while True:
            self.console.clear()

            # Get backup list
            backups = git_manager.get_backup_directories()

            # Get terminal size for scrolling
            terminal_size = self.console.size
            terminal_height = terminal_size.height
            # Account for: title(1) + empty(1) + header(1) + empty(1) + footer(1) + empty(1) + controls(1) + panel borders(2) + margins(2)
            available_height = terminal_height - 12  # More conservative
            max_visible_items = max(2, available_height)  # Minimum 2 items

            # Calculate scroll offset
            if current_selection < scroll_offset:
                scroll_offset = current_selection
            elif current_selection >= scroll_offset + max_visible_items:
                scroll_offset = current_selection - max_visible_items + 1

            # Create header
            title_text = Text("🗑️ BACKUP MANAGER", style=f"bold {MAT_PRIMARY}")

            # Content lines
            content_lines = []
            content_lines.append("")

            if not backups:
                content_lines.append(Text("No backups found", style=MAT_TEXT_SECONDARY))
                content_lines.append("")
                content_lines.append(Text("[q] Back to menu", style=MAT_TEXT_HINT))
            else:
                # Show scroll info if needed
                if len(backups) > max_visible_items:
                    content_lines.append(Text(f"Backups {scroll_offset + 1}-{min(scroll_offset + max_visible_items, len(backups))} of {len(backups)}", style=MAT_TEXT_PRIMARY))
                else:
                    content_lines.append(Text(f"Found {len(backups)} backups:", style=MAT_TEXT_PRIMARY))
                content_lines.append("")

                # Get terminal width for alignment
                panel_width = min(80, terminal_size.width - 6)  # Account for panel padding

                # List visible backups with selection
                for i in range(max_visible_items):
                    backup_idx = i + scroll_offset
                    if backup_idx >= len(backups):
                        break

                    backup = backups[backup_idx]

                    # Format size
                    if backup['size'] < 1024:
                        size_str = f"{backup['size']}B"
                    elif backup['size'] < 1024 * 1024:
                        size_str = f"{backup['size'] / 1024:.1f}KB"
                    else:
                        size_str = f"{backup['size'] / (1024 * 1024):.1f}MB"

                    # Format timestamp
                    time_str = backup['timestamp'].strftime("%d/%m/%Y %H:%M:%S")
                    file_info = f"{backup['file_count']} file"

                    if backup_idx == current_selection:
                        style = f"bold {MAT_BANANA}"
                        prefix = "🍌"
                        # The emoji counts as about 2 characters for alignment
                        prefix_length = 2
                    else:
                        style = "bright_black"  # Light gray leggibile
                        prefix = "  "  # Due spazi per compensare la larghezza dell'emoji
                        prefix_length = 2

                    # Create aligned text: timestamp left, size right
                    main_text = f"{time_str} • {file_info}"
                    right_text = size_str

                    # Calculate spacing for right alignment using consistent prefix length
                    total_left_length = prefix_length + len(main_text) + 1  # +1 for space after prefix
                    available_space = panel_width - total_left_length - len(right_text)
                    spacing = max(1, available_space)

                    left_text = f"{prefix} {main_text}"

                    backup_info = Text.assemble(
                        (left_text, style),
                        (" " * spacing, style),
                        (right_text, MAT_TEXT_HINT)
                    )
                    content_lines.append(backup_info)

                content_lines.append("")

                # Show scroll hint if needed
                if len(backups) > max_visible_items:
                    content_lines.append(Text("[↑↓] Navigate/Scroll • [x] Delete • [q] Back", style=MAT_TEXT_HINT))
                else:
                    content_lines.append(Text("[↑↓] Navigate • [x] Delete • [q] Back", style=MAT_TEXT_HINT))

            # Create panel
            panel_content = Group(*content_lines)
            panel = Panel(
                panel_content,
                title=title_text,
                border_style=MAT_PRIMARY,
                padding=(1, 2)
            )

            # Display panel
            self.console.print(panel, justify="center")

            if not backups:
                # No backups, only allow quit
                key = get_key()
                if key in ['q', KeyCodes.ESC]:
                    break
                continue

            # Handle input
            key = get_key()

            if key in ['q', KeyCodes.ESC]:
                break
            elif key == KeyCodes.ARROW_UP and current_selection > 0:
                current_selection -= 1
            elif key == KeyCodes.ARROW_DOWN and current_selection < len(backups) - 1:
                current_selection += 1
            elif key == 'x':
                # Delete selected backup
                if backups:
                    backup = backups[current_selection]
                    if git_manager.delete_backup(backup['name']):
                        self.show_success("Backup deleted!")
                        time.sleep(1)
                        # Adjust selection if we deleted the last item
                        if current_selection >= len(git_manager.get_backup_directories()):
                            current_selection = max(0, len(git_manager.get_backup_directories()) - 1)
                    else:
                        self.show_error("Error deleting backup!")
                        time.sleep(1)

    def edit_gitignore(self) -> bool:
        """Show .gitignore editing interface"""
        self.console.clear()

        gitignore_panel = Panel(
            Group(
                Text("📝 EDIT .GITIGNORE", style=f"bold {LIME_ACCENT}", justify="center"),
                Text(""),
                Text("This feature will open .gitignore with the system editor.", style="white"),
                Text("For now use the file browser to navigate and edit .gitignore.", style=LIME_SECONDARY),
                Text(""),
                Text("Press any key to continue...", style=LIME_SECONDARY, justify="center")
            ),
            title="📝 EDIT GITIGNORE",
            title_align="center",
            border_style=LIME_PRIMARY,
            padding=(1, 2)
        )

        self.console.print(gitignore_panel)
        get_key()
        return False  # Not implemented yet

    def show_log_viewer(self) -> None:
        """Display log viewer with scroll and management options"""
        from ..core.logger import Logger
        from ..core.config_manager import ConfigManager

        config_manager = ConfigManager()
        logger = Logger(config_manager.config)

        current_line = 0
        scroll_offset = 0

        while True:
            self.console.clear()

            # Read log file
            log_lines = []
            log_size = logger.get_log_size()

            try:
                log_path = logger.get_log_path()
                if os.path.exists(log_path):
                    with open(log_path, "r", encoding="utf-8") as f:
                        log_lines = f.readlines()
                else:
                    log_lines = ["No log file found - logging might be disabled"]
            except Exception as e:
                log_lines = [f"Error reading log file: {str(e)}"]

            # Get terminal size for scrolling - optimize for full window usage
            terminal_size = self.console.size
            visible_height = max(1, terminal_size.height - 8)  # Minimal space for header/controls

            # Ensure current_line is within bounds
            if current_line >= len(log_lines) and log_lines:
                current_line = len(log_lines) - 1
            elif current_line < 0:
                current_line = 0

            # Adjust scroll offset to keep current line visible
            if log_lines:
                if current_line < scroll_offset:
                    scroll_offset = current_line
                elif current_line >= scroll_offset + visible_height:
                    scroll_offset = current_line - visible_height + 1

            # Display log content
            log_content = []

            # Compact header with file info in one line
            log_content.append(Text.assemble(
                ("📋 Log: ", f"bold {MAT_PRIMARY}"),
                (f"{os.path.basename(logger.get_log_path())}", MAT_PRIMARY),
                (f" • {log_size}B • {len(log_lines)} lines", MAT_TEXT_HINT)
            ))

            # Display visible log lines
            if not log_lines:
                log_content.append(Text("Log empty or unavailable", style=MAT_TEXT_SECONDARY))
            else:
                for i in range(visible_height):
                    line_idx = i + scroll_offset
                    if line_idx < len(log_lines):
                        line = log_lines[line_idx].rstrip()

                        # Highlight current line
                        if line_idx == current_line:
                            style = f"bold {MAT_BANANA}"
                            prefix = "► "
                        else:
                            style = "white"
                            prefix = "  "

                        # Optimize width usage with shorter line prefix
                        line_prefix = f"{line_idx + 1:3d}:"
                        max_width = terminal_size.width - len(prefix) - len(line_prefix) - 2  # Account for prefix and spacing

                        if len(line) > max_width:
                            line = line[:max_width - 3] + "..."

                        log_content.append(Text(f"{prefix}{line_prefix} {line}", style=style))

            # Scroll info
            if len(log_lines) > visible_height:
                log_content.append(Text(""))
                scroll_info = Text(
                    f"Showing {scroll_offset + 1}-{min(scroll_offset + visible_height, len(log_lines))} of {len(log_lines)}",
                    style=MAT_TEXT_HINT
                )
                log_content.append(scroll_info)

            # Controls - full width separator
            log_content.append(Text(""))
            log_content.append(Text("─" * (terminal_size.width - 4), style=MAT_TEXT_HINT))

            controls_line = Text.assemble(
                ("Navigate ", MAT_TEXT_HINT), ("↑↓", MAT_PRIMARY), ("  ", ""),
                ("FastScroll ", MAT_TEXT_HINT), ("PgUp/Dn", MAT_PRIMARY), ("  ", ""),
                ("Refresh ", MAT_TEXT_HINT), ("r", MAT_ACCENT), ("  ", ""),
                ("Clear Log ", MAT_TEXT_HINT), ("d", "bold red"), ("  ", ""),
                ("Exit ", MAT_TEXT_HINT), ("q", "#F44336")
            )
            log_content.append(controls_line)

            # Display panel
            panel = Panel(
                Group(*log_content),
                title="📋 LOG VIEWER",
                title_align="left",
                border_style=MAT_ACCENT,
                padding=(0, 1)
            )

            self.console.print(panel)

            # Get user input
            key = get_key()

            # Navigation
            if key == KeyCodes.ARROW_UP or key.lower() == 'k':
                if log_lines:
                    current_line = max(0, current_line - 1)
            elif key == KeyCodes.ARROW_DOWN or key.lower() == 'j':
                if log_lines:
                    current_line = min(len(log_lines) - 1, current_line + 1)
            elif key == KeyCodes.PAGE_UP:
                if log_lines:
                    current_line = max(0, current_line - visible_height)
            elif key == KeyCodes.PAGE_DOWN:
                if log_lines:
                    current_line = min(len(log_lines) - 1, current_line + visible_height)

            # Actions
            elif key.lower() == 'r':
                # Refresh - just continue the loop to reload
                continue
            elif key.lower() == 'd':
                # Clear log with confirmation
                if self.confirm("Clear entire log?", False):
                    if logger.clear_log():
                        current_line = 0
                        scroll_offset = 0
                        # Continue loop to refresh display immediately
                    else:
                        info_panel = Panel(
                            Text("Error deleting log file", style="white"),
                            title="❌ Error",
                            border_style="red",
                            padding=(0, 1)
                        )
                        self.console.print(info_panel)
                        get_key()
            elif key.lower() == 'q' or key == KeyCodes.ESC:
                break

    def show_push_status(self, git_manager) -> bool:
        """Show pending push status and offer to push. Returns True if user wants to push."""
        has_remote, commits_ahead, commit_list = git_manager.get_push_status()

        if not has_remote:
            return False  # No remote configured, no action needed

        if commits_ahead == 0:
            return False  # Nothing to push

        # Create push status display
        content = []

        # Header
        content.append(Text(f"🚀 {commits_ahead} commit{'s' if commits_ahead > 1 else ''} ready to push",
                          style=f"bold {MAT_ACCENT}"))
        content.append(Text(""))

        # Show commits to be pushed
        content.append(Text("Commit da inviare:", style=MAT_PRIMARY))
        for commit in commit_list:
            content.append(Text(f"  • {commit}", style=MAT_TEXT_SECONDARY))

        content.append(Text(""))
        content.append(Text(f"Remote: {git_manager.config.remote}", style=MAT_TEXT_HINT))

        # Display panel
        panel = Panel(
            Group(*content),
            title="📤 PUSH STATUS",
            title_align="left",
            border_style=MAT_ACCENT,
            padding=(0, 1)
        )

        self.console.print(panel)

        # Auto push after commit
        return True
