"""GUI modules for MuXolotl - Modern redesign"""

from .about_window import AboutWindow
from .audio_tab import AudioTab
from .main_window import MuXolotlApp
from .settings_window import SettingsWindow
from .tooltip import TOOLTIPS, ToolTip, create_tooltip
from .video_tab import VideoTab

__all__ = [
    "TOOLTIPS",
    "AboutWindow",
    "AudioTab",
    "MuXolotlApp",
    "SettingsWindow",
    "ToolTip",
    "VideoTab",
    "create_tooltip",
]
