#!/usr/bin/env python3
"""
UFPS Installation Script
Handles complete setup including dependencies, RIFE, models, and ffmpeg
"""

import os
import sys
import subprocess
import platform
import shutil
import tempfile
import urllib.request
import ssl
import zipfile
import tarfile
from pathlib import Path
import json
import hashlib

# Installation configuration
INSTALL_DIR = Path.home() / ".ufps"
VENV_DIR = INSTALL_DIR / "venv"
RIFE_DIR = INSTALL_DIR / "RIFE"
MODELS_DIR = INSTALL_DIR / "models"
FFMPEG_DIR = INSTALL_DIR / "ffmpeg"
CONFIG_FILE = INSTALL_DIR / "config.json"
BIN_DIR = Path.home() / ".local" / "bin"

# URLs for dependencies
RIFE_REPO = "https://github.com/hzwer/ECCV2022-RIFE.git"
MODEL_URLS = {
    "RIFE_HD": {
        # Google Drive direct download link (using export format)
        "url": "https://drive.google.com/uc?export=download&id=1APIzVeI-4ZZCEuIRE1m6WYfSCaOsi_7_",
        "size": "~50MB",
        "files": ["flownet.pkl", "contextnet.pkl", "unet.pkl", "fusionnet.pkl"],
        "gdrive_id": "1APIzVeI-4ZZCEuIRE1m6WYfSCaOsi_7_"
    },
    "RIFE_v4": {
        # Alternative model from the paper
        "url": "https://drive.google.com/uc?export=download&id=1h42aGYPNJn2q8j_GVkS_yDu__G_UZ2GX",
        "size": "~13MB", 
        "files": ["flownet.pkl", "contextnet.pkl", "unet.pkl"],
        "gdrive_id": "1h42aGYPNJn2q8j_GVkS_yDu__G_UZ2GX"
    }
}

# FFmpeg download URLs by platform
FFMPEG_URLS = {
    "darwin": {
        "arm64": "https://evermeet.cx/ffmpeg/getrelease/ffmpeg/7z",
        "x86_64": "https://evermeet.cx/ffmpeg/getrelease/ffmpeg/7z"
    },
    "linux": {
        "x86_64": "https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz"
    }
}

class ColorPrint:
    """Simple colored output without dependencies"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    
    @classmethod
    def info(cls, msg):
        print(f"{cls.OKBLUE}ℹ{cls.ENDC}  {msg}")
    
    @classmethod
    def success(cls, msg):
        print(f"{cls.OKGREEN}✓{cls.ENDC}  {msg}")
    
    @classmethod
    def warning(cls, msg):
        print(f"{cls.WARNING}⚠{cls.ENDC}  {msg}")
    
    @classmethod
    def error(cls, msg):
        print(f"{cls.FAIL}✗{cls.ENDC}  {msg}")
    
    @classmethod
    def header(cls, msg):
        print(f"\n{cls.HEADER}{cls.BOLD}{msg}{cls.ENDC}")
        print("=" * len(msg))

def check_python_version():
    """Ensure Python 3.8+"""
    if sys.version_info < (3, 8):
        ColorPrint.error("Python 3.8 or higher is required")
        ColorPrint.info("Your version: Python " + ".".join(map(str, sys.version_info[:3])))
        sys.exit(1)

def check_system():
    """Check system compatibility"""
    system = platform.system().lower()
    arch = platform.machine().lower()
    
    if system not in ["darwin", "linux"]:
        ColorPrint.error(f"Unsupported OS: {system}")
        ColorPrint.info("UFPS currently supports macOS and Linux")
        sys.exit(1)
    
    return system, arch

def run_command(cmd, cwd=None, capture=False):
    """Run a shell command"""
    try:
        if capture:
            result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
            return result.returncode == 0, result.stdout, result.stderr
        else:
            result = subprocess.run(cmd, shell=True, cwd=cwd)
            return result.returncode == 0
    except Exception as e:
        ColorPrint.error(f"Command failed: {e}")
        return False if not capture else (False, "", str(e))

def download_file(url, dest, desc="Downloading"):
    """Download file with progress"""
    try:
        ColorPrint.info(f"{desc}...")
        
        # Check if it's a Google Drive URL and use gdown if available
        if "drive.google.com" in url:
            # Try using gdown for Google Drive files
            try:
                import gdown
                gdown.download(url, str(dest), quiet=False)
                return True
            except ImportError:
                # Fall back to wget/curl for Google Drive
                ColorPrint.warning("gdown not available, trying alternative download method...")
                gdrive_id = url.split("id=")[-1] if "id=" in url else None
                if gdrive_id:
                    # Try wget with Google Drive
                    wget_cmd = f'wget --no-check-certificate "https://drive.google.com/uc?export=download&id={gdrive_id}" -O "{dest}"'
                    success = run_command(wget_cmd)
                    if success:
                        return True
                    # Try curl as fallback
                    curl_cmd = f'curl -L "https://drive.google.com/uc?export=download&id={gdrive_id}" -o "{dest}"'
                    success = run_command(curl_cmd)
                    return success
        
        # Standard download for non-Google Drive URLs
        def download_hook(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(100, downloaded * 100 // total_size) if total_size > 0 else 0
            bar_length = 40
            filled = int(bar_length * percent // 100)
            bar = '█' * filled + '░' * (bar_length - filled)
            if total_size > 0:
                size_mb = total_size / 1024 / 1024
                downloaded_mb = downloaded / 1024 / 1024
                print(f'\r  [{bar}] {percent}% ({downloaded_mb:.1f}/{size_mb:.1f} MB)', end='', flush=True)
            else:
                print(f'\r  Downloading... {downloaded / 1024 / 1024:.1f} MB', end='', flush=True)
        
        # Create SSL context that doesn't verify certificates (for Google Drive)
        if "drive.google.com" in url:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl_context))
            urllib.request.install_opener(opener)
        
        urllib.request.urlretrieve(url, dest, reporthook=download_hook)
        print()  # New line after progress
        return True
    except Exception as e:
        ColorPrint.error(f"Download failed: {e}")
        return False

def setup_virtual_environment():
    """Create isolated Python environment"""
    ColorPrint.header("Setting up Python environment")
    
    if VENV_DIR.exists():
        ColorPrint.info("Virtual environment already exists")
        return True
    
    ColorPrint.info("Creating virtual environment...")
    if not run_command(f'"{sys.executable}" -m venv "{VENV_DIR}"'):
        ColorPrint.error("Failed to create virtual environment")
        return False
    
    ColorPrint.success("Virtual environment created")
    
    # Get pip path in venv
    if platform.system() == "Windows":
        pip_path = VENV_DIR / "Scripts" / "pip"
        python_path = VENV_DIR / "Scripts" / "python"
    else:
        pip_path = VENV_DIR / "bin" / "pip"
        python_path = VENV_DIR / "bin" / "python"
    
    # Upgrade pip
    ColorPrint.info("Upgrading pip...")
    run_command(f'"{python_path}" -m pip install --upgrade pip')
    
    return True

def install_python_packages():
    """Install Python dependencies in venv"""
    ColorPrint.header("Installing Python packages")
    
    if platform.system() == "Windows":
        pip_path = VENV_DIR / "Scripts" / "pip"
    else:
        pip_path = VENV_DIR / "bin" / "pip"
    
    packages = [
        "torch torchvision --index-url https://download.pytorch.org/whl/cpu",
        "opencv-python",
        "numpy",
        "Pillow",
        "rich",
        "questionary",
        "tqdm",
        "requests",
        "packaging",
        "scikit-video"  # Required by RIFE's inference_video.py
    ]
    
    for package in packages:
        ColorPrint.info(f"Installing {package.split()[0]}...")
        if not run_command(f'"{pip_path}" install {package}'):
            ColorPrint.warning(f"Failed to install {package}, continuing...")
    
    ColorPrint.success("Python packages installed")
    return True

def setup_rife():
    """Download and setup RIFE"""
    ColorPrint.header("Setting up RIFE")
    
    if RIFE_DIR.exists():
        ColorPrint.info("RIFE already exists")
        return True
    
    ColorPrint.info("Cloning RIFE repository...")
    if not run_command(f'git clone --depth 1 "{RIFE_REPO}" "{RIFE_DIR}"'):
        ColorPrint.error("Failed to clone RIFE. Is git installed?")
        ColorPrint.info("Install git with: brew install git (macOS) or apt-get install git (Linux)")
        return False
    
    ColorPrint.success("RIFE downloaded")
    return True

def download_models():
    """Install RIFE models from bundled files or download"""
    ColorPrint.header("Installing AI models")
    
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check if models already exist
    existing_models = list(MODELS_DIR.glob("*.pkl"))
    if existing_models:
        ColorPrint.info(f"Models already installed: {[m.name for m in existing_models]}")
        return True
    
    # Check for bundled models in the project directory
    script_dir = Path(__file__).parent
    bundled_models_dir = script_dir / "models"
    
    if bundled_models_dir.exists():
        bundled_files = list(bundled_models_dir.glob("*.pkl")) + list(bundled_models_dir.glob("*.py"))
        if bundled_files:
            ColorPrint.info(f"Installing bundled models from {bundled_models_dir}")
            for model_file in bundled_files:
                dest = MODELS_DIR / model_file.name
                ColorPrint.info(f"  Copying {model_file.name}")
                shutil.copy2(model_file, dest)
            ColorPrint.success(f"Installed {len(bundled_files)} model files")
            return True
    
    # Fallback to download instructions
    ColorPrint.warning("No bundled models found")
    ColorPrint.info("Models can be downloaded manually:")
    ColorPrint.info("1. Download HD models from: https://drive.google.com/file/d/1APIzVeI-4ZZCEuIRE1m6WYfSCaOsi_7_/view")
    ColorPrint.info("2. Extract the .pkl files to: ~/.ufps/models/")
    
    # Don't fail installation - models can be obtained later
    return True

def setup_ffmpeg():
    """Download or locate ffmpeg"""
    ColorPrint.header("Setting up FFmpeg")
    
    # First check if ffmpeg is already installed
    if shutil.which("ffmpeg"):
        ColorPrint.success("FFmpeg found in system PATH")
        return True
    
    # Check our local installation
    local_ffmpeg = FFMPEG_DIR / "ffmpeg"
    if local_ffmpeg.exists():
        ColorPrint.info("FFmpeg already installed locally")
        return True
    
    system, arch = check_system()
    
    # Try to install via package manager
    ColorPrint.info("Attempting to install FFmpeg...")
    
    if system == "darwin":
        # Check for Homebrew
        if shutil.which("brew"):
            ColorPrint.info("Installing FFmpeg via Homebrew...")
            if run_command("brew install ffmpeg"):
                ColorPrint.success("FFmpeg installed via Homebrew")
                return True
    elif system == "linux":
        # Try apt-get
        if shutil.which("apt-get"):
            ColorPrint.info("Installing FFmpeg via apt-get...")
            if run_command("sudo apt-get update && sudo apt-get install -y ffmpeg"):
                ColorPrint.success("FFmpeg installed via apt-get")
                return True
    
    # Manual download as fallback
    ColorPrint.warning("Package manager installation failed, downloading manually...")
    FFMPEG_DIR.mkdir(parents=True, exist_ok=True)
    
    # For now, we'll require manual installation
    ColorPrint.warning("Please install FFmpeg manually:")
    if system == "darwin":
        ColorPrint.info("  brew install ffmpeg")
    else:
        ColorPrint.info("  sudo apt-get install ffmpeg")
    
    return False

def create_wrapper_script():
    """Create the main ufps executable wrapper"""
    ColorPrint.header("Creating executable wrapper")
    
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    
    wrapper_path = BIN_DIR / "ufps"
    
    # Create wrapper script
    wrapper_content = f'''#!/usr/bin/env bash
# UFPS Wrapper Script
# Auto-generated by install.py

# Configuration
UFPS_HOME="{INSTALL_DIR}"
VENV_PATH="{VENV_DIR}"
SCRIPT_PATH="{INSTALL_DIR}/cli.py"

# Activate virtual environment and run
source "$VENV_PATH/bin/activate" 2>/dev/null
export UFPS_HOME
export UFPS_MODELS_DIR="{MODELS_DIR}"
export UFPS_RIFE_DIR="{RIFE_DIR}"

exec python "$SCRIPT_PATH" "$@"
'''
    
    wrapper_path.write_text(wrapper_content)
    wrapper_path.chmod(0o755)
    
    ColorPrint.success(f"Wrapper created at {wrapper_path}")
    
    # Check if ~/.local/bin is in PATH
    if str(BIN_DIR) not in os.environ.get("PATH", ""):
        ColorPrint.warning(f"Add {BIN_DIR} to your PATH:")
        shell = os.environ.get("SHELL", "/bin/bash")
        if "zsh" in shell:
            ColorPrint.info(f'  echo \'export PATH="{BIN_DIR}:$PATH"\' >> ~/.zshrc')
            ColorPrint.info("  source ~/.zshrc")
        else:
            ColorPrint.info(f'  echo \'export PATH="{BIN_DIR}:$PATH"\' >> ~/.bashrc')
            ColorPrint.info("  source ~/.bashrc")
    
    return True

def copy_main_script():
    """Copy the main CLI script to installation directory"""
    ColorPrint.header("Installing main script")
    
    # Convert the original ufps script to use our managed paths
    cli_path = INSTALL_DIR / "cli.py"
    
    # Read original script
    original_script = Path("ufps_old")
    if not original_script.exists():
        ColorPrint.error("Original ufps script not found")
        return False
    
    content = original_script.read_text()
    
    # Update paths to use environment variables
    content = content.replace(
        'RIFE_PATH = Path("/Users/home/dev/ECCV2022-RIFE")',
        'RIFE_PATH = Path(os.environ.get("UFPS_RIFE_DIR", Path.home() / ".ufps" / "RIFE"))'
    )
    content = content.replace(
        'MODEL_PATH = RIFE_PATH / "train_log"',
        'MODEL_PATH = Path(os.environ.get("UFPS_MODELS_DIR", Path.home() / ".ufps" / "models"))'
    )
    
    cli_path.write_text(content)
    cli_path.chmod(0o755)
    
    ColorPrint.success("Main script installed")
    return True

def save_config():
    """Save installation configuration"""
    config = {
        "version": "1.0.0",
        "install_dir": str(INSTALL_DIR),
        "venv_dir": str(VENV_DIR),
        "rife_dir": str(RIFE_DIR),
        "models_dir": str(MODELS_DIR),
        "ffmpeg_dir": str(FFMPEG_DIR),
        "installed_at": str(Path.cwd()),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    }
    
    CONFIG_FILE.write_text(json.dumps(config, indent=2))
    ColorPrint.success("Configuration saved")

def main():
    """Main installation process"""
    print("""
╔═══════════════════════════════════════╗
║          UFPS INSTALLER v1.0          ║
║   Ultra FPS Video Interpolation Tool   ║
╚═══════════════════════════════════════╝
    """)
    
    # Pre-flight checks
    check_python_version()
    system, arch = check_system()
    
    ColorPrint.info(f"System: {system} ({arch})")
    ColorPrint.info(f"Python: {sys.version.split()[0]}")
    ColorPrint.info(f"Install directory: {INSTALL_DIR}")
    
    # Create main directory
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    
    # Installation steps
    steps = [
        ("Creating Python environment", setup_virtual_environment),
        ("Installing Python packages", install_python_packages),
        ("Setting up RIFE", setup_rife),
        ("Downloading AI models", download_models),
        ("Setting up FFmpeg", setup_ffmpeg),
        ("Installing main script", copy_main_script),
        ("Creating executable", create_wrapper_script),
        ("Saving configuration", save_config)
    ]
    
    failed = False
    for desc, func in steps:
        if not func():
            ColorPrint.error(f"Failed: {desc}")
            failed = True
            if desc in ["Creating Python environment", "Setting up RIFE"]:
                break  # Critical failures
    
    print("\n" + "="*40)
    
    if failed:
        ColorPrint.error("Installation completed with errors")
        ColorPrint.warning("Some features may not work correctly")
    else:
        ColorPrint.success("Installation completed successfully!")
    
    print(f"""
To use UFPS:
  1. Add {BIN_DIR} to your PATH (if not already done)
  2. Run: ufps
  
To uninstall:
  python uninstall.py
    """)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled by user")
        sys.exit(1)
    except Exception as e:
        ColorPrint.error(f"Installation failed: {e}")
        sys.exit(1)