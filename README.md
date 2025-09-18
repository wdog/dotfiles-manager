# 🐉 Dotfiles Manager

A powerful Python-based TUI (Terminal User Interface) application for managing your dotfiles files with git integration. Fully translated English interface with robust input handling for both interactive and automated environments.

## ✨ Features

- **🎨 Rich Terminal UI** - Beautiful interface with lime color theme and emoji icons
- **📁 File Browser** - Navigate and select configuration files with multi-selection support
- **🔄 Git Integration** - Full git workflow with bare repository support for dotfiles
- **🛡️ Backup System** - Automatic backup creation before pull conflicts
- **⚙️ Settings Management** - Easy configuration editing with compact form-style interface
- **📋 File Tracking** - View tracked files and current repository status
- **🚀 Quick Operations** - Fast commit, push, pull operations with y/n confirmations
- **🌍 English Interface** - Complete English translation with consistent terminology
- **🤖 Automation Ready** - Robust input handling for scripted environments

## 🏗️ Architecture

The application follows a modular, extensible design:

```
dotfiles_manager/
├── app.py              # Main application coordinator
├── core/               # Business logic layer
│   ├── config_manager.py   # Configuration management
│   ├── git_manager.py      # Git operations
│   ├── file_manager.py     # File system operations
│   └── logger.py           # Error and info logging
├── ui/                 # User interface layer
│   └── rich_ui.py          # Rich-based TUI implementation
├── interfaces/         # Abstract interfaces
│   └── ui_interface.py     # UI interface for extensibility
└── common.py           # Shared constants and types
```

## 🚀 Getting Started

### Prerequisites

- Python 3.7+
- Git
- Linux/Unix system (tested on Linux)

### 1. Clone the Repository

```bash
git clone https://github.com/wdog/dotfiles-manager.git
cd dotfiles-manager
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. First Run

```bash
python main.py
```

## 📋 Step-by-Step Tutorial

### Step 1: Initial Configuration

1. **Launch Application**
   ```bash
   python main.py
   ```

2. **Open Settings**
   - Select `🐒 Settings` from main menu (navigate with arrows and press Enter, or use shortcut keys shown)

3. **Edit Configuration**
   - Choose `✏️ Edit Settings`
   - Configure the following fields (see [Settings Explained](#-settings-explained) for details):
     - [`git_dir`](#git_dir): `~/.dotfiles.git` (default is fine)
     - [`work_tree`](#work_tree): `~` (your home directory)
     - [`remote`](#remote): Your dotfiles repository URL (e.g., `https://github.com/username/dotfiles.git`)
     - [`enable_logging`](#enable_logging): `true` (recommended for debugging)
   - Press `s` to save settings
   - Press `q` to exit settings editor

### Step 2: Initialize Repository

1. **Back in Settings Menu**
   - Select `🚀 Initialize Git Repo`
   - Confirm with `y` when prompted
   - Wait for initialization to complete (creates bare git repository)

### Step 3: First Pull (if you have existing dotfiles)

1. **From Main Menu**
   - Select `🍻 Modified Files`
   - Press `g` to pull changes from remote
   - If conflicts occur, backups are automatically created in `~/.config/dotfiles-manager/backup/`

### Step 4: Add Your First Files

1. **Browse Files**
   - From main menu, select `🐙 Browse Files`
   - Navigate using arrows
   - Find your config files (e.g., `.bashrc`, `.vimrc`, `.config/`)

2. **Select Files**
   - Press `Space` to select files (🍌 banana emoji indicates selection)
   - Select multiple files as needed

3. **Stage Files**
   - Press `Tab` to add selected files to git staging area
   - Confirm with `y` when prompted

### Step 5: Commit Changes

1. **View Staged Files**
   - Go back to main menu and select `🍻 Modified Files`
   - You'll see your staged files listed

2. **Create Commit**
   - Press `c` to commit
   - Auto-generated commit message will be shown
   - Confirm with `y`

### Step 6: Push to Remote

1. **Push Changes**
   - Still in Modified Files view, press `p` to push
   - Changes are pushed to your remote repository
   - No additional confirmation needed

### Step 7: Monitor and Manage

#### Viewing Logs
1. **Access Logs**
   - Go to `🐒 Settings` → `📋 View Logs`
   - Navigate with arrows
   - Press `r` to refresh
   - Press `d` to clear logs (with confirmation)

#### Managing Backups
1. **Access Backup Manager**
   - Go to `🐒 Settings` → `🗑️ Manage Backups`
   - View all backups with timestamp and file count
   - Press `x` to delete unwanted backups
   - Each backup shows size and creation date

#### Ongoing Workflow
1. **Regular Updates**
   - Use `🐙 Browse Files` to add new config files
   - Use `🍻 Modified Files` to commit and push changes
   - Pull updates with `g` in Modified Files view

2. **Quick Operations**
   - `c` = commit with auto-generated message
   - `p` = push to remote (no confirmation)
   - `g` = pull from remote (no confirmation)
   - `r` = remove from staging (unstage files)

## 🎮 Key Controls

### Main Navigation
- **↑↓** - Navigate menus
- **Enter** - Select option
- **Shortcut keys** - Use the key shortcuts displayed in option menus
- **q / Esc** - Go back/quit

### File Browser
- **Space** - Toggle file selection (🍌 banana emoji indicates selection)
- **Tab** - Add selected files to git staging
- **/** - Search files
- **s** - Toggle sort mode (name/modified/size)

### Modified Files View
- **↑↓** - Navigate files
- **Space** - Toggle file selection
- **c** - Commit selected/all files
- **p** - Push changes (no confirmation)
- **g** - Pull changes (no confirmation)
- **r** - Remove from staging (unstage)

### Settings Interface
- **↑↓** - Navigate between fields
- **Enter** - Edit current field
- **s** - Save all changes
- **r** - Reset current field (with y/n confirmation)
- **q** - Exit without saving

### Backup Manager
- **↑↓** - Navigate backups
- **x** - Delete backup (no confirmation)
- **q** - Return to menu

## ⚙️ Configuration

The application uses a simple `config.json` file with these settings:

```json
{
    "git_dir": "~/.dotfiles.git",
    "work_tree": "~",
    "remote": "https://github.com/yourusername/dotfiles.git",
    "enable_logging": true
}
```

### Git Setup

The application creates a **bare repository** for dotfiles management:

```bash
# This is done automatically by the app:
git init --bare ~/.dotfiles.git
git --git-dir=~/.dotfiles.git --work-tree=~ config status.showUntrackedFiles no
```

## 🛡️ Backup System

The application automatically creates backups when:
- Pull operations would overwrite local files
- Files exist locally that conflict with remote changes

Backups are stored in `~/.config/dotfiles-manager/backup/YYYYMMDD_HHMMSS/`

### Managing Backups

1. Go to **Settings** → **🗑️ Manage Backups**
2. View all backups with timestamp, file count, and size
3. Use **x** to delete unwanted backups (no confirmation)
4. Navigate with **↑↓** arrows
5. Press **q** to return to settings menu

## 🆕 Recent Updates



### Logging

Enable logging in settings to track operations and debug issues. View logs with **Settings** → **📋 View Logs**.

Log controls:
- **↑↓** - Navigate through log entries
- **d** - Clear entire log (with y/n confirmation)
- **r** - Refresh log display
- **q** - Return to settings menu

### Remote Repository

The application supports any git remote (GitHub, GitLab, self-hosted):

```bash
# Example remotes:
https://github.com/username/dotfiles.git
git@github.com:username/dotfiles.git
https://gitlab.com/username/dotfiles.git
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes following the modular architecture
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source. Feel free to use, modify, and distribute.

## 🆘 Troubleshooting

### Application Won't Start
- Check Python version: `python --version` (requires 3.7+)
- Verify dependencies: `pip install -r requirements.txt`
- Check terminal size (minimum recommended: 80x24)
- Ensure `rich` library is installed: `pip install rich`

### Repository Initialization Fails
- Verify git is installed: `git --version`
- Check permissions for git directory location
- Ensure remote URL is correct and accessible
- Use Settings → Initialize Git Repo with y/n confirmations

### Git Operations Fail
- Check repository initialization in Settings
- Verify SSH keys are set up for git remotes
- Enable logging to see detailed error messages
- Try manual git operations to test connectivity

### Files Not Showing
- Check .gitignore patterns in Settings → Edit .gitignore
- Verify file permissions in target directories
- Use file browser search (/) to locate specific files
- Check if files are already tracked in Tracked Files view

### Input/Navigation Issues
- Ensure terminal supports ANSI escape sequences
- Try different terminal emulators if keys don't work
- Navigate with arrow keys or use shortcut keys displayed in option menus
- Application supports both interactive and automated input

## ⚙️ Settings Explained

Understanding the configuration settings is crucial for proper dotfiles management. Each setting controls how the application interacts with Git and manages your files.

### `git_dir`
**Purpose**: Location of the Git repository metadata
**Default**: `~/.dotfiles.git`
**What it does**: This is where Git stores all repository information (commits, branches, refs, etc.). Using a hidden directory keeps your home directory clean while maintaining full Git functionality.

**Why bare repository**: A bare repository has no working directory, which is perfect for dotfiles since your entire home directory becomes the working tree.

### `work_tree`
**Purpose**: The directory that contains your actual files
**Default**: `~` (your home directory)
**What it does**: This tells Git where your actual configuration files are located. All file operations (add, commit, etc.) operate on files within this directory.

**Why home directory**: Your dotfiles (.bashrc, .vimrc, .config/, etc.) are naturally stored in your home directory, so this becomes your Git working tree.

### `remote`
**Purpose**: URL of your remote Git repository
**Example**: `https://github.com/username/dotfiles.git`
**What it does**: This is where your dotfiles are stored in the cloud. The application uses this to:
- Push your local changes to backup/share them
- Pull updates from other machines
- Synchronize dotfiles across multiple systems

**Supported formats**:
- HTTPS: `https://github.com/user/repo.git`
- SSH: `git@github.com:user/repo.git`
- GitLab: `https://gitlab.com/user/repo.git`

### `enable_logging`
**Purpose**: Controls whether operations are logged
**Default**: `false`
**What it does**: When enabled, all Git operations and application events are logged to help with:
- Debugging issues
- Understanding what operations were performed
- Tracking changes over time

**Log location**: Logs can be viewed through Settings → View Logs

### How Settings Work Together

1. **Repository Structure**: `git_dir` + `work_tree` create a bare repository that manages your home directory
2. **File Management**: Files in `work_tree` are tracked by Git metadata in `git_dir`
3. **Synchronization**: `remote` enables sharing dotfiles across machines
4. **Monitoring**: `enable_logging` provides visibility into all operations

### Optimization Settings (Automatic)

The application automatically configures these Git settings for optimal performance:

- `status.showUntrackedFiles no` - Prevents Git from scanning thousands of untracked files in your home directory
- `advice.addIgnoredFile false` - Disables warnings about ignored files
- `core.worktree` - Points to your home directory
- `core.excludesfile` - Uses global gitignore for common patterns

---

**Made with 🦀 and ❤️ for me**
