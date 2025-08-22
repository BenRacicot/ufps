#!/usr/bin/env python3
"""
UFPS Model Downloader
Downloads RIFE AI models for video interpolation
"""

import os
import sys
import subprocess
import urllib.request
import ssl
import zipfile
import tempfile
from pathlib import Path

MODELS_DIR = Path.home() / ".ufps" / "models"

def download_with_gdown():
    """Try downloading with gdown (handles Google Drive better)"""
    print("Attempting to download models using gdown...")
    
    # Install gdown if not available
    try:
        import gdown
    except ImportError:
        print("Installing gdown...")
        subprocess.run([sys.executable, "-m", "pip", "install", "gdown"], check=True)
        import gdown
    
    # HD models from Google Drive
    url = "https://drive.google.com/uc?id=1APIzVeI-4ZZCEuIRE1m6WYfSCaOsi_7_"
    output = MODELS_DIR / "models.zip"
    
    try:
        gdown.download(url, str(output), quiet=False)
        return output
    except Exception as e:
        print(f"gdown failed: {e}")
        return None

def download_with_wget():
    """Try downloading with wget"""
    print("Attempting to download models using wget...")
    
    # Google Drive file ID
    file_id = "1APIzVeI-4ZZCEuIRE1m6WYfSCaOsi_7_"
    output = MODELS_DIR / "models.zip"
    
    # Construct wget command for Google Drive
    cmd = [
        "wget",
        "--no-check-certificate",
        "--save-cookies", "/tmp/cookies.txt",
        "--keep-session-cookies",
        f"https://drive.google.com/uc?export=download&id={file_id}",
        "-O", str(output)
    ]
    
    try:
        subprocess.run(cmd, check=True)
        return output
    except Exception as e:
        print(f"wget failed: {e}")
        return None

def extract_models(zip_path):
    """Extract model files from zip"""
    print("Extracting models...")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Extract to temp directory first
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_ref.extractall(temp_dir)
                
                # Find and copy .pkl files
                temp_path = Path(temp_dir)
                pkl_files = list(temp_path.rglob("*.pkl"))
                
                if not pkl_files:
                    print("No .pkl files found in archive")
                    return False
                
                for pkl_file in pkl_files:
                    dest = MODELS_DIR / pkl_file.name
                    print(f"Copying {pkl_file.name} to {dest}")
                    pkl_file.rename(dest)
                
                print(f"Extracted {len(pkl_files)} model files")
                return True
                
    except Exception as e:
        print(f"Extraction failed: {e}")
        return False

def main():
    """Main download function"""
    print("UFPS Model Downloader")
    print("=" * 40)
    
    # Create models directory
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check if models already exist
    existing_models = list(MODELS_DIR.glob("*.pkl"))
    if len(existing_models) >= 3:
        print(f"Models already present: {[m.name for m in existing_models]}")
        return 0
    
    # Try different download methods
    zip_path = None
    
    # Method 1: gdown (best for Google Drive)
    zip_path = download_with_gdown()
    
    # Method 2: wget
    if not zip_path or not zip_path.exists():
        zip_path = download_with_wget()
    
    # Method 3: Manual download instructions
    if not zip_path or not zip_path.exists():
        print("\n" + "=" * 40)
        print("Automatic download failed. Please download manually:")
        print("1. Go to: https://drive.google.com/file/d/1APIzVeI-4ZZCEuIRE1m6WYfSCaOsi_7_/view")
        print("2. Click 'Download' button")
        print(f"3. Extract the .pkl files to: {MODELS_DIR}")
        print("=" * 40)
        return 1
    
    # Extract models
    if extract_models(zip_path):
        print("\nModels downloaded successfully!")
        zip_path.unlink()  # Clean up zip file
        return 0
    else:
        print("\nFailed to extract models")
        return 1

if __name__ == "__main__":
    sys.exit(main())