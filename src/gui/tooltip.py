"""
Tooltip system for MuXolotl
"""

import customtkinter as ctk
from tkinter import Toplevel, Label

class ToolTip:
    """
    Create a tooltip for a given widget with modern styling
    """
    def __init__(self, widget, text, delay=500):
        """
        Initialize tooltip
        
        Args:
            widget: Widget to attach tooltip to
            text: Tooltip text (can be multiline)
            delay: Delay in milliseconds before showing tooltip
        """
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0
        
        # Bind events
        self.widget.bind("<Enter>", self.schedule)
        self.widget.bind("<Leave>", self.hide)
        self.widget.bind("<Button>", self.hide)
    
    def schedule(self, event=None):
        """Schedule tooltip to appear after delay"""
        self.unschedule()
        self.id = self.widget.after(self.delay, self.show)
    
    def unschedule(self):
        """Cancel scheduled tooltip"""
        id_val = self.id
        self.id = None
        if id_val:
            self.widget.after_cancel(id_val)
    
    def show(self):
        """Display tooltip"""
        if self.tipwindow or not self.text:
            return
        
        # Calculate position
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        # Create tooltip window
        self.tipwindow = tw = Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        # Modern styling
        label = Label(
            tw,
            text=self.text,
            justify='left',
            background="#1e293b",
            foreground="#f1f5f9",
            relief='solid',
            borderwidth=1,
            font=("Segoe UI", 9),
            padx=10,
            pady=8
        )
        label.pack()
    
    def hide(self, event=None):
        """Hide tooltip"""
        self.unschedule()
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()


def create_tooltip(widget, text, delay=500):
    """
    Helper function to create tooltip
    
    Args:
        widget: Widget to attach tooltip to
        text: Tooltip text
        delay: Delay before showing (ms)
    
    Returns:
        ToolTip instance
    """
    return ToolTip(widget, text, delay)


# Tooltip texts database
TOOLTIPS = {
    # Audio tooltips
    "audio_format": """Output Format
━━━━━━━━━━━━━━━━━━━━━━━━━━
Choose the container format for your audio file.

Common formats:
• MP3 - Universal compatibility, lossy
• FLAC - Lossless, larger file size
• WAV - Uncompressed, largest size
• AAC/M4A - Modern, efficient compression
• OGG/OPUS - Open-source, great quality""",

    "audio_codec": """Audio Codec
━━━━━━━━━━━━━━━━━━━━━━━━━━
Determines how audio is encoded.

Options:
• copy (fast) - No re-encoding, instant
• auto - Smart codec selection
• Specific codecs - Manual control

Use 'copy' when just changing container!""",

    "audio_bitrate": """Audio Bitrate
━━━━━━━━━━━━━━━━━━━━━━━━━━
Controls audio quality and file size.

Guidelines:
• 128k - Acceptable for speech
• 192k - Good quality for music
• 256k - High quality
• 320k - Maximum MP3 quality
• Original - Keep source bitrate

Higher = Better quality + Larger file""",

    "audio_sample_rate": """Sample Rate
━━━━━━━━━━━━━━━━━━━━━━━━━━
Number of audio samples per second.

Common rates:
• 44100 Hz - CD quality standard
• 48000 Hz - Professional audio/video
• 96000 Hz - High-resolution audio

Usually best to keep 'Original'""",

    "audio_channels": """Audio Channels
━━━━━━━━━━━━━━━━━━━━━━━━━━
Number of audio channels.

Options:
• Original - Keep source channels
• Mono - Single channel (smaller file)
• Stereo - Two channels (L+R)

Most music uses Stereo""",

    # Video tooltips
    "video_format": """Output Video Format
━━━━━━━━━━━━━━━━━━━━━━━━━━
Container format for your video.

Popular formats:
• MP4 - Universal, best compatibility
• MKV - Feature-rich, supports everything
• AVI - Old but widely supported
• MOV - Apple standard
• WEBM - Web-optimized, modern""",

    "video_codec": """Video Codec
━━━━━━━━━━━━━━━━━━━━━━━━━━
How video is compressed/encoded.

Options:
• copy (fast) - No re-encoding (instant!)
• auto (recommended) - Smart selection
• GPU encoders - Hardware acceleration
  ⚡ 5-15x faster than CPU
• CPU encoders - Universal but slower

Hardware encoding requires GPU support.""",

    "speed_profile": """Speed Profile
━━━━━━━━━━━━━━━━━━━━━━━━━━
Balance between speed and quality.

Profiles:
⚡ Ultra Fast - 3-5x faster, lower quality
🚀 Fast - 2x faster, good quality
⚖️ Balanced - Optimal speed/quality
💎 High Quality - Slower, best quality

Recommendation: Start with Balanced""",

    "hwaccel": """Hardware Decode Acceleration
━━━━━━━━━━━━━━━━━━━━━━━━━━
Uses GPU to decode input video.

Options:
• auto - Automatic detection (recommended)
• none - CPU only
• Specific methods - Manual selection

Note: This is for DECODING input.
GPU ENCODING is separate (see Video Codec)""",

    "video_resolution": """Output Resolution
━━━━━━━━━━━━━━━━━━━━━━━━━━
Video dimensions in pixels.

Common resolutions:
• 3840x2160 - 4K Ultra HD
• 1920x1080 - Full HD (most common)
• 1280x720 - HD
• 854x480 - SD

Keep 'Original' to preserve quality
Downscaling reduces file size""",

    "video_fps": """Frame Rate (FPS)
━━━━━━━━━━━━━━━━━━━━━━━━━━
Frames per second in output video.

Common rates:
• 24 - Cinema standard
• 25 - PAL video standard
• 30 - NTSC, YouTube standard
• 60 - Smooth, gaming videos

Usually keep 'Original'
Higher FPS = larger file""",

    "video_bitrate": """Video Bitrate
━━━━━━━━━━━━━━━━━━━━━━━━━━
Data rate for video stream.

Guidelines (1080p):
• 2-3M - Low quality
• 5M - Good for most videos
• 8-10M - High quality
• 15M+ - Very high quality

Higher = Better quality + Larger file
'auto' uses quality-based encoding (CRF)"""
}