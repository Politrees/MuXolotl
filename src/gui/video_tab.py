"""Modern Video conversion tab for MuXolotl - WITH SPEED PROFILES AND TOOLTIPS
"""

import os
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from core.format_detector import FormatDetector
from core.video_converter import VideoConverter
from utils.logger import get_logger

from .tooltip import TOOLTIPS, create_tooltip

logger = get_logger()

COLORS = {
    "primary": "#6366f1",
    "primary_hover": "#4f46e5",
    "success": "#10b981",
    "warning": "#f59e0b",
    "error": "#ef4444",
    "bg_dark": "#0f172a",
    "bg_medium": "#1e293b",
    "bg_light": "#334155",
    "text_primary": "#f1f5f9",
    "text_secondary": "#94a3b8",
    "border": "#475569",
}

class VideoTab:
    """Modern Video conversion tab with hardware encoding"""

    def __init__(self, parent, config):
        """Initialize video tab"""
        self.parent = parent
        self.config = config
        self.converter = VideoConverter()
        self.detector = FormatDetector()
        self.input_file = None
        self.is_converting = False

        # Get hardware encoder info
        self.encoder_info = self.converter.get_encoder_info()
        logger.info(f"Available encoders: {self.encoder_info}")

        # Initialize hardware acceleration detection (silent)
        logger.debug("Detecting hardware acceleration...")
        try:
            self.working_hwaccels = self.detector.get_working_hwaccels()
        except Exception as e:
            logger.warning(f"Hardware acceleration detection failed: {e}")
            self.working_hwaccels = set()

        self._setup_ui()

    def _setup_ui(self):
        """Setup modern UI - compact and beautiful"""
        # Configure grid
        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_columnconfigure(1, weight=2)

        # === LEFT PANEL - File & Mode ===
        left_panel = ctk.CTkFrame(self.parent, fg_color=COLORS["bg_light"], corner_radius=10)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)

        # File section
        file_header = ctk.CTkLabel(
            left_panel,
            text="📁 Input Video",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_primary"],
        )
        file_header.pack(pady=(15, 10), padx=15)

        # File display area
        file_display_frame = ctk.CTkFrame(left_panel, fg_color=COLORS["bg_medium"], corner_radius=8, height=120)
        file_display_frame.pack(fill="x", padx=15, pady=(0, 10))
        file_display_frame.pack_propagate(False)

        self.file_icon_label = ctk.CTkLabel(
            file_display_frame,
            text="🎬",
            font=ctk.CTkFont(size=40),
        )
        self.file_icon_label.pack(pady=(10, 5))

        self.file_name_label = ctk.CTkLabel(
            file_display_frame,
            text="No file selected",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"],
            wraplength=200,
        )
        self.file_name_label.pack(pady=5)

        self.file_info_label = ctk.CTkLabel(
            file_display_frame,
            text="",
            font=ctk.CTkFont(size=9),
            text_color=COLORS["text_secondary"],
        )
        self.file_info_label.pack()

        # File buttons
        file_btn_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        file_btn_frame.pack(fill="x", padx=15, pady=(0, 15))

        select_btn = ctk.CTkButton(
            file_btn_frame,
            text="📂 Select Video",
            command=self._select_file,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            height=38,
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        select_btn.pack(fill="x", pady=2)

        clear_btn = ctk.CTkButton(
            file_btn_frame,
            text="🗑️ Clear",
            command=self._clear_file,
            fg_color=COLORS["bg_dark"],
            hover_color=COLORS["border"],
            height=35,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
        )
        clear_btn.pack(fill="x", pady=2)

        # Separator
        separator1 = ctk.CTkFrame(left_panel, height=2, fg_color=COLORS["border"])
        separator1.pack(fill="x", padx=15, pady=10)

        # Conversion mode
        mode_header = ctk.CTkLabel(
            left_panel,
            text="🎯 Conversion Mode",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_primary"],
        )
        mode_header.pack(pady=(5, 10), padx=15)

        self.mode_var = ctk.StringVar(value="video_to_video")

        mode_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        mode_frame.pack(fill="x", padx=15, pady=(0, 15))

        video_radio = ctk.CTkRadioButton(
            mode_frame,
            text="Video to Video",
            variable=self.mode_var,
            value="video_to_video",
            command=self._update_mode,
            font=ctk.CTkFont(size=12),
            radiobutton_width=20,
            radiobutton_height=20,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
        )
        video_radio.pack(anchor="w", pady=5)

        audio_radio = ctk.CTkRadioButton(
            mode_frame,
            text="Extract Audio Only",
            variable=self.mode_var,
            value="video_to_audio",
            command=self._update_mode,
            font=ctk.CTkFont(size=12),
            radiobutton_width=20,
            radiobutton_height=20,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
        )
        audio_radio.pack(anchor="w", pady=5)

        # === RIGHT PANEL - Settings ===
        right_panel = ctk.CTkFrame(self.parent, fg_color=COLORS["bg_light"], corner_radius=10)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)

        # Scrollable settings
        scroll_frame = ctk.CTkScrollableFrame(
            right_panel,
            fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["primary"],
        )
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Settings header
        settings_header = ctk.CTkLabel(
            scroll_frame,
            text="⚙️ Conversion Settings",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_primary"],
        )
        settings_header.pack(pady=(5, 10), anchor="w")

        # === SPEED PROFILE (for video mode only) ===
        self.profile_frame = ctk.CTkFrame(scroll_frame, fg_color=COLORS["bg_medium"], corner_radius=8)
        # Will be shown/hidden in _update_mode

        profile_header_frame = ctk.CTkFrame(self.profile_frame, fg_color="transparent")
        profile_header_frame.pack(fill="x", padx=15, pady=(10, 5))

        profile_header = ctk.CTkLabel(
            profile_header_frame,
            text="⚡ Speed Profile",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text_primary"],
        )
        profile_header.pack(side="left")

        # Add tooltip to header
        create_tooltip(profile_header_frame, TOOLTIPS["speed_profile"])

        profile_options_frame = ctk.CTkFrame(self.profile_frame, fg_color="transparent")
        profile_options_frame.pack(fill="x", padx=15, pady=(0, 10))

        self.profile_var = ctk.StringVar(value="Balanced")

        profiles = [
            ("⚡ Ultra Fast", "Ultra Fast (lower quality)"),
            ("🚀 Fast", "Fast"),
            ("⚖️ Balanced", "Balanced"),
            ("💎 High Quality", "High Quality (slower)"),
        ]

        for icon_text, value in profiles:
            radio = ctk.CTkRadioButton(
                profile_options_frame,
                text=icon_text,
                variable=self.profile_var,
                value=value,
                font=ctk.CTkFont(size=11),
                radiobutton_width=18,
                radiobutton_height=18,
                fg_color=COLORS["primary"],
                hover_color=COLORS["primary_hover"],
            )
            radio.pack(anchor="w", pady=3)
            create_tooltip(radio, TOOLTIPS["speed_profile"])

        # Settings container
        self.settings_container = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        self.settings_container.pack(fill="x", pady=5)

        # === FORMAT (always visible) ===
        format_label_frame = ctk.CTkFrame(self.settings_container, fg_color="transparent")
        format_label_frame.pack(fill="x", pady=5)

        format_label = ctk.CTkLabel(
            format_label_frame,
            text="Output Format:",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
            width=120,
            anchor="w",
        )
        format_label.pack(side="left", padx=(0, 10))
        create_tooltip(format_label, TOOLTIPS["video_format"])

        self.format_var = ctk.StringVar(value=self.config.get("video.default_format", "mp4"))
        self.format_menu = ctk.CTkOptionMenu(
            format_label_frame,
            variable=self.format_var,
            values=self.converter.get_supported_formats(),
            fg_color=COLORS["bg_medium"],
            button_color=COLORS["primary"],
            button_hover_color=COLORS["primary_hover"],
            dropdown_fg_color=COLORS["bg_dark"],
            font=ctk.CTkFont(size=11),
            dropdown_font=ctk.CTkFont(size=11),
            height=32,
            corner_radius=6,
        )
        self.format_menu.pack(side="left", fill="x", expand=True)
        create_tooltip(self.format_menu, TOOLTIPS["video_format"])

        # === VIDEO CODEC (hidden in audio mode) ===
        self.video_codec_frame = ctk.CTkFrame(self.settings_container, fg_color="transparent")
        self.video_codec_frame.pack(fill="x", pady=5)

        video_codec_label = ctk.CTkLabel(
            self.video_codec_frame,
            text="Video Codec:",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
            width=120,
            anchor="w",
        )
        video_codec_label.pack(side="left", padx=(0, 10))
        create_tooltip(video_codec_label, TOOLTIPS["video_codec"])

        # Build codec list with hardware encoders first
        video_codecs = ["copy (fast)", "auto (recommended)"]
        if self.converter.hardware_encoders["h264"]:
            hw_codec = self.converter.hardware_encoders["h264"]
            if hw_codec != "libx264":
                video_codecs.append(f"{hw_codec} (GPU)")
        video_codecs.extend(["libx264 (CPU)", "libx265 (HEVC)", "libvpx-vp9"])

        self.video_codec_var = ctk.StringVar(value="copy (fast)")
        self.video_codec_menu = ctk.CTkOptionMenu(
            self.video_codec_frame,
            variable=self.video_codec_var,
            values=video_codecs,
            fg_color=COLORS["bg_medium"],
            button_color=COLORS["primary"],
            button_hover_color=COLORS["primary_hover"],
            dropdown_fg_color=COLORS["bg_dark"],
            font=ctk.CTkFont(size=11),
            dropdown_font=ctk.CTkFont(size=11),
            height=32,
            corner_radius=6,
        )
        self.video_codec_menu.pack(side="left", fill="x", expand=True)
        create_tooltip(self.video_codec_menu, TOOLTIPS["video_codec"])

        # === AUDIO CODEC (always visible) ===
        self.audio_codec_frame = ctk.CTkFrame(self.settings_container, fg_color="transparent")
        self.audio_codec_frame.pack(fill="x", pady=5)

        audio_codec_label = ctk.CTkLabel(
            self.audio_codec_frame,
            text="Audio Codec:",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
            width=120,
            anchor="w",
        )
        audio_codec_label.pack(side="left", padx=(0, 10))
        create_tooltip(audio_codec_label, TOOLTIPS["audio_codec"])

        self.audio_codec_var = ctk.StringVar(value="copy (fast)")
        self.audio_codec_menu = ctk.CTkOptionMenu(
            self.audio_codec_frame,
            variable=self.audio_codec_var,
            values=["copy (fast)", "auto", "aac", "libmp3lame", "libopus", "libvorbis"],
            fg_color=COLORS["bg_medium"],
            button_color=COLORS["primary"],
            button_hover_color=COLORS["primary_hover"],
            dropdown_fg_color=COLORS["bg_dark"],
            font=ctk.CTkFont(size=11),
            dropdown_font=ctk.CTkFont(size=11),
            height=32,
            corner_radius=6,
        )
        self.audio_codec_menu.pack(side="left", fill="x", expand=True)
        create_tooltip(self.audio_codec_menu, TOOLTIPS["audio_codec"])

        # === AUDIO BITRATE (always visible) ===
        self.audio_bitrate_frame = ctk.CTkFrame(self.settings_container, fg_color="transparent")
        self.audio_bitrate_frame.pack(fill="x", pady=5)

        audio_bitrate_label = ctk.CTkLabel(
            self.audio_bitrate_frame,
            text="Audio Bitrate:",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
            width=120,
            anchor="w",
        )
        audio_bitrate_label.pack(side="left", padx=(0, 10))
        create_tooltip(audio_bitrate_label, TOOLTIPS["audio_bitrate"])

        self.audio_bitrate_var = ctk.StringVar(value="Original")
        self.audio_bitrate_menu = ctk.CTkOptionMenu(
            self.audio_bitrate_frame,
            variable=self.audio_bitrate_var,
            values=["Original", "96k", "128k", "160k", "192k", "256k", "320k"],
            fg_color=COLORS["bg_medium"],
            button_color=COLORS["primary"],
            button_hover_color=COLORS["primary_hover"],
            dropdown_fg_color=COLORS["bg_dark"],
            font=ctk.CTkFont(size=11),
            dropdown_font=ctk.CTkFont(size=11),
            height=32,
            corner_radius=6,
        )
        self.audio_bitrate_menu.pack(side="left", fill="x", expand=True)
        create_tooltip(self.audio_bitrate_menu, TOOLTIPS["audio_bitrate"])

        # === HARDWARE ACCELERATION (for video mode only) ===
        self.hwaccel_frame = ctk.CTkFrame(self.settings_container, fg_color="transparent")
        self.hwaccel_frame.pack(fill="x", pady=5)

        hwaccel_label = ctk.CTkLabel(
            self.hwaccel_frame,
            text="HW Decode:",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
            width=120,
            anchor="w",
        )
        hwaccel_label.pack(side="left", padx=(0, 10))
        create_tooltip(hwaccel_label, TOOLTIPS["hwaccel"])

        if self.working_hwaccels:
            hwaccels = ["auto", "none"] + sorted(list(self.working_hwaccels))
            default_hwaccel = self.config.get("advanced.hardware_acceleration", "auto")
        else:
            hwaccels = ["none"]
            default_hwaccel = "none"

        self.hwaccel_var = ctk.StringVar(value=default_hwaccel)
        self.hwaccel_menu = ctk.CTkOptionMenu(
            self.hwaccel_frame,
            variable=self.hwaccel_var,
            values=hwaccels,
            fg_color=COLORS["bg_medium"],
            button_color=COLORS["primary"],
            button_hover_color=COLORS["primary_hover"],
            dropdown_fg_color=COLORS["bg_dark"],
            font=ctk.CTkFont(size=11),
            dropdown_font=ctk.CTkFont(size=11),
            height=32,
            corner_radius=6,
        )
        self.hwaccel_menu.pack(side="left", fill="x", expand=True)
        create_tooltip(self.hwaccel_menu, TOOLTIPS["hwaccel"])

        # === ADVANCED OPTIONS ===
        self.advanced_frame = ctk.CTkFrame(scroll_frame, fg_color=COLORS["bg_medium"], corner_radius=8)
        self.advanced_frame.pack(fill="x", pady=15)

        advanced_header = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
        advanced_header.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(
            advanced_header,
            text="🔧 Advanced Options",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text_primary"],
        ).pack(side="left")

        self.show_advanced = False
        self.advanced_toggle_btn = ctk.CTkButton(
            advanced_header,
            text="▼ Show",
            command=self._toggle_advanced,
            width=80,
            height=28,
            corner_radius=6,
            fg_color=COLORS["bg_light"],
            hover_color=COLORS["border"],
            font=ctk.CTkFont(size=11),
        )
        self.advanced_toggle_btn.pack(side="right")

        # Advanced options container (initially hidden)
        self.advanced_options = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")

        # === SEPARATOR ===
        separator2 = ctk.CTkFrame(scroll_frame, height=2, fg_color=COLORS["border"])
        separator2.pack(fill="x", pady=15)

        # === OUTPUT DIRECTORY ===
        output_label = ctk.CTkLabel(
            scroll_frame,
            text="💾 Output Directory",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_primary"],
        )
        output_label.pack(pady=(5, 10), anchor="w")

        output_frame = ctk.CTkFrame(scroll_frame, fg_color=COLORS["bg_medium"], corner_radius=8)
        output_frame.pack(fill="x", pady=5)

        self.output_dir_var = ctk.StringVar(value=self.config.get("last_output_dir"))

        output_entry = ctk.CTkEntry(
            output_frame,
            textvariable=self.output_dir_var,
            font=ctk.CTkFont(size=11),
            fg_color=COLORS["bg_medium"],
            border_width=0,
            height=35,
        )
        output_entry.pack(side="left", fill="x", expand=True, padx=10, pady=5)

        browse_btn = ctk.CTkButton(
            output_frame,
            text="📂",
            command=self._browse_output_dir,
            width=40,
            height=35,
            corner_radius=6,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            font=ctk.CTkFont(size=16),
        )
        browse_btn.pack(side="right", padx=5, pady=5)

        # === PROGRESS SECTION ===
        progress_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        progress_frame.pack(fill="x", pady=15)

        self.status_label = ctk.CTkLabel(
            progress_frame,
            text="Ready to convert",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
        )
        self.status_label.pack(pady=(0, 8))

        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            height=8,
            corner_radius=4,
            fg_color=COLORS["bg_medium"],
            progress_color=COLORS["primary"],
        )
        self.progress_bar.pack(fill="x", pady=5)
        self.progress_bar.set(0)

        # === CONVERT BUTTONS ===
        convert_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        convert_frame.pack(fill="x", pady=(10, 5))

        # Convert button
        self.convert_button = ctk.CTkButton(
            convert_frame,
            text="🚀 START CONVERSION",
            command=self._start_conversion,
            height=50,
            corner_radius=10,
            fg_color=COLORS["success"],
            hover_color="#059669",
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self.convert_button.pack(fill="x")

        # Cancel button (initially hidden)
        self.cancel_button = ctk.CTkButton(
            convert_frame,
            text="⛔ CANCEL",
            command=self._cancel_conversion,
            height=45,
            corner_radius=10,
            fg_color=COLORS["warning"],
            hover_color="#d97706",
            font=ctk.CTkFont(size=14, weight="bold"),
        )

        # Initialize mode
        self._update_mode()

    def _update_mode(self):
        """Update UI based on conversion mode"""
        mode = self.mode_var.get()

        if mode == "video_to_video":
            # Update format options to video formats
            formats = self.converter.get_supported_formats()
            default = self.config.get("video.default_format", "mp4")
            if default not in formats:
                default = formats[0] if formats else "mp4"

            # Update format menu
            self.format_menu.configure(values=formats)
            self.format_var.set(default)

            # Show video-specific options
            self.profile_frame.pack(fill="x", pady=(0, 10), before=self.settings_container)
            self.video_codec_frame.pack(fill="x", pady=5)
            self.hwaccel_frame.pack(fill="x", pady=5)

        else:  # video_to_audio
            # Update format options to audio formats
            from core.audio_converter import AudioConverter
            audio_converter = AudioConverter()
            formats = audio_converter.get_supported_formats()
            default = self.config.get("audio.default_format", "mp3")
            if default not in formats:
                default = formats[0] if formats else "mp3"

            # Update format menu
            self.format_menu.configure(values=formats)
            self.format_var.set(default)

            # Hide video-specific options
            self.profile_frame.pack_forget()
            self.video_codec_frame.pack_forget()
            self.hwaccel_frame.pack_forget()

    def _toggle_advanced(self):
        """Toggle advanced options visibility"""
        self.show_advanced = not self.show_advanced

        if self.show_advanced:
            self.advanced_options.pack(fill="x", padx=15, pady=(0, 10))
            self.advanced_toggle_btn.configure(text="▲ Hide")

            # Add advanced options if not already added
            if len(self.advanced_options.winfo_children()) == 0:
                # Resolution
                res_frame = ctk.CTkFrame(self.advanced_options, fg_color="transparent")
                res_frame.pack(fill="x", pady=5)

                res_label = ctk.CTkLabel(
                    res_frame,
                    text="Resolution:",
                    font=ctk.CTkFont(size=12),
                    text_color=COLORS["text_secondary"],
                    width=120,
                    anchor="w",
                )
                res_label.pack(side="left", padx=(0, 10))
                create_tooltip(res_label, TOOLTIPS["video_resolution"])

                self.resolution_var = ctk.StringVar(value="Original")
                res_menu = ctk.CTkOptionMenu(
                    res_frame,
                    variable=self.resolution_var,
                    values=["Original", "3840x2160 (4K)", "2560x1440 (2K)", "1920x1080 (FHD)", "1280x720 (HD)", "854x480 (SD)"],
                    fg_color=COLORS["bg_medium"],
                    button_color=COLORS["primary"],
                    button_hover_color=COLORS["primary_hover"],
                    dropdown_fg_color=COLORS["bg_dark"],
                    font=ctk.CTkFont(size=11),
                    height=32,
                    corner_radius=6,
                )
                res_menu.pack(side="left", fill="x", expand=True)
                create_tooltip(res_menu, TOOLTIPS["video_resolution"])

                # FPS
                fps_frame = ctk.CTkFrame(self.advanced_options, fg_color="transparent")
                fps_frame.pack(fill="x", pady=5)

                fps_label = ctk.CTkLabel(
                    fps_frame,
                    text="Frame Rate:",
                    font=ctk.CTkFont(size=12),
                    text_color=COLORS["text_secondary"],
                    width=120,
                    anchor="w",
                )
                fps_label.pack(side="left", padx=(0, 10))
                create_tooltip(fps_label, TOOLTIPS["video_fps"])

                self.fps_var = ctk.StringVar(value="Original")
                fps_menu = ctk.CTkOptionMenu(
                    fps_frame,
                    variable=self.fps_var,
                    values=["Original", "24", "25", "30", "50", "60"],
                    fg_color=COLORS["bg_medium"],
                    button_color=COLORS["primary"],
                    button_hover_color=COLORS["primary_hover"],
                    dropdown_fg_color=COLORS["bg_dark"],
                    font=ctk.CTkFont(size=11),
                    height=32,
                    corner_radius=6,
                )
                fps_menu.pack(side="left", fill="x", expand=True)
                create_tooltip(fps_menu, TOOLTIPS["video_fps"])

                # Video bitrate
                vbitrate_frame = ctk.CTkFrame(self.advanced_options, fg_color="transparent")
                vbitrate_frame.pack(fill="x", pady=5)

                vbitrate_label = ctk.CTkLabel(
                    vbitrate_frame,
                    text="Video Bitrate:",
                    font=ctk.CTkFont(size=12),
                    text_color=COLORS["text_secondary"],
                    width=120,
                    anchor="w",
                )
                vbitrate_label.pack(side="left", padx=(0, 10))
                create_tooltip(vbitrate_label, TOOLTIPS["video_bitrate"])

                self.video_bitrate_var = ctk.StringVar(value="auto")
                vbitrate_menu = ctk.CTkOptionMenu(
                    vbitrate_frame,
                    variable=self.video_bitrate_var,
                    values=["auto", "1M", "2M", "3M", "5M", "8M", "10M", "15M"],
                    fg_color=COLORS["bg_medium"],
                    button_color=COLORS["primary"],
                    button_hover_color=COLORS["primary_hover"],
                    dropdown_fg_color=COLORS["bg_dark"],
                    font=ctk.CTkFont(size=11),
                    height=32,
                    corner_radius=6,
                )
                vbitrate_menu.pack(side="left", fill="x", expand=True)
                create_tooltip(vbitrate_menu, TOOLTIPS["video_bitrate"])
        else:
            self.advanced_options.pack_forget()
            self.advanced_toggle_btn.configure(text="▼ Show")

    def _select_file(self):
        """Select video file"""
        file = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[
                ("Video Files", "*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.webm *.mpeg *.mpg *.m4v *.3gp"),
                ("All Files", "*.*"),
            ],
        )

        if file:
            self.input_file = file
            self._update_file_display()

    def _clear_file(self):
        """Clear selected file"""
        self.input_file = None
        self._update_file_display()

    def _update_file_display(self):
        """Update file display"""
        if self.input_file:
            filename = Path(self.input_file).name

            # Truncate long filenames
            if len(filename) > 30:
                display_name = filename[:27] + "..."
            else:
                display_name = filename

            self.file_name_label.configure(text=display_name)

            # Get file info
            try:
                size = os.path.getsize(self.input_file) / (1024 * 1024)
                info_text = f"Size: {size:.1f} MB"

                # Try to get video info
                file_info = self.converter.get_file_info(self.input_file)
                if file_info and "format" in file_info:
                    duration = float(file_info["format"].get("duration", 0))
                    if duration > 0:
                        mins = int(duration // 60)
                        secs = int(duration % 60)
                        info_text = f"{info_text} | {mins}:{secs:02d}"

                self.file_info_label.configure(text=info_text)
            except:
                self.file_info_label.configure(text="")
        else:
            self.file_name_label.configure(text="No file selected")
            self.file_info_label.configure(text="")

    def _browse_output_dir(self):
        """Browse for output directory"""
        directory = filedialog.askdirectory(
            title="Select Output Directory",
            initialdir=self.output_dir_var.get(),
        )

        if directory:
            self.output_dir_var.set(directory)
            self.config.set("last_output_dir", directory)

    def _start_conversion(self):
        """Start conversion process"""
        if self.is_converting:
            return

        if not self.input_file:
            messagebox.showwarning("No File", "Please select a video file to convert")
            return

        if not self.output_dir_var.get():
            messagebox.showwarning("No Output Directory", "Please select an output directory")
            return

        self.is_converting = True
        self.convert_button.pack_forget()
        self.cancel_button.pack(fill="x")

        thread = threading.Thread(target=self._convert_file, daemon=True)
        thread.start()

    def _cancel_conversion(self):
        """Cancel ongoing conversion"""
        if self.is_converting:
            response = messagebox.askyesno(
                "Cancel Conversion",
                "Are you sure you want to cancel the conversion?",
            )
            if response:
                # Signal cancellation
                self.converter.ffmpeg.cancel()
                self._update_status(0, "⏳ Cancelling...")

    def _convert_file(self):
        """Convert video file with speed profile support"""
        try:
            mode = self.mode_var.get()

            # Get codec settings
            video_codec_str = self.video_codec_var.get()

            # Parse codec (remove labels)
            if "copy" in video_codec_str.lower():
                video_codec = "copy"
            elif "auto" in video_codec_str.lower():
                video_codec = "auto"
            elif "GPU" in video_codec_str:
                # Extract actual codec name
                video_codec = video_codec_str.split()[0]
            elif "CPU" in video_codec_str:
                video_codec = video_codec_str.split()[0]
            else:
                video_codec = video_codec_str

            audio_codec_str = self.audio_codec_var.get()
            audio_codec = "copy" if "copy" in audio_codec_str.lower() else audio_codec_str

            # Get bitrate
            audio_bitrate_str = self.audio_bitrate_var.get()
            audio_bitrate = None if audio_bitrate_str == "Original" or audio_codec == "copy" else audio_bitrate_str

            # Apply speed profile
            profile = self.profile_var.get()
            preset = "medium"
            crf = 23
            tune = None

            if "Ultra Fast" in profile:
                preset = "ultrafast"
                crf = 28
                tune = "fastdecode"
            elif "Fast" in profile:
                preset = "veryfast"
                crf = 26
            elif "High Quality" in profile:
                preset = "slow"
                crf = 18
            # Balanced - keep defaults

            # Get advanced settings if available
            resolution = None
            fps = None
            video_bitrate = "auto"

            if self.show_advanced:
                resolution_str = self.resolution_var.get()
                if "Original" not in resolution_str:
                    resolution = resolution_str.split()[0]

                fps_str = self.fps_var.get()
                if "Original" not in fps_str:
                    fps = int(fps_str)

                video_bitrate = self.video_bitrate_var.get()

            # Get hwaccel value
            hwaccel = self.hwaccel_var.get()

            # Don't use CRF/preset when copying
            if video_codec == "copy":
                crf = None
                preset = None
                tune = None

            if mode == "video_to_video":
                result = self.converter.convert(
                    input_file=self.input_file,
                    output_dir=self.output_dir_var.get(),
                    output_format=self.format_var.get(),
                    video_codec=video_codec,
                    audio_codec=audio_codec,
                    video_bitrate=video_bitrate,
                    audio_bitrate=audio_bitrate,
                    crf=crf,
                    preset=preset,
                    tune=tune,
                    resolution=resolution,
                    fps=fps,
                    hwaccel=hwaccel,
                    preserve_metadata=True,
                    progress_callback=self._update_status,
                )
            else:  # video_to_audio
                result = self.converter.extract_audio(
                    input_file=self.input_file,
                    output_dir=self.output_dir_var.get(),
                    output_format=self.format_var.get(),
                    audio_codec=audio_codec,
                    audio_bitrate=audio_bitrate,
                    progress_callback=self._update_status,
                )

            if result and self.is_converting:
                self._update_status(1.0, "✅ Conversion completed successfully!")
                messagebox.showinfo(
                    "Success",
                    f"File converted successfully!\n\nOutput: {result}",
                )
            elif not self.is_converting:
                self._update_status(0, "❌ Conversion cancelled")
            else:
                self._update_status(0, "❌ Conversion failed")
                messagebox.showerror("Error", "Conversion failed. Please check the log for details.")

        except Exception as e:
            if self.is_converting:
                logger.error(f"Conversion error: {e}", exc_info=True)
                self._update_status(0, f"❌ Error: {e!s}")
                messagebox.showerror("Error", f"Conversion failed:\n{e!s}")

        finally:
            self.is_converting = False
            self.cancel_button.pack_forget()
            self.convert_button.pack(fill="x")

    def _update_status(self, progress, message):
        """Update progress bar and status"""
        self.progress_bar.set(progress)
        self.status_label.configure(text=message)
