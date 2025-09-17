"""
Git Manager
Handles all Git operations for the dotfiles repository.
"""

import os
import subprocess
import stat
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from .config_manager import ConfigManager
from ..common import Config, FileInfo, GitChange

class GitManager:
    """Manages all Git operations for the dotfiles repository"""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager

    @property
    def config(self) -> Config:
        """Get current configuration"""
        return self.config_manager.config

    def create_backup_before_pull(self) -> Optional[str]:
        """Create backup of files that would be overwritten by pull"""
        try:
            work_tree = os.path.expanduser(self.config.work_tree)

            # First try to fetch latest changes to compare
            self.run_git_command(['fetch', 'origin', 'main'])

            files_to_backup = []

            # Get list of all files that will come from origin/main
            success, stdout, _ = self.run_git_command(['ls-tree', '-r', '--name-only', 'origin/main'])
            if success:
                for line in stdout.split('\n'):
                    line = line.strip()
                    if not line:
                        continue

                    file_path = os.path.join(work_tree, line)
                    # If file exists locally, it might be overwritten
                    if os.path.exists(file_path):
                        files_to_backup.append(line)

            if not files_to_backup:
                return None

            # Create backup directory
            backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(work_tree, '.config', 'dotfiles-manager', 'backup', backup_timestamp)
            os.makedirs(backup_dir, exist_ok=True)

            # Copy files to backup
            backed_up_files = []
            for file_rel_path in files_to_backup:
                source_path = os.path.join(work_tree, file_rel_path)
                backup_path = os.path.join(backup_dir, file_rel_path)

                # Create subdirectories if needed
                backup_file_dir = os.path.dirname(backup_path)
                if backup_file_dir:
                    os.makedirs(backup_file_dir, exist_ok=True)

                try:
                    shutil.copy2(source_path, backup_path)
                    backed_up_files.append(file_rel_path)
                except (OSError, IOError) as e:
                    print(f"Warning: Could not backup {file_rel_path}: {e}")

            if backed_up_files:
                print(f"Created backup of {len(backed_up_files)} files in {backup_dir}")
                return backup_dir

        except Exception as e:
            print(f"Warning: Could not create backup: {e}")

        return None

    def get_backup_directories(self) -> List[Dict[str, Any]]:
        """Get list of all backup directories with metadata"""
        try:
            work_tree = os.path.expanduser(self.config.work_tree)
            backup_base_dir = os.path.join(work_tree, '.config', 'dotfiles-manager', 'backup')

            if not os.path.exists(backup_base_dir):
                return []

            backups = []
            for item in os.listdir(backup_base_dir):
                backup_path = os.path.join(backup_base_dir, item)
                if os.path.isdir(backup_path):
                    try:
                        # Parse timestamp from directory name (YYYYMMDD_HHMMSS)
                        timestamp_str = item
                        timestamp_obj = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

                        # Get directory size and file count
                        total_size = 0
                        file_count = 0
                        for root, dirs, files in os.walk(backup_path):
                            file_count += len(files)
                            for file in files:
                                try:
                                    total_size += os.path.getsize(os.path.join(root, file))
                                except OSError:
                                    pass

                        backups.append({
                            'name': item,
                            'path': backup_path,
                            'timestamp': timestamp_obj,
                            'size': total_size,
                            'file_count': file_count
                        })
                    except ValueError:
                        # Skip directories that don't match timestamp format
                        continue

            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x['timestamp'], reverse=True)
            return backups

        except Exception as e:
            print(f"Error getting backup directories: {e}")
            return []

    def delete_backup(self, backup_name: str) -> bool:
        """Delete a specific backup directory"""
        try:
            work_tree = os.path.expanduser(self.config.work_tree)
            backup_path = os.path.join(work_tree, '.config', 'dotfiles-manager', 'backup', backup_name)

            if os.path.exists(backup_path):
                shutil.rmtree(backup_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting backup {backup_name}: {e}")
            return False

    def get_git_command_base(self) -> List[str]:
        """Get base git command with proper git-dir and work-tree"""
        config = self.config
        git_dir = os.path.expanduser(config.git_dir)
        work_tree = os.path.expanduser(config.work_tree)

        return [
            'git',
            f'--git-dir={git_dir}',
            f'--work-tree={work_tree}'
        ]

    def run_git_command(self, args: List[str], capture_output: bool = True) -> Tuple[bool, str, str]:
        """Run git command and return success, stdout, stderr"""
        command = self.get_git_command_base() + args

        try:
            result = subprocess.run(
                command,
                capture_output=capture_output,
                text=True,
                cwd=os.path.expanduser(self.config.work_tree)
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.SubprocessError as e:
            return False, "", str(e)

    def is_git_repo_initialized(self) -> bool:
        """Check if git repository is initialized"""
        git_dir = os.path.expanduser(self.config.git_dir)
        return os.path.isdir(git_dir) and os.path.exists(os.path.join(git_dir, 'HEAD'))

    def initialize_git_repo(self) -> bool:
        """Initialize bare git repository with complete configuration"""
        config = self.config
        git_dir = os.path.expanduser(config.git_dir)
        work_tree = os.path.expanduser(config.work_tree)

        try:
            # Remove existing git directory if it exists
            if os.path.exists(git_dir):
                import shutil
                shutil.rmtree(git_dir)

            # Create git directory
            os.makedirs(git_dir, exist_ok=True)

            # Initialize bare repository using standard git init --bare command
            result = subprocess.run(
                ['git', 'init', '--bare', git_dir],
                capture_output=True,
                text=True,
                cwd=work_tree
            )
            if result.returncode != 0:
                return False

            # Create gitignore directory structure
            gitignore_dir = os.path.expanduser('~/.config/dotfiles-manager')
            gitignore_path = os.path.join(gitignore_dir, '.gitignore')

            # Create .config/dotfiles-manager directory if it doesn't exist
            os.makedirs(gitignore_dir, exist_ok=True)

            # Create default .gitignore if it doesn't exist
            if not os.path.exists(gitignore_path):
                default_gitignore = """# Default dotfiles manager gitignore patterns

# Temporary files
*~
*.swp
*.swo
.DS_Store
Thumbs.db

# Cache directories
__pycache__/
*.pyc
.cache/

# IDE files
.vscode/
.idea/

# Log files
*.log
"""
                with open(gitignore_path, 'w') as f:
                    f.write(default_gitignore)

            # Set up essential git configuration for bare repository using direct git commands
            git_config_commands = [
                (['git', '-C', git_dir, 'config', 'status.showUntrackedFiles', 'no'], "Hide untracked files"),
                (['git', '-C', git_dir, 'config', 'core.worktree', work_tree], "Configure work tree"),
                (['git', '-C', git_dir, 'config', 'core.excludesfile', gitignore_path], "Configure global gitignore")
            ]

            for cmd_args, description in git_config_commands:
                result = subprocess.run(cmd_args, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"Warning: Failed to {description}: {result.stderr}")

            # Add remote if specified
            if config.remote:
                success, _, _ = self.run_git_command(['remote', 'add', 'origin', config.remote])
                if not success:
                    print(f"Warning: Failed to add remote origin")
                else:
                    # Set upstream for main branch if remote was added successfully
                    self._setup_upstream_tracking()

            return True

        except Exception as e:
            print(f"Error during git repository initialization: {e}")
            return False

    def get_file_git_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get git information for a specific file"""
        if not self.is_git_repo_initialized():
            return None

        # Make path relative to work tree
        work_tree = os.path.expanduser(self.config.work_tree)
        if file_path.startswith(work_tree):
            rel_path = os.path.relpath(file_path, work_tree)
        else:
            rel_path = file_path

        # Get file status
        success, stdout, _ = self.run_git_command(['status', '--porcelain', '--', rel_path])
        if not success:
            return None

        status_info = {'path': rel_path, 'status': 'untracked'}

        if stdout.strip():
            line = stdout.strip().split('\n')[0]
            if len(line) >= 3:
                staged = line[0] if line[0] != ' ' else ''
                worktree = line[1] if line[1] != ' ' else ''
                status_info['status'] = f"{staged}{worktree}"
        else:
            # File might be tracked but unchanged
            success, _, _ = self.run_git_command(['ls-files', '--', rel_path])
            if success:
                status_info['status'] = 'tracked'

        return status_info

    def get_tracked_files_info(self) -> List[FileInfo]:
        """Get information about all tracked files"""
        if not self.is_git_repo_initialized():
            return []

        files_info = []
        work_tree = os.path.expanduser(self.config.work_tree)

        # Get list of tracked files
        success, stdout, _ = self.run_git_command(['ls-files'])
        if not success:
            return []

        tracked_files = [line.strip() for line in stdout.split('\n') if line.strip()]

        for rel_path in tracked_files:
            full_path = os.path.join(work_tree, rel_path)

            try:
                stat_info = os.stat(full_path)
                file_info = FileInfo(
                    path=rel_path,
                    status='tracked',
                    size=stat_info.st_size,
                    mtime=stat_info.st_mtime,
                    is_dir=stat.S_ISDIR(stat_info.st_mode)
                )

                # Get detailed status
                git_info = self.get_file_git_info(full_path)
                if git_info:
                    file_info.status = git_info['status']

                files_info.append(file_info)

            except (OSError, IOError):
                # File might be deleted, still include it
                file_info = FileInfo(
                    path=rel_path,
                    status='deleted',
                    size=0,
                    mtime=0
                )
                files_info.append(file_info)

        return files_info

    def get_current_changes(self) -> List[GitChange]:
        """Get current changes (staged and unstaged)"""
        if not self.is_git_repo_initialized():
            return []

        changes = []

        # Get status with porcelain format
        success, stdout, _ = self.run_git_command(['status', '--porcelain'])
        if not success:
            return []

        for line in stdout.split('\n'):
            line = line.strip()
            if not line:
                continue

            if len(line) >= 3:
                staged = line[0] if line[0] != ' ' else ''
                worktree = line[1] if line[1] != ' ' else ''
                file_path = line[3:]  # Skip the first 3 characters (XY filename)

                change_info = GitChange(
                    file=file_path,
                    staged=staged,
                    worktree=worktree,
                    status_code=f"{staged}{worktree}"
                )
                changes.append(change_info)

        return changes

    def is_file_tracked(self, file_path: str) -> bool:
        """Check if a file is tracked by git"""
        if not self.is_git_repo_initialized():
            return False

        work_tree = os.path.expanduser(self.config.work_tree)

        # Convert to relative path
        if file_path.startswith(work_tree):
            rel_path = os.path.relpath(file_path, work_tree)
        else:
            rel_path = file_path

        # Use git ls-files to check if file is tracked
        success, stdout, _ = self.run_git_command(['ls-files', '--', rel_path])
        return success and stdout.strip() != ""

    def add_single_file(self, file_path: str) -> bool:
        """Add a single file to git repository"""
        if not self.is_git_repo_initialized():
            return False

        work_tree = os.path.expanduser(self.config.work_tree)

        # Convert to relative path
        if file_path.startswith(work_tree):
            rel_path = os.path.relpath(file_path, work_tree)
        else:
            rel_path = file_path

        # Check if file exists
        full_path = os.path.join(work_tree, rel_path) if not os.path.isabs(file_path) else file_path
        if not os.path.exists(full_path):
            return False

        success, _, _ = self.run_git_command(['add', rel_path])
        return success

    def remove_single_file(self, file_path: str) -> bool:
        """Remove a single file from git repository (but keep in filesystem)"""
        if not self.is_git_repo_initialized():
            return False

        work_tree = os.path.expanduser(self.config.work_tree)

        # Convert to relative path
        if file_path.startswith(work_tree):
            rel_path = os.path.relpath(file_path, work_tree)
        else:
            rel_path = file_path

        # Use git rm --cached to remove from tracking but keep file
        success, _, _ = self.run_git_command(['rm', '--cached', rel_path])
        return success

    def add_files(self, file_paths: List[str]) -> Tuple[bool, List[str], Dict[str, str]]:
        """Add files to git repository

        Returns:
            tuple: (success: bool, success_files: List[str], failed_files: Dict[str, str])
                   failed_files maps file_path to error_message
        """
        if not file_paths:
            return True, [], {}

        # Verify git repository is initialized
        if not self.is_git_repo_initialized():
            print("Error: Git repository not initialized")
            return False, [], {"repository": "Git repository not initialized"}

        # Verify git configuration is correct
        config_valid, issues = self.verify_git_configuration()
        if not config_valid:
            print(f"Warning: Git configuration issues detected: {', '.join(issues)}")

        success_files = []
        failed_files = {}
        work_tree = os.path.expanduser(self.config.work_tree)

        for file_path in file_paths:
            # Convert to relative path
            if file_path.startswith(work_tree):
                rel_path = os.path.relpath(file_path, work_tree)
            else:
                rel_path = file_path

            # Check if file exists
            full_path = os.path.join(work_tree, rel_path) if not os.path.isabs(file_path) else file_path
            if not os.path.exists(full_path):
                error_msg = f"File does not exist: {full_path}"
                print(f"Warning: {error_msg}")
                failed_files[file_path] = error_msg
                continue

            success, stdout, stderr = self.run_git_command(['add', rel_path])
            if success:
                success_files.append(file_path)  # Use original path, not rel_path
                print(f"Added: {rel_path}")
            else:
                error_msg = stderr.strip() if stderr else "Unknown git add error"
                failed_files[file_path] = error_msg
                print(f"Error adding {rel_path}: {error_msg}")

        # Report results
        if success_files:
            print(f"Successfully added {len(success_files)} files")
        if failed_files:
            print(f"Failed to add {len(failed_files)} files: {', '.join([os.path.basename(f) for f in failed_files.keys()])}")

        return len(success_files) > 0, success_files, failed_files

    def commit_changes(self, message: str) -> bool:
        """Commit staged changes"""
        if not message.strip():
            return False

        success, _, _ = self.run_git_command(['commit', '-m', message])
        return success

    def generate_commit_message(self, changes: List[GitChange]) -> str:
        """Generate automatic commit message based on changes"""
        if not changes:
            return "update: dotfiles configuration"

        # Categorize changes
        added = [c for c in changes if c.staged == 'A']
        modified = [c for c in changes if c.staged == 'M']
        deleted = [c for c in changes if c.staged == 'D']
        renamed = [c for c in changes if c.staged == 'R']

        parts = []
        if added:
            if len(added) == 1:
                parts.append(f"add {os.path.basename(added[0].file)}")
            else:
                parts.append(f"add {len(added)} files")

        if modified:
            if len(modified) == 1:
                parts.append(f"update {os.path.basename(modified[0].file)}")
            else:
                parts.append(f"update {len(modified)} files")

        if deleted:
            if len(deleted) == 1:
                parts.append(f"remove {os.path.basename(deleted[0].file)}")
            else:
                parts.append(f"remove {len(deleted)} files")

        if renamed:
            if len(renamed) == 1:
                parts.append(f"rename {os.path.basename(renamed[0].file)}")
            else:
                parts.append(f"rename {len(renamed)} files")

        if parts:
            return ", ".join(parts)
        else:
            return "update dotfiles"

    def parse_git_status_code(self, staged: str, worktree: str) -> Tuple[str, str]:
        """Parse git status codes into readable format"""
        status_map = {
            'A': 'Added', 'M': 'Modified', 'D': 'Deleted', 'R': 'Renamed',
            'C': 'Copied', 'U': 'Updated', '?': 'Untracked', '!': 'Ignored'
        }

        staged_desc = status_map.get(staged, 'Unknown') if staged else ''
        worktree_desc = status_map.get(worktree, 'Unknown') if worktree else ''

        return staged_desc, worktree_desc

    def verify_git_configuration(self) -> Tuple[bool, List[str]]:
        """Verify that all required git configurations are properly set"""
        if not self.is_git_repo_initialized():
            return False, ["Git repository not initialized"]

        issues = []
        config = self.config
        work_tree = os.path.expanduser(config.work_tree)
        gitignore_path = os.path.expanduser('~/.config/dotfiles-manager/.gitignore')

        # Check essential configurations
        checks = [
            ('status.showUntrackedFiles', 'no'),
            ('core.worktree', work_tree),
            ('core.excludesfile', gitignore_path)
        ]

        for config_key, expected_value in checks:
            success, stdout, _ = self.run_git_command(['config', '--local', config_key])
            if not success:
                issues.append(f"Missing configuration: {config_key}")
            elif stdout.strip() != expected_value:
                issues.append(f"Incorrect {config_key}: expected '{expected_value}', got '{stdout.strip()}'")

        # Check if .gitignore exists
        if not os.path.exists(gitignore_path):
            issues.append(f"Global .gitignore not found at {gitignore_path}")

        return len(issues) == 0, issues

    def push_changes(self) -> bool:
        """Push committed changes to remote repository"""
        if not self.is_git_repo_initialized():
            return False

        success, _, _ = self.run_git_command(['push', 'origin', 'main'])
        return success

    def get_push_status(self) -> tuple[bool, int, list]:
        """Get push status - returns (has_remote, commits_ahead, commit_list)"""
        if not self.is_git_repo_initialized():
            return False, 0, []

        # Check if remote is configured
        if not self.config.remote:
            return False, 0, []

        # Check if we have any commits
        has_commits, _, _ = self.run_git_command(['rev-parse', 'HEAD'])
        if not has_commits:
            return True, 0, []

        # Get commits ahead of remote
        success, output, _ = self.run_git_command(['rev-list', '--count', 'HEAD', '--not', '--remotes'])
        if not success:
            # If command fails, try to fetch and check again
            self.run_git_command(['fetch', 'origin'])
            success, output, _ = self.run_git_command(['rev-list', '--count', 'HEAD', '--not', '--remotes'])
            if not success:
                return True, 0, []

        try:
            commits_ahead = int(output.strip())
        except (ValueError, AttributeError):
            commits_ahead = 0

        commit_list = []
        if commits_ahead > 0:
            # Get list of commits to push
            success, commit_output, _ = self.run_git_command([
                'log', '--oneline', f'HEAD~{commits_ahead}..HEAD'
            ])
            if success and commit_output:
                commit_list = [line.strip() for line in commit_output.strip().split('\n') if line.strip()]

        return True, commits_ahead, commit_list

    def get_pull_status(self) -> tuple[bool, int, list]:
        """Get pull status - returns (has_remote, commits_behind, commit_list)"""
        if not self.is_git_repo_initialized():
            return False, 0, []

        # Check if remote is configured
        if not self.config.remote:
            return False, 0, []

        # Check if we have any commits
        has_commits, _, _ = self.run_git_command(['rev-parse', 'HEAD'])
        if not has_commits:
            return True, 0, []

        # Fetch latest from remote first
        self.run_git_command(['fetch', 'origin'])

        # Get commits behind remote
        success, output, _ = self.run_git_command(['rev-list', '--count', '--remotes', '--not', 'HEAD'])
        if not success:
            return True, 0, []

        try:
            commits_behind = int(output.strip())
        except (ValueError, AttributeError):
            commits_behind = 0

        commit_list = []
        if commits_behind > 0:
            # Get list of commits to pull
            success, commit_output, _ = self.run_git_command([
                'log', '--oneline', f'HEAD..origin/main'
            ])
            if success and commit_output:
                commit_list = [line.strip() for line in commit_output.strip().split('\n') if line.strip()]

        return True, commits_behind, commit_list

    def pull_changes(self) -> bool:
        """Pull changes from remote repository"""
        if not self.is_git_repo_initialized():
            return False

        # Check if remote origin exists
        remote_exists, _, _ = self.run_git_command(['remote', 'get-url', 'origin'])
        if not remote_exists:
            return False

        # Check if repository has any commits
        has_commits, _, _ = self.run_git_command(['rev-parse', 'HEAD'])

        if not has_commits:
            # Repository is empty, do initial pull to create main branch
            success, _, stderr = self.run_git_command(['pull', 'origin', 'main'])
            overwrite_keywords = [
                "sarebbero sovrascritti dal merge",
                "would be overwritten by merge",
                "would be overwritten by checkout",
                "untracked working tree files would be overwritten",
                "The following untracked working tree files would be overwritten"
            ]
            has_overwrite_error = any(keyword in stderr.lower() for keyword in overwrite_keywords)

            if not success and has_overwrite_error:
                # Untracked files would be overwritten, create backup first
                backup_dir = self.create_backup_before_pull()
                if backup_dir:
                    print(f"📦 Existing files saved to backup: {backup_dir}")

                # Fetch and force checkout
                fetch_success, _, _ = self.run_git_command(['fetch', 'origin', 'main'])
                if fetch_success:
                    # Create and checkout main branch pointing to origin/main, forcing overwrite
                    success, _, _ = self.run_git_command(['checkout', '-b', 'main', 'origin/main', '--force'])

            if success:
                # Set upstream tracking after successful initial pull/checkout
                self.run_git_command(['branch', '--set-upstream-to=origin/main', 'main'])
            return success

        # Try pull with upstream first
        success, _, stderr = self.run_git_command(['pull'])

        if not success and "no tracking information" in stderr.lower():
            # No upstream configured, try with --set-upstream
            success, _, stderr = self.run_git_command(['pull', '--set-upstream', 'origin', 'main'])
            if success:
                # Also set the upstream tracking for future operations
                self.run_git_command(['branch', '--set-upstream-to=origin/main', 'main'])
        elif not success:
            # Check if files would be overwritten
            overwrite_keywords = [
                "sarebbero sovrascritti dal merge",
                "would be overwritten by merge",
                "would be overwritten by checkout",
                "untracked working tree files would be overwritten",
                "The following untracked working tree files would be overwritten"
            ]
            has_overwrite_error = any(keyword in stderr.lower() for keyword in overwrite_keywords)

            if has_overwrite_error:
                print(f"🔍 Detected overwrite error: {stderr}")
                # Create backup before forcing pull
                backup_dir = self.create_backup_before_pull()
                if backup_dir:
                    print(f"📦 Existing files saved to backup: {backup_dir}")

                # Force pull by stashing local changes temporarily
                print("🔄 Stashing untracked files...")
                self.run_git_command(['stash', '--include-untracked'])
                print("🔄 Attempting pull...")
                success, _, _ = self.run_git_command(['pull', 'origin', 'main'])
                print(f"✅ Pull result: {success}")
                # Don't restore stash to avoid conflicts
            else:
                # Try explicit pull if simple pull failed for other reasons
                success, _, _ = self.run_git_command(['pull', 'origin', 'main'])

        return success

    def unstage_all_changes(self) -> bool:
        """Remove all changes from staging area"""
        if not self.is_git_repo_initialized():
            return False

        # Get list of staged files first
        changes = self.get_current_changes()
        staged_files = [change.file for change in changes if change.staged and change.staged != ' ']

        if not staged_files:
            return True  # Nothing to unstage

        # Check if repository has any commits
        has_commits, _, _ = self.run_git_command(['rev-parse', 'HEAD'])
        if not has_commits:
            # If no commits exist, use git rm --cached for each staged file
            work_tree = os.path.expanduser(self.config.work_tree)
            rel_paths = []
            for file_path in staged_files:
                if file_path.startswith(work_tree):
                    rel_path = os.path.relpath(file_path, work_tree)
                else:
                    rel_path = file_path
                rel_paths.append(rel_path)

            if rel_paths:
                success, _, _ = self.run_git_command(['rm', '--cached'] + rel_paths)
                return success
            return True
        else:
            success, _, _ = self.run_git_command(['reset', 'HEAD'])
            return success

    def unstage_single_file(self, file_path: str) -> bool:
        """Remove a single file from staging area"""
        if not self.is_git_repo_initialized():
            return False

        work_tree = os.path.expanduser(self.config.work_tree)

        # Convert to relative path
        if file_path.startswith(work_tree):
            rel_path = os.path.relpath(file_path, work_tree)
        else:
            rel_path = file_path

        # Check if repository has any commits
        has_commits, _, _ = self.run_git_command(['rev-parse', 'HEAD'])
        if not has_commits:
            # If no commits exist, use git rm --cached to unstage
            success, _, _ = self.run_git_command(['rm', '--cached', rel_path])
            return success
        else:
            success, _, _ = self.run_git_command(['reset', 'HEAD', rel_path])
            return success

    def unstage_multiple_files(self, file_paths: List[str]) -> bool:
        """Remove multiple files from staging area"""
        if not self.is_git_repo_initialized():
            return False

        if not file_paths:
            return True

        work_tree = os.path.expanduser(self.config.work_tree)
        rel_paths = []

        # Convert all paths to relative paths
        for file_path in file_paths:
            if file_path.startswith(work_tree):
                rel_path = os.path.relpath(file_path, work_tree)
            else:
                rel_path = file_path
            rel_paths.append(rel_path)

        # Check if repository has any commits
        has_commits, _, _ = self.run_git_command(['rev-parse', 'HEAD'])
        if not has_commits:
            # If no commits exist, use git rm --cached to unstage
            success, _, _ = self.run_git_command(['rm', '--cached'] + rel_paths)
            return success
        else:
            # Run git reset for all files at once
            success, _, _ = self.run_git_command(['reset', 'HEAD'] + rel_paths)
            return success

    def get_git_status_info(self) -> Dict[str, Any]:
        """Get comprehensive git status information"""
        if not self.is_git_repo_initialized():
            return {"initialized": False, "error": "Repository not initialized"}

        info = {
            "initialized": True,
            "configurations": {},
            "remote": None,
            "tracked_files_count": 0,
            "changes_count": 0
        }

        # Get configurations
        config_keys = ['status.showUntrackedFiles', 'core.worktree', 'core.excludesfile']
        for key in config_keys:
            success, value, _ = self.run_git_command(['config', '--local', key])
            info["configurations"][key] = value.strip() if success else "Not set"

        # Get remote info
        success, remotes, _ = self.run_git_command(['remote', '-v'])
        if success and remotes.strip():
            info["remote"] = remotes.strip().split('\n')[0]

        # Get file counts
        tracked_files = self.get_tracked_files_info()
        changes = self.get_current_changes()
        info["tracked_files_count"] = len(tracked_files)
        info["changes_count"] = len(changes)

        return info

    def _setup_upstream_tracking(self) -> bool:
        """Set up upstream tracking for main branch to origin/main"""
        try:
            # Check if repository has any commits
            has_commits, _, _ = self.run_git_command(['rev-parse', 'HEAD'])

            if not has_commits:
                # No commits yet - just set the upstream configuration
                # This will be used when the first push happens
                success, _, _ = self.run_git_command(['config', 'branch.main.remote', 'origin'])
                if success:
                    success, _, _ = self.run_git_command(['config', 'branch.main.merge', 'refs/heads/main'])
                return success

            # Check if main branch exists
            success, _, _ = self.run_git_command(['show-ref', '--verify', '--quiet', 'refs/heads/main'])
            if not success:
                # Create main branch if it doesn't exist
                success, _, _ = self.run_git_command(['checkout', '-b', 'main'])
                if not success:
                    return False

            # Set upstream tracking for both push and pull
            success, _, _ = self.run_git_command(['push', '--set-upstream', 'origin', 'main'])
            if success:
                # Set upstream tracking for pull operations
                success, _, _ = self.run_git_command(['branch', '--set-upstream-to=origin/main', 'main'])
            return success
        except Exception:
            return False

    def update_remote_origin(self, remote_url: str) -> bool:
        """Update or add remote origin with the given URL"""
        if not self.is_git_repo_initialized():
            return False

        try:
            # Check if origin remote exists
            success, _, _ = self.run_git_command(['remote', 'get-url', 'origin'])

            if success:
                # Remote exists, update it
                success, _, _ = self.run_git_command(['remote', 'set-url', 'origin', remote_url])
                if success:
                    # Set upstream tracking after updating remote
                    self._setup_upstream_tracking()
                return success
            else:
                # Remote doesn't exist, add it
                success, _, _ = self.run_git_command(['remote', 'add', 'origin', remote_url])
                if success:
                    # Set upstream tracking after adding remote
                    self._setup_upstream_tracking()
                return success

        except Exception as e:
            print(f"Error updating remote: {e}")
            return False

    def remove_remote_origin(self) -> bool:
        """Remove remote origin"""
        if not self.is_git_repo_initialized():
            return False

        try:
            # Check if origin exists first
            success, _, _ = self.run_git_command(['remote', 'get-url', 'origin'])
            if success:
                # Remove origin remote
                success, _, _ = self.run_git_command(['remote', 'remove', 'origin'])
                return success
            return True  # Already doesn't exist

        except Exception as e:
            print(f"Error removing remote: {e}")
            return False