# UFPS - Ultra FPS Video Interpolation Tool

AI-powered frame rate enhancement for videos using RIFE (Real-time Intermediate Flow Estimation).

## Features

- 🎬 **Frame Rate Enhancement**: Increase video FPS by 2×, 4×, or 8×
- 🤖 **AI-Powered**: Uses RIFE neural network for smooth interpolation
- 🎯 **Smart Targeting**: Automatically suggests optimal frame rates (60, 120, 240 FPS)
- 🎨 **Quality Presets**: Choose between Maximum, High, Balanced, or Compressed output
- 📊 **Interactive CLI**: Beautiful terminal interface with progress tracking
- 🔧 **Self-Contained**: Manages its own Python environment and dependencies

## Requirements

- Python 3.8 or higher
- macOS or Linux (Windows support coming soon)
- ~500MB disk space for models and dependencies
- GPU recommended for faster processing (CPU fallback available)

## Installation

### Quick Install

```bash
# Clone the repository
git clone https://github.com/yourusername/ufps.git
cd ufps

# Run the installer
python install.py
```

The installer will:
1. Create an isolated Python environment at `~/.ufps/`
2. Download and install all dependencies (PyTorch, OpenCV, etc.)
3. Clone the RIFE repository
4. Download AI models (~13MB)
5. Set up FFmpeg (or provide installation instructions)
6. Create the `ufps` command in `~/.local/bin/`

### Add to PATH

After installation, add the binary directory to your PATH:

```bash
# For bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# For zsh (macOS default)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

## Usage

Simply run `ufps` in any directory containing video files:

```bash
cd /path/to/videos
ufps
```

The interactive CLI will:
1. Scan for video files in the current directory
2. Let you select a video to process
3. Show detailed video information
4. Offer FPS upgrade options
5. Let you choose quality settings
6. Process the video with real-time progress

### Example Workflow

```
$ ufps

╔════════════════════════════════════════╗
║              UFPS v1.0                 ║
║    Ultra FPS Video Interpolation       ║
║         Powered by RIFE AI             ║
╚════════════════════════════════════════╝

Select a video file:
❯ vacation_footage.mp4 (156.3 MB)
  presentation.mov (89.2 MB)
  
📹 vacation_footage.mp4
┌─────────────┬──────────────┐
│ Resolution  │ 1920×1080    │
│ Frame Rate  │ 30.00 FPS    │
│ Duration    │ 2m 15s       │
│ Codec       │ H264         │
└─────────────┴──────────────┘

🎬 Available FPS Upgrades
┌───┬────────────┬──────────────┬─────────────────────┐
│ # │ Target FPS │ Interpolation│ Details             │
├───┼────────────┼──────────────┼─────────────────────┤
│ 1 │ 60 FPS ⭐  │ 2×           │ Smooth motion       │
│ 2 │ 120 FPS 🎮 │ 4×           │ Gaming quality      │
│ 3 │ 240 FPS 🎬 │ 8×           │ Slow motion         │
└───┴────────────┴──────────────┴─────────────────────┘

Choose target frame rate: 60 FPS (2× interpolation) ⭐ Recommended
Select quality preset: ⭐ High (CRF 18) - Recommended

Processing...
[████████████████████] 100% Complete

✅ SUCCESS!
Output: vacation_footage_60fps.mp4
Size: 198.5 MB
Time: 3m 42s
```

## Supported Formats

- **Input**: MP4, AVI, MOV, MKV, WEBM, FLV, WMV, M4V
- **Output**: MP4 (H.264/H.265)

## Performance

Processing time depends on:
- Video resolution and duration
- Selected interpolation scale (2×, 4×, 8×)
- Hardware (GPU vs CPU)
- Quality settings

Typical performance:
- 1080p 1-minute video → 60 FPS: ~2-5 minutes (GPU) / ~10-20 minutes (CPU)
- 4K video: ~4× slower than 1080p

## Configuration

UFPS stores its configuration and models at:
- Installation: `~/.ufps/`
- Configuration: `~/.ufps/config.json`
- Models: `~/.ufps/models/`
- RIFE: `~/.ufps/RIFE/`

## Uninstallation

To completely remove UFPS:

```bash
python uninstall.py
```

This will remove:
- The `~/.ufps/` directory and all contents
- The `ufps` command from `~/.local/bin/`

## Troubleshooting

### FFmpeg not found
Install FFmpeg using your package manager:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Fedora
sudo dnf install ffmpeg
```

### CUDA/GPU Support
For GPU acceleration, install PyTorch with CUDA:
```bash
~/.ufps/venv/bin/pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Permission Errors
Ensure the installation directory is writable:
```bash
chmod -R u+w ~/.ufps
```

## License

MIT License

## Credits

- RIFE: [https://github.com/hzwer/Practical-RIFE](https://github.com/hzwer/Practical-RIFE)
- FFmpeg: [https://ffmpeg.org](https://ffmpeg.org)

## Contributing

Contributions are welcome! Please feel free to submit pull requests.

## Roadmap

- [ ] Windows support
- [ ] Batch processing mode
- [ ] Custom model support
- [ ] Hardware encoding (NVENC/VideoToolbox)
- [ ] Web interface
- [ ] Docker container