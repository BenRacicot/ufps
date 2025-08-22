"""
Utility functions for UFPS
"""

import json
import subprocess
import shutil
from pathlib import Path
import platform

def find_ffmpeg():
    """Find ffmpeg and ffprobe executables"""
    # Check if in PATH
    ffmpeg_path = shutil.which('ffmpeg')
    ffprobe_path = shutil.which('ffprobe')
    
    if ffmpeg_path and ffprobe_path:
        return ffmpeg_path, ffprobe_path
    
    # Common locations on macOS
    if platform.system() == "Darwin":
        possible_paths = [
            '/usr/local/bin/ffmpeg',
            '/opt/homebrew/bin/ffmpeg',
            '/opt/local/bin/ffmpeg',
            str(Path.home() / '.ufps' / 'ffmpeg' / 'ffmpeg'),
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                ffprobe = Path(path).parent / 'ffprobe'
                if ffprobe.exists():
                    return str(path), str(ffprobe)
    
    return None, None

def get_video_info(video_path, ffprobe_path=None):
    """Get detailed video information"""
    ffprobe = ffprobe_path or shutil.which('ffprobe')
    if not ffprobe:
        raise RuntimeError("ffprobe not found")
    
    video_path = Path(video_path).resolve()
    
    cmd = [
        ffprobe,
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_format',
        '-show_streams',
        str(video_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"Failed to get video info: {result.stderr}")
    
    data = json.loads(result.stdout)
    
    # Find video stream
    video_stream = None
    audio_stream = None
    for stream in data.get('streams', []):
        if stream['codec_type'] == 'video' and not video_stream:
            video_stream = stream
        elif stream['codec_type'] == 'audio' and not audio_stream:
            audio_stream = stream
    
    if not video_stream:
        raise RuntimeError("No video stream found")
    
    # Calculate FPS
    fps_str = video_stream.get('r_frame_rate', '30/1')
    if '/' in fps_str:
        num, den = map(float, fps_str.split('/'))
        fps = num / den if den != 0 else 30.0
    else:
        fps = float(fps_str)
    
    # Get duration
    duration = float(data.get('format', {}).get('duration', 0))
    
    # File size
    file_size = Path(video_path).stat().st_size / (1024 * 1024)  # MB
    
    return {
        'fps': fps,
        'width': video_stream.get('width', 0),
        'height': video_stream.get('height', 0),
        'codec': video_stream.get('codec_name', 'unknown'),
        'duration': duration,
        'file_size': file_size,
        'bitrate': int(data.get('format', {}).get('bit_rate', 0)) // 1000,  # kbps
        'has_audio': audio_stream is not None,
        'audio_codec': audio_stream.get('codec_name', 'none') if audio_stream else 'none',
        'frame_count': int(video_stream.get('nb_frames', fps * duration))
    }

def get_video_files(directory="."):
    """Get all video files in the directory"""
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v'}
    video_files = []
    
    for file in Path(directory).iterdir():
        if file.suffix.lower() in video_extensions and file.is_file():
            video_files.append(file)
    
    return sorted(video_files, key=lambda x: x.name.lower())

def format_duration(seconds):
    """Format duration nicely"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

def get_fps_options(current_fps):
    """Get valid FPS upgrade options based on current FPS"""
    standard_fps = [24, 25, 30, 48, 50, 60, 90, 96, 100, 120, 144, 180, 240]
    
    options = []
    for target in standard_fps:
        if target > current_fps:
            scale_needed = target / current_fps
            
            # Check if achievable with RIFE (2x, 4x, 8x)
            if scale_needed <= 2:
                actual_fps = current_fps * 2
                scale = 2
            elif scale_needed <= 4:
                actual_fps = current_fps * 4
                scale = 4
            elif scale_needed <= 8:
                actual_fps = current_fps * 8
                scale = 8
            else:
                continue
            
            # Add option
            if abs(actual_fps - target) < 1:
                options.append({
                    'target': target,
                    'actual': actual_fps,
                    'scale': scale,
                    'exact': True
                })
            elif actual_fps <= 240:
                options.append({
                    'target': actual_fps,
                    'actual': actual_fps,
                    'scale': scale,
                    'exact': False
                })
    
    # Remove duplicates
    seen = set()
    unique_options = []
    for opt in options:
        key = (opt['actual'], opt['scale'])
        if key not in seen:
            seen.add(key)
            unique_options.append(opt)
    
    return sorted(unique_options, key=lambda x: x['actual'])