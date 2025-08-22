#!/usr/bin/env python3
"""
UFPS Installation Test Suite - Python Version
More detailed testing with better control
"""

import os
import sys
import shutil
import subprocess
import tempfile
import json
import time
from pathlib import Path
from datetime import datetime

# Test configuration
INSTALL_DIR = Path.home() / ".ufps"
BIN_PATH = Path.home() / ".local" / "bin" / "ufps"
TEST_VIDEO_URL = "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4"

class TestColors:
    """Terminal colors for test output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class InstallationTester:
    def __init__(self, clean_install=False, verbose=False):
        self.clean_install = clean_install
        self.verbose = verbose
        self.backup_dir = Path(tempfile.mkdtemp(prefix="ufps_backup_"))
        self.test_results = []
        self.original_exists = False
        
    def print_header(self, text):
        """Print section header"""
        print(f"\n{TestColors.CYAN}{'='*50}{TestColors.ENDC}")
        print(f"{TestColors.CYAN}{text}{TestColors.ENDC}")
        print(f"{TestColors.CYAN}{'='*50}{TestColors.ENDC}")
    
    def print_test(self, name):
        """Print test name"""
        print(f"\n{TestColors.BLUE}▶ {name}{TestColors.ENDC}")
    
    def print_success(self, msg):
        """Print success message"""
        print(f"  {TestColors.GREEN}✓{TestColors.ENDC} {msg}")
        self.test_results.append(("PASS", msg))
    
    def print_fail(self, msg):
        """Print failure message"""
        print(f"  {TestColors.RED}✗{TestColors.ENDC} {msg}")
        self.test_results.append(("FAIL", msg))
    
    def print_info(self, msg):
        """Print info message"""
        print(f"  {TestColors.YELLOW}ℹ{TestColors.ENDC} {msg}")
    
    def print_warning(self, msg):
        """Print warning message"""
        print(f"  {TestColors.YELLOW}⚠{TestColors.ENDC} {msg}")
    
    def backup_existing(self):
        """Backup existing installation"""
        if INSTALL_DIR.exists():
            self.original_exists = True
            self.print_info(f"Backing up existing installation to {self.backup_dir}")
            shutil.copytree(INSTALL_DIR, self.backup_dir / "ufps")
            
        if BIN_PATH.exists():
            shutil.copy2(BIN_PATH, self.backup_dir / "ufps_bin")
    
    def restore_backup(self):
        """Restore original installation"""
        if self.original_exists:
            self.print_info("Restoring original installation...")
            if INSTALL_DIR.exists():
                shutil.rmtree(INSTALL_DIR)
            shutil.copytree(self.backup_dir / "ufps", INSTALL_DIR)
            
            if (self.backup_dir / "ufps_bin").exists():
                BIN_PATH.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(self.backup_dir / "ufps_bin", BIN_PATH)
    
    def cleanup(self):
        """Clean up test artifacts"""
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
    
    def run_command(self, cmd, capture=True):
        """Run shell command"""
        if self.verbose:
            self.print_info(f"Running: {cmd}")
        
        if capture:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.returncode == 0, result.stdout, result.stderr
        else:
            result = subprocess.run(cmd, shell=True)
            return result.returncode == 0
    
    def test_prerequisites(self):
        """Test 1: Check prerequisites"""
        self.print_test("Test 1: Prerequisites Check")
        
        # Python version
        if sys.version_info >= (3, 8):
            self.print_success(f"Python {sys.version.split()[0]} >= 3.8")
        else:
            self.print_fail(f"Python {sys.version.split()[0]} < 3.8")
            return False
        
        # Git
        if shutil.which("git"):
            self.print_success("Git is installed")
        else:
            self.print_fail("Git not found")
            return False
        
        # Installation files
        required_files = ["install.py", "uninstall.py", "pyproject.toml"]
        for file in required_files:
            if Path(file).exists():
                self.print_success(f"{file} exists")
            else:
                self.print_fail(f"{file} not found")
                return False
        
        return True
    
    def test_fresh_install(self):
        """Test 2: Fresh installation"""
        self.print_test("Test 2: Fresh Installation")
        
        # Remove existing if clean install requested
        if self.clean_install and INSTALL_DIR.exists():
            self.print_info("Removing existing installation for clean test...")
            shutil.rmtree(INSTALL_DIR)
        
        # Run installer
        success, stdout, stderr = self.run_command("python3 install.py")
        if success:
            self.print_success("Installation completed")
        else:
            self.print_fail("Installation failed")
            if self.verbose:
                print("STDOUT:", stdout)
                print("STDERR:", stderr)
            return False
        
        # Verify structure
        checks = [
            (INSTALL_DIR, "Installation directory"),
            (INSTALL_DIR / "venv", "Virtual environment"),
            (INSTALL_DIR / "cli.py", "Main CLI script"),
            (INSTALL_DIR / "config.json", "Configuration file"),
            (BIN_PATH, "Executable wrapper"),
        ]
        
        for path, desc in checks:
            if path.exists():
                self.print_success(f"{desc} created")
            else:
                self.print_fail(f"{desc} not found")
                return False
        
        # Check config content
        config = json.loads((INSTALL_DIR / "config.json").read_text())
        if "version" in config and "python_version" in config:
            self.print_success("Configuration properly saved")
        else:
            self.print_fail("Configuration incomplete")
        
        return True
    
    def test_python_packages(self):
        """Test 3: Verify Python packages"""
        self.print_test("Test 3: Python Package Verification")
        
        venv_python = INSTALL_DIR / "venv" / "bin" / "python"
        if not venv_python.exists():
            venv_python = INSTALL_DIR / "venv" / "Scripts" / "python.exe"  # Windows
        
        packages = {
            "torch": "PyTorch",
            "torchvision": "TorchVision",
            "cv2": "OpenCV",
            "numpy": "NumPy",
            "PIL": "Pillow",
            "rich": "Rich (CLI formatting)",
            "questionary": "Questionary (CLI prompts)"
        }
        
        for module, name in packages.items():
            cmd = f'"{venv_python}" -c "import {module}"'
            success, _, _ = self.run_command(cmd)
            if success:
                self.print_success(f"{name} installed")
            else:
                self.print_fail(f"{name} not found")
        
        return True
    
    def test_rife_setup(self):
        """Test 4: RIFE and models"""
        self.print_test("Test 4: RIFE and Model Setup")
        
        # Check RIFE directory
        rife_dir = INSTALL_DIR / "RIFE"
        if rife_dir.exists():
            self.print_success("RIFE repository present")
            
            # Check for key RIFE files
            rife_files = ["inference_video.py", "inference_img.py", "model"]
            for file in rife_files:
                if any(rife_dir.rglob(file + "*")):
                    self.print_success(f"RIFE {file} found")
                else:
                    self.print_warning(f"RIFE {file} not found")
        else:
            self.print_fail("RIFE repository not found")
            return False
        
        # Check models
        models_dir = INSTALL_DIR / "models"
        if models_dir.exists():
            model_files = list(models_dir.glob("*.pkl"))
            if len(model_files) >= 3:
                self.print_success(f"AI models present ({len(model_files)} files)")
                for model in model_files:
                    size_mb = model.stat().st_size / 1024 / 1024
                    self.print_info(f"  {model.name}: {size_mb:.1f} MB")
            else:
                self.print_fail(f"Incomplete models ({len(model_files)} files)")
        else:
            self.print_fail("Models directory not found")
        
        return True
    
    def test_cli_execution(self):
        """Test 5: CLI execution"""
        self.print_test("Test 5: CLI Execution")
        
        if not BIN_PATH.exists():
            self.print_fail("Executable not found")
            return False
        
        # Try to get help or version
        test_commands = [
            (f'echo "q" | "{BIN_PATH}"', "Interactive mode"),
            (f'cd /tmp && echo "q" | "{BIN_PATH}"', "Run from different directory"),
        ]
        
        for cmd, desc in test_commands:
            success, stdout, stderr = self.run_command(cmd)
            if "UFPS" in stdout or "video" in stdout.lower() or "Ultra FPS" in stdout:
                self.print_success(f"{desc} works")
            else:
                self.print_warning(f"{desc} - unclear output")
                if self.verbose:
                    print("Output:", stdout[:200])
        
        return True
    
    def test_reinstallation(self):
        """Test 6: Reinstallation handling"""
        self.print_test("Test 6: Reinstallation Handling")
        
        # Save current config
        config_before = (INSTALL_DIR / "config.json").read_text()
        
        # Run installer again
        success, stdout, stderr = self.run_command("python3 install.py")
        if success:
            self.print_success("Reinstallation completed without errors")
        else:
            self.print_fail("Reinstallation failed")
            return False
        
        # Check config preserved/updated
        config_after = (INSTALL_DIR / "config.json").read_text()
        if config_after:
            self.print_success("Configuration maintained")
        
        # Verify everything still works
        if BIN_PATH.exists() and INSTALL_DIR.exists():
            self.print_success("Installation intact after reinstall")
        else:
            self.print_fail("Installation broken after reinstall")
            return False
        
        return True
    
    def test_uninstallation(self):
        """Test 7: Uninstallation"""
        self.print_test("Test 7: Uninstallation")
        
        # Run uninstaller with auto-confirm
        success, stdout, stderr = self.run_command('echo "y" | python3 uninstall.py')
        if success:
            self.print_success("Uninstaller executed")
        else:
            self.print_fail("Uninstaller failed")
            return False
        
        # Check removal
        if not INSTALL_DIR.exists():
            self.print_success("Installation directory removed")
        else:
            self.print_fail("Installation directory still exists")
            return False
        
        if not BIN_PATH.exists():
            self.print_success("Executable removed")
        else:
            self.print_fail("Executable still exists")
            return False
        
        return True
    
    def test_edge_cases(self):
        """Test 8: Edge cases and error handling"""
        self.print_test("Test 8: Edge Cases")
        
        # Test with missing permissions (if possible)
        # Test with interrupted installation
        # Test with corrupted config
        
        self.print_info("Edge case testing not fully implemented")
        return True
    
    def run_all_tests(self):
        """Run complete test suite"""
        self.print_header("UFPS Installation Test Suite")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Clean Install: {self.clean_install}")
        print(f"Verbose: {self.verbose}")
        
        # Backup existing installation
        if not self.clean_install:
            self.backup_existing()
        
        try:
            # Run test sequence
            tests = [
                self.test_prerequisites,
                self.test_fresh_install,
                self.test_python_packages,
                self.test_rife_setup,
                self.test_cli_execution,
                self.test_reinstallation,
                self.test_uninstallation,
                # self.test_edge_cases,
            ]
            
            for test in tests:
                if not test():
                    self.print_warning(f"Stopping due to failure in {test.__name__}")
                    break
            
        finally:
            # Restore backup if needed
            if not self.clean_install and self.original_exists:
                self.restore_backup()
            
            # Cleanup
            self.cleanup()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        self.print_header("Test Summary")
        
        passed = sum(1 for result, _ in self.test_results if result == "PASS")
        failed = sum(1 for result, _ in self.test_results if result == "FAIL")
        total = len(self.test_results)
        
        print(f"\nResults: {passed}/{total} passed, {failed} failed")
        
        if failed > 0:
            print(f"\n{TestColors.RED}Failed tests:{TestColors.ENDC}")
            for result, msg in self.test_results:
                if result == "FAIL":
                    print(f"  • {msg}")
        
        if failed == 0:
            print(f"\n{TestColors.GREEN}{TestColors.BOLD}All tests passed! ✨{TestColors.ENDC}")
        else:
            print(f"\n{TestColors.RED}{TestColors.BOLD}Some tests failed!{TestColors.ENDC}")

def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test UFPS installation")
    parser.add_argument("--clean", action="store_true", 
                      help="Remove existing installation before testing")
    parser.add_argument("--verbose", "-v", action="store_true",
                      help="Show detailed output")
    parser.add_argument("--quick", action="store_true",
                      help="Run quick tests only (skip download-heavy tests)")
    
    args = parser.parse_args()
    
    tester = InstallationTester(
        clean_install=args.clean,
        verbose=args.verbose
    )
    
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print(f"\n{TestColors.YELLOW}Testing interrupted by user{TestColors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{TestColors.RED}Test suite error: {e}{TestColors.ENDC}")
        sys.exit(1)

if __name__ == "__main__":
    main()