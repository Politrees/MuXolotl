#!/usr/bin/env python3
"""MuXolotl - Universal Media Converter
Entry point for the application
"""

import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

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
    except (KeyboardInterrupt, SystemExit):
        logger.info("Application terminated by user")
        sys.exit(0)
    except (ImportError, RuntimeError, OSError) as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
