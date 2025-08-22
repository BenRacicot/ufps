"""
UFPS - Ultra FPS Video Interpolation Tool
AI-powered frame rate enhancement for videos
"""

__version__ = "1.0.0"
__author__ = "UFPS Contributors"

from .core import VideoProcessor, RIFEInterpolator
from .utils import get_video_info, find_ffmpeg

__all__ = [
    "VideoProcessor",
    "RIFEInterpolator", 
    "get_video_info",
    "find_ffmpeg",
]