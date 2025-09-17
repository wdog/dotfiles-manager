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

### 4. Initial Setup

1. **Open Settings Menu** - Select `🐒 Settings` from main menu
2. **Edit Configuration** - Choose `✏️ Edit Settings`
3. **Configure Git Repository**:
   - Set `git_dir` (default: `~/.dotfiles.git`)
   - Set `work_tree` (default: `~`)
   - Set `remote` URL (your dotfiles repository)
   - Enable logging if desired
4. **Initialize Repository** - Go back and select `🚀 Initialize Git Repo`
   - Confirm with `y` when prompted
   - Repository will be automatically configured

### 5. Basic Workflow

1. **Browse Files** - Use `🐙 Browse Files` to select configuration files
2. **Stage Changes** - Select files and press `Tab` to add to git
3. **View Changes** - Use `🍻 Modified Files` to see staged files
4. **Commit** - Press `c` to commit with auto-generated message
5. **Push** - Press `p` to push changes to remote repository

## 🎮 Key Controls

### Main Navigation
- **↑↓ / hjkl** - Navigate menus
- **Enter** - Select option
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
- Use number keys (1-5) for direct menu selection
- Application supports both interactive and automated input

---

**Made with 🦀 and ❤️ for me**
