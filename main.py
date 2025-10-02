#!/usr/bin/env python3
"""
MuXolotl - Universal Media Converter
Entry point for the application
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gui.main_window import MuXolotlApp
from utils.logger import setup_logger

def main():
    """Main application entry point"""
    # Setup logging
    logger = setup_logger()
    logger.info("Starting MuXolotl application")
    
    try:
        # Create and run application
        app = MuXolotlApp()
        app.run()
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()