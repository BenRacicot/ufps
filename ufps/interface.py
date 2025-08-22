"""
Interactive CLI interface for UFPS
"""

import os
import sys
import time
import subprocess
from pathlib import Path

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
    from rich.text import Text
    from rich.align import Align
    from rich import box
    import questionary
    from questionary import Style
except ImportError:
    print("Installing required packages...")
    subprocess.run([sys.executable, "-m", "pip", "install", "rich", "questionary"], check=True)
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
    from rich.text import Text
    from rich.align import Align
    from rich import box
    import questionary
    from questionary import Style

from ufps.core import process_video
from ufps.utils import (
    find_ffmpeg, get_video_info, get_video_files,
    format_duration, get_fps_options
)

console = Console()

# Custom style for questionary
custom_style = Style([
    ('qmark', 'fg:#673ab7 bold'),
    ('question', 'bold'),
    ('answer', 'fg:#f44336 bold'),
    ('pointer', 'fg:#673ab7 bold'),
    ('highlighted', 'fg:#673ab7 bold'),
    ('selected', 'fg:#cc5454'),
    ('separator', 'fg:#cc5454'),
    ('instruction', 'fg:#abb2bf'),
    ('text', ''),
    ('disabled', 'fg:#858585 italic')
])


class InteractiveCLI:
    """Main interactive interface"""
    
    def __init__(self):
        self.ffmpeg_path, self.ffprobe_path = find_ffmpeg()
    
    def display_banner(self):
        """Show welcome banner"""
        console.clear()
        banner = Panel(
            Align.center(
                Text.from_markup(
                    "[bold magenta]UFPS[/bold magenta]\n"
                    "[cyan]Ultra FPS Video Interpolation[/cyan]\n"
                    "[dim]Powered by RIFE AI[/dim]"
                )
            ),
            box=box.DOUBLE,
            padding=(1, 2)
        )
        console.print(banner)
        console.print()
    
    def check_requirements(self):
        """Check if all requirements are met"""
        # Check FFmpeg
        if not self.ffmpeg_path or not self.ffprobe_path:
            console.print("[red]✗ FFmpeg not found![/red]")
            console.print("[yellow]Please run the installer: python install.py[/yellow]")
            return False
        
        # Check RIFE
        rife_dir = Path(os.environ.get("UFPS_RIFE_DIR", Path.home() / ".ufps" / "RIFE"))
        if not rife_dir.exists():
            console.print("[red]✗ RIFE not found![/red]")
            console.print("[yellow]Please run the installer: python install.py[/yellow]")
            return False
        
        # Check models
        models_dir = Path(os.environ.get("UFPS_MODELS_DIR", Path.home() / ".ufps" / "models"))
        if not models_dir.exists():
            console.print("[red]✗ Models not found![/red]")
            console.print("[yellow]Please run the installer: python install.py[/yellow]")
            return False
        
        return True
    
    def display_video_info(self, video_path, info):
        """Display video information in a nice table"""
        table = Table(title=f"📹 {video_path.name}", box=box.ROUNDED, title_style="bold magenta")
        
        table.add_column("Property", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")
        
        table.add_row("Resolution", f"{info['width']}×{info['height']}")
        table.add_row("Frame Rate", f"{info['fps']:.2f} FPS")
        table.add_row("Duration", format_duration(info['duration']))
        table.add_row("Total Frames", f"{info['frame_count']:,}")
        table.add_row("Video Codec", info['codec'].upper())
        table.add_row("Audio", f"✓ {info['audio_codec']}" if info['has_audio'] else "✗ No audio")
        table.add_row("Bitrate", f"{info['bitrate']:,} kbps")
        table.add_row("File Size", f"{info['file_size']:.1f} MB")
        
        console.print(table)
    
    def display_fps_options(self, options, current_fps):
        """Display FPS options in a nice format"""
        table = Table(title="🎬 Available FPS Upgrades", box=box.ROUNDED, title_style="bold green")
        
        table.add_column("#", style="dim", width=3)
        table.add_column("Target FPS", style="cyan", no_wrap=True)
        table.add_column("Interpolation", style="yellow")
        table.add_column("Details", style="white")
        
        for i, opt in enumerate(options, 1):
            target_str = f"{opt['actual']:.0f} FPS"
            scale_str = f"{opt['scale']}×"
            
            if opt['scale'] == 2:
                detail = "Adds 1 frame between each original"
            elif opt['scale'] == 4:
                detail = "Adds 3 frames between each original"
            else:
                detail = "Adds 7 frames between each original"
            
            # Add special markers
            if opt['actual'] == 60:
                target_str += " ⭐"
                detail += " (Smooth motion)"
            elif opt['actual'] == 120:
                target_str += " 🎮"
                detail += " (Gaming quality)"
            elif opt['actual'] == 240:
                target_str += " 🎬"
                detail += " (Slow motion)"
            
            table.add_row(str(i), target_str, scale_str, detail)
        
        console.print(table)
    
    def run(self):
        """Main CLI loop"""
        self.display_banner()
        
        if not self.check_requirements():
            sys.exit(1)
        
        # Get video files
        video_files = get_video_files()
        
        if not video_files:
            console.print("[red]No video files found in current directory![/red]")
            console.print("[dim]Supported: MP4, AVI, MOV, MKV, WEBM, FLV, WMV, M4V[/dim]")
            sys.exit(1)
        
        # Select video
        video_choices = []
        for v in video_files:
            size_mb = v.stat().st_size / 1024 / 1024
            display_name = v.name if len(v.name) <= 60 else v.name[:57] + "..."
            video_choices.append(f"{display_name} ({size_mb:.1f} MB)")
        
        selected_index = questionary.select(
            "Select a video file:",
            choices=video_choices,
            style=custom_style
        ).ask()
        
        if selected_index is None:
            console.print("[yellow]Cancelled[/yellow]")
            sys.exit(0)
        
        selected_video = video_files[video_choices.index(selected_index)]
        
        console.print()
        console.print(f"[green]Selected:[/green] {selected_video.name}")
        console.print()
        
        # Get video info
        with console.status("[bold green]Analyzing video..."):
            info = get_video_info(selected_video, self.ffprobe_path)
        
        self.display_video_info(selected_video, info)
        console.print()
        
        # Get FPS options
        fps_options = get_fps_options(info['fps'])
        
        if not fps_options:
            console.print("[red]This video is already at maximum supported FPS![/red]")
            sys.exit(0)
        
        self.display_fps_options(fps_options, info['fps'])
        console.print()
        
        # Select target FPS
        fps_choices = []
        for opt in fps_options:
            choice = f"{opt['actual']:.0f} FPS ({opt['scale']}× interpolation)"
            if opt['actual'] == 60:
                choice += " ⭐ Recommended"
            elif opt['actual'] == 120:
                choice += " 🎮 Gaming"
            elif opt['actual'] == 240:
                choice += " 🎬 Slow Motion"
            fps_choices.append(choice)
        
        selected_fps = questionary.select(
            "Choose target frame rate:",
            choices=fps_choices,
            style=custom_style
        ).ask()
        
        if selected_fps is None:
            console.print("[yellow]Cancelled[/yellow]")
            sys.exit(0)
        
        selected_option = fps_options[fps_choices.index(selected_fps)]
        
        # Quality selection
        quality_choice = questionary.select(
            "Select quality preset:",
            choices=[
                "🎬 Maximum (CRF 15) - Largest file",
                "⭐ High (CRF 18) - Recommended",
                "📱 Balanced (CRF 23) - Good quality, smaller file",
                "💾 Compressed (CRF 28) - Smallest file"
            ],
            style=custom_style
        ).ask()
        
        quality_map = {
            "🎬 Maximum (CRF 15) - Largest file": 15,
            "⭐ High (CRF 18) - Recommended": 18,
            "📱 Balanced (CRF 23) - Good quality, smaller file": 23,
            "💾 Compressed (CRF 28) - Smallest file": 28
        }
        quality = quality_map.get(quality_choice, 18)
        
        # Output filename
        default_output = selected_video.parent / f"{selected_video.stem}_{int(selected_option['actual'])}fps{selected_video.suffix}"
        
        use_custom = questionary.confirm(
            "Use custom output filename?",
            default=False,
            style=custom_style
        ).ask()
        
        if use_custom:
            custom_name = questionary.text(
                "Enter output filename:",
                default=str(default_output.name),
                style=custom_style
            ).ask()
            if '/' not in custom_name:
                output_path = selected_video.parent / custom_name
            else:
                output_path = Path(custom_name)
        else:
            output_path = default_output
        
        # Summary
        console.print()
        summary = Table(title="📋 Processing Summary", box=box.ROUNDED, title_style="bold cyan")
        summary.add_column("Setting", style="cyan")
        summary.add_column("Value", style="white")
        
        summary.add_row("Input", selected_video.name)
        summary.add_row("Current FPS", f"{info['fps']:.2f}")
        summary.add_row("Target FPS", f"{selected_option['actual']:.0f}")
        summary.add_row("Interpolation", f"{selected_option['scale']}×")
        summary.add_row("Quality", f"CRF {quality}")
        summary.add_row("Output", output_path.name)
        
        estimated_size = info['file_size'] * selected_option['scale'] * (0.8 if quality > 20 else 1.2)
        summary.add_row("Estimated Size", f"~{estimated_size:.1f} MB")
        
        console.print(summary)
        console.print()
        
        # Confirm
        if not questionary.confirm("Start processing?", default=True, style=custom_style).ask():
            console.print("[yellow]Cancelled[/yellow]")
            sys.exit(0)
        
        console.print()
        
        # Process video
        start_time = time.time()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Processing video...", total=100)
            
            def update_progress(msg, pct):
                progress.update(task, description=f"[cyan]{msg}", completed=pct)
            
            try:
                success = process_video(
                    selected_video,
                    output_path,
                    selected_option['scale'],
                    selected_option['actual'],
                    quality,
                    update_progress
                )
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                success = False
        
        elapsed = time.time() - start_time
        
        if success:
            console.print()
            output_size = output_path.stat().st_size / (1024 * 1024)
            
            success_panel = Panel(
                Align.center(
                    Text.from_markup(
                        f"[bold green]✅ SUCCESS![/bold green]\n\n"
                        f"[white]Output: {output_path.name}[/white]\n"
                        f"[cyan]Size: {output_size:.1f} MB[/cyan]\n"
                        f"[yellow]Time: {format_duration(elapsed)}[/yellow]"
                    )
                ),
                box=box.DOUBLE,
                border_style="green",
                padding=(1, 2)
            )
            console.print(success_panel)
            
            # Ask to open
            if questionary.confirm("Open the video?", default=True, style=custom_style).ask():
                if sys.platform == "darwin":
                    subprocess.run(["open", str(output_path)])
                elif sys.platform.startswith("linux"):
                    subprocess.run(["xdg-open", str(output_path)])
        else:
            console.print("[red]✗ Processing failed![/red]")
            sys.exit(1)