#!/usr/bin/env python3
"""
UFPS Uninstaller
Cleanly removes UFPS and all its components
"""

import os
import sys
import shutil
from pathlib import Path
import json

# Installation paths
INSTALL_DIR = Path.home() / ".ufps"
BIN_DIR = Path.home() / ".local" / "bin"
WRAPPER_PATH = BIN_DIR / "ufps"
CONFIG_FILE = INSTALL_DIR / "config.json"

class ColorPrint:
    """Simple colored output"""
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    
    @classmethod
    def success(cls, msg):
        print(f"{cls.OKGREEN}✓{cls.ENDC}  {msg}")
    
    @classmethod
    def warning(cls, msg):
        print(f"{cls.WARNING}⚠{cls.ENDC}  {msg}")
    
    @classmethod
    def error(cls, msg):
        print(f"{cls.FAIL}✗{cls.ENDC}  {msg}")

def confirm_uninstall():
    """Ask for confirmation"""
    print("""
╔═══════════════════════════════════════╗
║         UFPS UNINSTALLER v1.0         ║
╚═══════════════════════════════════════╝
    """)
    
    if INSTALL_DIR.exists():
        # Calculate size
        total_size = sum(f.stat().st_size for f in INSTALL_DIR.rglob('*') if f.is_file())
        size_mb = total_size / 1024 / 1024
        
        print(f"This will remove:")
        print(f"  • UFPS installation directory: {INSTALL_DIR}")
        print(f"  • Executable wrapper: {WRAPPER_PATH}")
        print(f"  • Total space to be freed: {size_mb:.1f} MB")
        print()
    else:
        ColorPrint.warning("UFPS installation not found at expected location")
        print(f"Expected: {INSTALL_DIR}")
        print()
    
    response = input("Continue with uninstallation? [y/N]: ").strip().lower()
    return response == 'y'

def remove_installation():
    """Remove all UFPS files"""
    removed_items = []
    failed_items = []
    
    # Remove main installation directory
    if INSTALL_DIR.exists():
        try:
            shutil.rmtree(INSTALL_DIR)
            removed_items.append(f"Installation directory: {INSTALL_DIR}")
        except Exception as e:
            failed_items.append(f"Installation directory: {e}")
    
    # Remove wrapper script
    if WRAPPER_PATH.exists():
        try:
            WRAPPER_PATH.unlink()
            removed_items.append(f"Executable: {WRAPPER_PATH}")
        except Exception as e:
            failed_items.append(f"Executable: {e}")
    
    # Clean up empty directories
    if BIN_DIR.exists() and not any(BIN_DIR.iterdir()):
        try:
            BIN_DIR.rmdir()
            removed_items.append(f"Empty directory: {BIN_DIR}")
        except:
            pass
    
    return removed_items, failed_items

def main():
    """Main uninstall process"""
    if not confirm_uninstall():
        print("Uninstallation cancelled")
        sys.exit(0)
    
    print("\nUninstalling UFPS...")
    print("-" * 40)
    
    removed, failed = remove_installation()
    
    # Report results
    if removed:
        print("\nSuccessfully removed:")
        for item in removed:
            ColorPrint.success(item)
    
    if failed:
        print("\nFailed to remove:")
        for item in failed:
            ColorPrint.error(item)
    
    print("\n" + "=" * 40)
    
    if failed:
        ColorPrint.warning("Uninstallation completed with errors")
        print("You may need to manually remove remaining files")
    else:
        ColorPrint.success("UFPS has been completely uninstalled")
    
    # PATH reminder
    print(f"""
Note: If you added {BIN_DIR} to your PATH during installation,
you may want to remove it from your shell configuration file:
  • ~/.bashrc or ~/.zshrc
    """)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nUninstallation cancelled")
        sys.exit(1)
    except Exception as e:
        ColorPrint.error(f"Uninstallation failed: {e}")
        sys.exit(1)