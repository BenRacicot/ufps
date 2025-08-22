#!/usr/bin/env python3
"""
UFPS CLI - Main command-line interface
"""

import os
import sys
from pathlib import Path

# Add package to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ufps.interface import InteractiveCLI

def main():
    """Main entry point"""
    cli = InteractiveCLI()
    cli.run()

if __name__ == "__main__":
    main()