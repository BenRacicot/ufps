"""
Core video processing and interpolation functionality
"""

import os
import subprocess
import shutil
import tempfile
from pathlib import Path
import math
from datetime import datetime

class VideoProcessor:
    """Handles video extraction and encoding"""
    
    def __init__(self, ffmpeg_path=None, ffprobe_path=None):
        self.ffmpeg = ffmpeg_path or shutil.which("ffmpeg")
        self.ffprobe = ffprobe_path or shutil.which("ffprobe")
        
        if not self.ffmpeg or not self.ffprobe:
            raise RuntimeError("FFmpeg not found. Please install ffmpeg.")
    
    def extract_frames(self, video_path, output_dir, quality=1):
        """Extract frames from video"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            self.ffmpeg,
            '-i', str(video_path),
            '-qscale:v', str(quality),
            '-qmin', '1',
            str(output_dir / "frame_%08d.png"),
            '-loglevel', 'error'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to extract frames: {result.stderr}")
        
        frames = list(output_dir.glob("*.png"))
        return len(frames)
    
    def extract_audio(self, video_path, output_path):
        """Extract audio track from video"""
        cmd = [
            self.ffmpeg,
            '-i', str(video_path),
            '-vn',
            '-acodec', 'copy',
            str(output_path),
            '-loglevel', 'error',
            '-y'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return output_path if Path(output_path).exists() else None
    
    def encode_video(self, frames_dir, output_path, fps, audio_path=None, crf=18):
        """Encode frames to video"""
        frames_dir = Path(frames_dir)
        
        if audio_path and Path(audio_path).exists():
            cmd = [
                self.ffmpeg,
                '-r', str(fps),
                '-i', str(frames_dir / "frame_%08d.png"),
                '-i', str(audio_path),
                '-c:v', 'libx264',
                '-crf', str(crf),
                '-preset', 'slow',
                '-pix_fmt', 'yuv420p',
                '-c:a', 'copy',
                str(output_path),
                '-loglevel', 'error',
                '-y'
            ]
        else:
            cmd = [
                self.ffmpeg,
                '-r', str(fps),
                '-i', str(frames_dir / "frame_%08d.png"),
                '-c:v', 'libx264',
                '-crf', str(crf),
                '-preset', 'slow',
                '-pix_fmt', 'yuv420p',
                str(output_path),
                '-loglevel', 'error',
                '-y'
            ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to encode video: {result.stderr}")
        
        return output_path


class RIFEInterpolator:
    """Handles RIFE model interpolation"""
    
    def __init__(self, rife_dir=None, models_dir=None):
        # Use environment variables or defaults
        self.rife_dir = Path(rife_dir or os.environ.get("UFPS_RIFE_DIR", Path.home() / ".ufps" / "RIFE"))
        self.models_dir = Path(models_dir or os.environ.get("UFPS_MODELS_DIR", Path.home() / ".ufps" / "models"))
        
        if not self.rife_dir.exists():
            raise RuntimeError(f"RIFE not found at {self.rife_dir}")
        
        if not self.models_dir.exists():
            raise RuntimeError(f"Models not found at {self.models_dir}")
        
        # Add RIFE to Python path
        sys.path.insert(0, str(self.rife_dir))
    
    def interpolate(self, input_dir, output_dir, scale=2):
        """Run RIFE interpolation"""
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Calculate exponent for RIFE (2^exp = scale)
        exp_value = int(math.log2(scale))
        
        # Save current directory
        original_dir = os.getcwd()
        
        try:
            # Change to RIFE directory
            os.chdir(self.rife_dir)
            
            # Try different inference scripts
            scripts = ["inference_video.py", "inference_img.py", "inference.py"]
            
            for script in scripts:
                script_path = self.rife_dir / script
                if not script_path.exists():
                    continue
                
                cmd = [
                    sys.executable, str(script_path),
                    '--img', str(input_dir),
                    '--output', str(output_dir),
                    '--exp', str(exp_value),
                    '--modelDir', str(self.models_dir)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    # Check if output was generated
                    output_frames = list(output_dir.glob("*.png"))
                    if output_frames:
                        return len(output_frames)
                
                # Try without modelDir parameter
                cmd = [
                    sys.executable, str(script_path),
                    '--img', str(input_dir),
                    '--output', str(output_dir),
                    '--exp', str(exp_value)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    output_frames = list(output_dir.glob("*.png"))
                    if output_frames:
                        return len(output_frames)
            
            raise RuntimeError("RIFE interpolation failed - no compatible script found")
            
        finally:
            # Restore directory
            os.chdir(original_dir)


def process_video(input_path, output_path, scale=2, target_fps=60, crf=18, progress_callback=None):
    """Main processing pipeline"""
    input_path = Path(input_path).resolve()
    output_path = Path(output_path).resolve()
    
    # Create temporary directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_stem = "".join(c if c.isalnum() or c in "._-" else "_" for c in input_path.stem[:20])
    temp_dir = Path(tempfile.mkdtemp(prefix=f"ufps_{safe_stem}_{timestamp}_"))
    
    try:
        frames_dir = temp_dir / "frames"
        interp_dir = temp_dir / "interpolated"
        
        # Initialize processors
        video_proc = VideoProcessor()
        rife_proc = RIFEInterpolator()
        
        # Step 1: Extract frames
        if progress_callback:
            progress_callback("Extracting frames...", 0)
        frame_count = video_proc.extract_frames(input_path, frames_dir)
        
        # Step 2: Run interpolation
        if progress_callback:
            progress_callback(f"Running {scale}× interpolation...", 25)
        interp_count = rife_proc.interpolate(frames_dir, interp_dir, scale)
        
        # Step 3: Extract audio
        if progress_callback:
            progress_callback("Processing audio...", 50)
        audio_path = temp_dir / "audio.aac"
        audio = video_proc.extract_audio(input_path, audio_path)
        
        # Step 4: Encode final video
        if progress_callback:
            progress_callback("Encoding final video...", 75)
        video_proc.encode_video(interp_dir, output_path, target_fps, audio, crf)
        
        if progress_callback:
            progress_callback("Complete!", 100)
        
        return True
        
    finally:
        # Clean up
        if temp_dir.exists():
            shutil.rmtree(temp_dir)