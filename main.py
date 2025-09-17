#!/usr/bin/env python3
"""
Dotfiles Manager - Main Entry Point
A modular, extensible dotfiles management application.
"""

import sys
import os

# Add the current directory to Python path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotfiles_manager.app import DotfilesApp
from dotfiles_manager.ui.rich_ui import RichUI

def main():
    """Main entry point"""
    try:
        # Create UI implementation option
        ui = RichUI()

        # Create and run the application
        app = DotfilesApp(ui)
        app.run()

    except ImportError as e:
        print(f"Error importing required modules: {e}")
        print("Make sure you have installed the required dependencies:")
        print("pip install rich")
        sys.exit(1)

    except Exception as e:
        print(f"Critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
