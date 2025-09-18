"""
Pytest configuration and shared fixtures
"""

import os
import tempfile
import shutil
import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from dotfiles_manager.core.config_manager import ConfigManager
from dotfiles_manager.core.git_manager import GitManager
from dotfiles_manager.core.file_manager import FileManager
from dotfiles_manager.common import Config


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_home(temp_dir):
    """Create a temporary home directory structure"""
    home_path = os.path.join(temp_dir, "home")
    os.makedirs(home_path, exist_ok=True)

    # Create some fake dotfiles
    dotfiles = [
        ".bashrc",
        ".vimrc",
        ".gitconfig",
        ".config/alacritty/alacritty.yml",
        ".config/wayfire/wayfire.ini"
    ]

    for dotfile in dotfiles:
        file_path = os.path.join(home_path, dotfile)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(f"# Test content for {dotfile}\n")

    return home_path


@pytest.fixture
def temp_git_dir(temp_dir):
    """Create a temporary git directory"""
    git_path = os.path.join(temp_dir, ".dotfiles.git")
    os.makedirs(git_path, exist_ok=True)
    return git_path


@pytest.fixture
def test_config(temp_home, temp_git_dir):
    """Create a test configuration"""
    return Config(
        git_dir=temp_git_dir,
        work_tree=temp_home,
        remote="https://github.com/test/dotfiles.git",
        enable_logging=True
    )


@pytest.fixture
def config_manager(temp_dir, test_config):
    """Create a ConfigManager instance for testing"""
    config_file = os.path.join(temp_dir, "test_config.json")

    manager = ConfigManager(config_file)
    manager._config = test_config
    manager.save_config()
    yield manager


@pytest.fixture
def git_manager(config_manager):
    """Create a GitManager instance for testing"""
    return GitManager(config_manager)


@pytest.fixture
def file_manager(config_manager):
    """Create a FileManager instance for testing"""
    return FileManager(config_manager)


@pytest.fixture
def mock_subprocess():
    """Mock subprocess for git commands"""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = ""
        yield mock_run


@pytest.fixture
def isolated_test_env(temp_dir):
    """Ensure tests don't affect the actual user environment"""
    # Store original environment
    original_home = os.environ.get('HOME')
    original_config_home = os.environ.get('XDG_CONFIG_HOME')

    # Set test environment
    test_home = os.path.join(temp_dir, "test_home")
    test_config = os.path.join(temp_dir, "test_config")
    os.makedirs(test_home, exist_ok=True)
    os.makedirs(test_config, exist_ok=True)

    os.environ['HOME'] = test_home
    os.environ['XDG_CONFIG_HOME'] = test_config

    yield {
        'home': test_home,
        'config': test_config
    }

    # Restore original environment
    if original_home:
        os.environ['HOME'] = original_home
    if original_config_home:
        os.environ['XDG_CONFIG_HOME'] = original_config_home
    else:
        os.environ.pop('XDG_CONFIG_HOME', None)