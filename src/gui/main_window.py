"""
Main application window for MuXolotl - Modern redesign
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import sys
from pathlib import Path
from PIL import Image

from .audio_tab import AudioTab
from .video_tab import VideoTab
from .settings_window import SettingsWindow
from .about_window import AboutWindow
from utils.config import Config
from utils.logger import get_logger

logger = get_logger()

# Modern color scheme
COLORS = {
    "primary": "#6366f1",
    "primary_hover": "#4f46e5",
    "secondary": "#8b5cf6",
    "success": "#10b981",
    "warning": "#f59e0b",
    "error": "#ef4444",
    "bg_dark": "#0f172a",
    "bg_medium": "#1e293b",
    "bg_light": "#334155",
    "text_primary": "#f1f5f9",
    "text_secondary": "#94a3b8",
    "border": "#475569"
}

# Set dark theme permanently
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ModernButton(ctk.CTkButton):
    """Modern styled button with gradient effect"""
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            corner_radius=8,
            border_width=0,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            **kwargs
        )

class MuXolotlApp:
    """Main application class with modern UI"""
    
    def __init__(self):
        """Initialize application"""
        self.config = Config()
        self.root = ctk.CTk()
        self.root.title("MuXolotl - Universal Media Converter")
        
        # Set fixed window size for better control
        window_width = 900
        window_height = 650
        
        # Center window
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(900, 650)
        self.root.maxsize(1400, 900)
        
        # Set window icon
        self.root.iconbitmap(self._get_resource_path("assets/icon.ico"))
        
        # Configure grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        self._setup_ui()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _get_resource_path(self, relative_path):
        """Get absolute path to resource (works for dev and PyInstaller)"""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        
        return os.path.join(base_path, relative_path)
    
    def _setup_ui(self):
        """Setup modern user interface"""
        # Main container
        main_container = ctk.CTkFrame(self.root, fg_color=COLORS["bg_dark"])
        main_container.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        main_container.grid_rowconfigure(1, weight=1)
        main_container.grid_columnconfigure(0, weight=1)
        
        # === TOP BAR ===
        top_bar = self._create_top_bar(main_container)
        top_bar.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        
        # === CONTENT AREA ===
        content_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(10, 15))
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)
        
        # Tab view with modern styling
        self.tabview = ctk.CTkTabview(
            content_frame,
            corner_radius=12,
            fg_color=COLORS["bg_medium"],
            segmented_button_fg_color=COLORS["bg_light"],
            segmented_button_selected_color=COLORS["primary"],
            segmented_button_selected_hover_color=COLORS["primary_hover"],
            segmented_button_unselected_color=COLORS["bg_light"],
            segmented_button_unselected_hover_color=COLORS["bg_medium"]
        )
        self.tabview.grid(row=0, column=0, sticky="nsew")
        
        # Create tabs
        audio_tab = self.tabview.add("🎵  Audio Converter")
        video_tab = self.tabview.add("🎬  Video Converter")
        
        # Initialize tab content
        self.audio_tab = AudioTab(audio_tab, self.config)
        self.video_tab = VideoTab(video_tab, self.config)
    
    def _create_top_bar(self, parent):
        """Create modern top bar"""
        top_bar = ctk.CTkFrame(
            parent, 
            height=70, 
            fg_color=COLORS["bg_medium"],
            corner_radius=0
        )
        
        # Left side - Logo and title
        left_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        left_frame.pack(side="left", padx=20, pady=15)
        
        # Logo/Icon
        icon_image = Image.open(self._get_resource_path("assets/icon.ico"))
        # Resize to appropriate size
        icon_image = icon_image.resize((40, 40), Image.Resampling.LANCZOS)
        icon_photo = ctk.CTkImage(light_image=icon_image, dark_image=icon_image, size=(40, 40))
                
        logo_label = ctk.CTkLabel(
            left_frame,
            image=icon_photo,
            text=""
        )
        logo_label.pack(side="left", padx=(0, 10))
        
        # Title
        title_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        title_frame.pack(side="left")
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="MuXolotl",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        title_label.pack(anchor="w")
        
        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="Universal Media Converter",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        )
        subtitle_label.pack(anchor="w")
        
        # Right side - Controls
        right_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        right_frame.pack(side="right", padx=20, pady=15)
        
        # Info/About button (small icon button)
        info_btn = ctk.CTkButton(
            right_frame,
            text="ⓘ",
            command=self._open_about,
            width=35,
            height=35,
            corner_radius=8,
            fg_color=COLORS["bg_light"],
            hover_color=COLORS["primary"],
            font=ctk.CTkFont(size=16)
        )
        info_btn.pack(side="right", padx=(5, 0))
        
        # Settings button
        settings_btn = ctk.CTkButton(
            right_frame,
            text="⚙️ Settings",
            command=self._open_settings,
            width=100,
            height=35,
            corner_radius=8,
            fg_color=COLORS["bg_light"],
            hover_color=COLORS["border"],
            font=ctk.CTkFont(size=12)
        )
        settings_btn.pack(side="right", padx=5)
        
        return top_bar
    
    def _open_about(self):
        """Open about window"""
        AboutWindow(self.root)
    
    def _open_settings(self):
        """Open settings window"""
        SettingsWindow(self.root, self.config)
    
    def _on_closing(self):
        """Handle window closing"""
        self.config.save()
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        """Run application"""
        logger.info("Starting MuXolotl GUI")
        self.root.mainloop()