"""
Main Application
Coordinates all components and manages the application lifecycle.
"""

import os
import time
from typing import Optional

from .core.config_manager import ConfigManager
from .core.git_manager import GitManager
from .core.file_manager import FileManager
from .core.logger import Logger
from .interfaces.ui_interface import UIInterface
from .ui.rich_ui import RichUI

class DotfilesApp:
    """Main application coordinator"""

    def __init__(self, ui: Optional[UIInterface] = None):
        # Core managers
        self.config_manager = ConfigManager()
        self.logger = Logger(self.config_manager.config)
        self.git_manager = GitManager(self.config_manager)
        self.file_manager = FileManager(self.config_manager)

        # UI implementation (default to RichUI)
        self.ui = ui if ui is not None else RichUI()

    def run(self):
        """Main application loop"""
        if not self.ui.initialize():
            print("Failed to initialize UI system")
            return

        try:
            while True:
                choice = self.ui.show_main_menu()

                if choice == "1":  # Browse Files
                    self._handle_file_browser()

                elif choice == "2":  # Modified Files
                    self._handle_modified_files()

                elif choice == "3":  # Tracked Files
                    self._handle_tracked_files()

                elif choice == "4":  # Settings
                    self._handle_settings()

                elif choice == "5":  # Exit
                    break

        except KeyboardInterrupt:
            pass  # Exit silently on Ctrl+C
        except Exception as e:
            self.ui.show_error(f"Unexpected error: {e}")
        finally:
            self.ui.cleanup()

    def _handle_file_browser(self):
        """Handle file browser functionality"""
        selected_files = self.ui.show_file_browser()
        if selected_files:
            self.ui.show_progress("Adding files to repository")

            # Check if git repo is initialized
            if not self.git_manager.is_git_repo_initialized():
                error_msg = "Git repository not initialized! Go to Settings to initialize it."
                self.ui.show_error(error_msg)
                self.logger.log_error(Exception("Git Add FAILED: Repository not initialized"), "git_add")
                self.logger.log_info("SOLUTION: Go to Settings → Initialize Git Repo to set up the repository", "git_add")
                return

            try:
                success, added_files, failed_files = self.git_manager.add_files(selected_files)

                if success:
                    if len(added_files) == len(selected_files):
                        self.ui.show_success(f"Added all {len(added_files)} files to repository!")
                        self.logger.log_info(f"Git Add SUCCESS: Added {len(added_files)} files to repository", "git_add")
                        self.logger.log_info(f"Files added: {', '.join([os.path.basename(f) for f in added_files])}", "git_add")
                    else:
                        failed_count = len(failed_files)
                        self.ui.show_success(f"Added {len(added_files)} files to repository!")
                        self.ui.show_error(f"Error with {failed_count} files - check details above")

                        # Log partial failure with detailed info for each failed file
                        self.logger.log_error(Exception(f"Git Add PARTIAL FAILURE: {failed_count} files failed to add"), "git_add")
                        self.logger.log_info(f"Successfully added files: {', '.join([os.path.basename(f) for f in added_files])}", "git_add")

                        # Log each failed file with its specific error
                        for file_path, error_msg in failed_files.items():
                            self.logger.log_error(Exception(f"{os.path.basename(file_path)}: {error_msg}"), "git_add")
                    time.sleep(2)
                else:
                    self.ui.show_error("Error adding files - check details above")
                    self.logger.log_error(Exception(f"Git Add COMPLETE FAILURE: Failed to add all {len(selected_files)} files"), "git_add")

                    # Log each failed file with its specific error
                    for file_path, error_msg in failed_files.items():
                        self.logger.log_error(Exception(f"{os.path.basename(file_path)}: {error_msg}"), "git_add")
                    time.sleep(2)
            except Exception as e:
                self.ui.show_error(f"Unexpected error during addition: {str(e)}")
                self.logger.log_error(Exception(f"Git Add UNEXPECTED ERROR: {str(e)}"), "git_add")
                self.logger.log_info(f"Attempted files: {', '.join(selected_files)}", "git_add")
                self.logger.log_info("SOLUTION: Check system permissions, disk space, and git installation", "git_add")
                time.sleep(2)

    def _handle_modified_files(self):
        """Handle modified files display and actions"""
        while True:
            changes = self.git_manager.get_current_changes()
            result = self.ui.show_modified_files(changes)

            if not result:
                # User pressed 'q' - exit to main menu
                break

            action = result.get("action")

            if action == "commit":
                message = result.get("message", "update dotfiles")
                self.ui.show_progress("Executing commit")
                try:
                    if self.git_manager.commit_changes(message):
                        self.ui.show_success("Commit completed successfully!")
                        self.logger.log_info(f"Commit successful: {message}", "commit")
                        time.sleep(1.5)

                        # Check if there are commits to push
                        if self.ui.show_push_status(self.git_manager):
                            self.ui.show_progress("Executing push")
                            if self.git_manager.push_changes():
                                self.ui.show_success("Push completed successfully!")
                                time.sleep(1.5)
                            else:
                                self.ui.show_error("Error during push!")
                                time.sleep(1.5)

                        # Continue loop to refresh the list
                    else:
                        self.ui.show_error("Error during commit!")
                        self.logger.log_error(Exception("Commit failed"), "commit")
                        time.sleep(1.5)
                except Exception as e:
                    self.ui.show_error(f"Error during commit: {str(e)}")
                    self.logger.log_error(e, "commit")
                    time.sleep(1.5)

            elif action == "push":
                self.ui.show_progress("Executing push")
                try:
                    if self.git_manager.push_changes():
                        self.ui.show_success("Push completed successfully!")
                        self.logger.log_info("Push successful to remote repository", "push")
                        time.sleep(1.5)
                        # Continue loop to refresh the list
                    else:
                        self.ui.show_error("Error during push!")
                        self.logger.log_error(Exception("Push failed"), "push")
                        time.sleep(1.5)
                except Exception as e:
                    self.ui.show_error(f"Error during push: {str(e)}")
                    self.logger.log_error(e, "push")
                    time.sleep(1.5)

            elif action == "pull":
                self.ui.show_progress("Executing pull")
                try:
                    if self.git_manager.pull_changes():
                        self.ui.show_success("Pull completed successfully!")
                        self.logger.log_info("Pull successful from remote repository", "pull")
                        time.sleep(1.5)
                        # Continue loop to refresh the list
                    else:
                        self.ui.show_error("Error during pull!")
                        self.logger.log_error(Exception("Pull failed"), "pull")
                        time.sleep(1.5)
                except Exception as e:
                    self.ui.show_error(f"Error during pull: {str(e)}")
                    self.logger.log_error(e, "pull")
                    time.sleep(1.5)

            elif action == "unstage_all":
                self.ui.show_progress("Removing from staging")
                if self.git_manager.unstage_all_changes():
                    self.ui.show_success("Changes removed from staging!")
                    time.sleep(1.5)
                    # Continue loop to refresh the list
                else:
                    self.ui.show_error("Error removing from staging!")
                    time.sleep(1.5)

            elif action == "unstage_file":
                file_path = result.get("file")
                if file_path:
                    self.ui.show_progress(f"Removing {file_path} from staging")
                    if self.git_manager.unstage_single_file(file_path):
                        self.ui.show_success(f"File '{file_path}' removed from staging!")
                        time.sleep(1.5)
                        # Continue loop to refresh the list
                    else:
                        self.ui.show_error(f"Error removing '{file_path}' from staging!")
                        time.sleep(1.5)

            elif action == "unstage_files":
                file_paths = result.get("files", [])
                if file_paths:
                    self.ui.show_progress(f"Removing {len(file_paths)} files from staging")
                    if self.git_manager.unstage_multiple_files(file_paths):
                        self.ui.show_success(f"{len(file_paths)} files removed from staging!")
                        time.sleep(1.5)
                        # Continue loop to refresh the list
                    else:
                        self.ui.show_error("Error removing files from staging!")
                        time.sleep(1.5)

    def _handle_tracked_files(self):
        """Handle tracked files display"""
        files = self.git_manager.get_tracked_files_info()
        self.ui.show_tracked_files(files)

    def _handle_settings(self):
        """Handle settings menu"""
        while True:
            choice = self.ui.show_settings_menu()

            if choice == "1":  # Edit Settings
                self._edit_settings()
            elif choice == "2":  # Initialize Repository
                self._initialize_repository()
            elif choice == "3":  # Edit .gitignore
                self._edit_gitignore()
            elif choice == "4":  # Manage Backup
                self._manage_backup()
            elif choice == "5":  # View Log (if logging enabled) or Return to Menu
                if self.config_manager.config.enable_logging:
                    self.ui.show_log_viewer()
                else:
                    # This is "Return to Menu" when logging is disabled
                    break
            elif choice == "6":  # Return to Menu (when logging enabled)
                break

    def _edit_settings(self):
        """Edit application settings"""
        config = self.config_manager.config
        current_config = config.to_dict()
        old_logging_enabled = config.enable_logging

        new_config = self.ui.edit_settings(current_config)
        if new_config:
            # Store old remote for comparison
            old_remote = current_config.get('remote', '')
            new_remote = new_config.get('remote', '')

            if self.config_manager.update_config(**new_config):
                # Update git remote if it changed and git repo is initialized
                if old_remote != new_remote and self.git_manager.is_git_repo_initialized():
                    if new_remote:
                        # Add or update remote origin
                        if self.git_manager.update_remote_origin(new_remote):
                            self.logger.log_info(f"Remote origin updated to: {new_remote}", "settings")
                        else:
                            self.logger.log_error(Exception("Failed to update remote origin"), "settings")
                    else:
                        # Remove remote origin if empty
                        if self.git_manager.remove_remote_origin():
                            self.logger.log_info("Remote origin removed", "settings")
                        else:
                            self.logger.log_error(Exception("Failed to remove remote origin"), "settings")

                # Check if logging was just enabled
                new_logging_enabled = new_config.get('enable_logging', False)
                if not old_logging_enabled and new_logging_enabled:
                    # Logging was just enabled - create new logger and log the event
                    from .core.logger import Logger
                    new_logger = Logger(self.config_manager.config)
                    new_logger.log_info("Logging enabled by user", "settings")
                    self.logger = new_logger  # Update app logger instance

                self.ui.show_success("Configuration saved!")
                time.sleep(1)
            else:
                self.ui.show_error("Error saving configuration!")

    def _initialize_repository(self):
        """Initialize git repository with detailed interface"""
        config = self.config_manager.config.to_dict()

        # Show detailed initialization interface
        if self.ui.initialize_git_repo_detailed(config):
            self.ui.show_progress("Initializing Git repository")
            if self.git_manager.initialize_git_repo():
                self.ui.show_success("Repository initialized successfully!")
                time.sleep(1.5)
            else:
                self.ui.show_error("Error during initialization!")

    def _edit_gitignore(self):
        """Edit .gitignore file"""
        self.ui.edit_gitignore()

    def _manage_backup(self):
        """Manage backup files"""
        self.ui.show_backup_manager()