"""Settings window for MuXolotl"""

from tkinter import messagebox

import customtkinter as ctk

COLORS = {
    "primary": "#6366f1",
    "primary_hover": "#4f46e5",
    "success": "#10b981",
    "bg_dark": "#0f172a",
    "bg_medium": "#1e293b",
    "bg_light": "#334155",
    "text_primary": "#f1f5f9",
    "text_secondary": "#94a3b8",
    "border": "#475569",
}


class SettingsWindow(ctk.CTkToplevel):
    """Modern settings window"""

    def __init__(self, parent, config):
        """Initialize settings window"""
        super().__init__(parent)

        self.config = config
        self.title("Settings - MuXolotl")
        self.geometry("600x500")
        self.resizable(False, False)

        # Initialize all settings variables
        self.output_dir_var = ctk.StringVar(value=self.config.get("last_output_dir"))
        self.thread_var = ctk.StringVar(value=str(self.config.get("advanced.thread_count", "auto")))
        self.overwrite_var = ctk.BooleanVar(value=self.config.get("advanced.overwrite_files", True))
        self.metadata_var = ctk.BooleanVar(value=self.config.get("advanced.preserve_metadata", True))
        
        # Audio settings
        self.audio_format_var = ctk.StringVar(value=self.config.get("audio.default_format", "mp3"))
        self.audio_codec_var = ctk.StringVar(value=self.config.get("audio.default_codec", "auto"))
        self.audio_bitrate_var = ctk.StringVar(value=self.config.get("audio.default_bitrate", "192k"))
        
        # Video settings
        self.video_format_var = ctk.StringVar(value=self.config.get("video.default_format", "mp4"))
        self.video_codec_var = ctk.StringVar(value=self.config.get("video.default_video_codec", "libx264"))
        self.video_preset_var = ctk.StringVar(value=self.config.get("video.default_preset", "medium"))
        self.video_crf_var = ctk.StringVar(value=self.config.get("video.default_crf", "23"))
        
        # Advanced settings
        self.hwaccel_var = ctk.StringVar(value=self.config.get("advanced.hardware_acceleration", "auto"))

        # Center window
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 600) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 500) // 2
        self.geometry(f"+{x}+{y}")

        # Make modal
        self.transient(parent)
        self.grab_set()

        self._setup_ui()

    def _setup_ui(self):
        """Setup UI"""
        # Main container
        main_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_dark"])
        main_frame.pack(fill="both", expand=True)

        # Header
        header_frame = ctk.CTkFrame(main_frame, fg_color=COLORS["bg_medium"], height=70, corner_radius=0)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        ctk.CTkLabel(
            header_frame,
            text="⚙️ Settings",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS["text_primary"],
        ).pack(pady=20)

        # Content with tabs
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Tab view
        tabview = ctk.CTkTabview(
            content_frame,
            corner_radius=10,
            fg_color=COLORS["bg_medium"],
            segmented_button_fg_color=COLORS["bg_light"],
            segmented_button_selected_color=COLORS["primary"],
            segmented_button_selected_hover_color=COLORS["primary_hover"],
        )
        tabview.pack(fill="both", expand=True)

        # Tabs
        general_tab = tabview.add("General")
        audio_tab = tabview.add("Audio")
        video_tab = tabview.add("Video")
        advanced_tab = tabview.add("Advanced")

        # Setup tabs
        self._setup_general_tab(general_tab)
        self._setup_audio_tab(audio_tab)
        self._setup_video_tab(video_tab)
        self._setup_advanced_tab(advanced_tab)

        # Bottom buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkButton(
            button_frame,
            text="💾 Save Settings",
            command=self._save_settings,
            height=40,
            corner_radius=8,
            fg_color=COLORS["success"],
            hover_color="#059669",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left", fill="x", expand=True, padx=(0, 5))

        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.destroy,
            height=40,
            corner_radius=8,
            fg_color=COLORS["bg_light"],
            hover_color=COLORS["border"],
            font=ctk.CTkFont(size=13),
        ).pack(side="left", fill="x", expand=True, padx=(5, 0))

    def _setup_general_tab(self, parent):
        """Setup general settings tab"""
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # Default output directory
        self._create_section_header(scroll, "📂 Default Output Directory")

        dir_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_light"], corner_radius=8)
        dir_frame.pack(fill="x", pady=10)

        ctk.CTkEntry(
            dir_frame,
            textvariable=self.output_dir_var,
            font=ctk.CTkFont(size=11),
            height=35,
        ).pack(side="left", fill="x", expand=True, padx=10, pady=10)

        # Thread count
        self._create_section_header(scroll, "⚡ Performance")

        thread_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_light"], corner_radius=8)
        thread_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(
            thread_frame,
            text="Thread Count:",
            font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=15, pady=15)

        ctk.CTkOptionMenu(
            thread_frame,
            variable=self.thread_var,
            values=["auto", "1", "2", "4", "6", "8", "12", "16"],
            width=120,
            fg_color=COLORS["bg_dark"],
            button_color=COLORS["primary"],
        ).pack(side="right", padx=15, pady=15)

        # Overwrite files
        self._create_section_header(scroll, "🔧 File Handling")

        options_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_light"], corner_radius=8)
        options_frame.pack(fill="x", pady=10)

        ctk.CTkCheckBox(
            options_frame,
            text="Overwrite existing files",
            variable=self.overwrite_var,
            font=ctk.CTkFont(size=12),
            checkbox_width=22,
            checkbox_height=22,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
        ).pack(anchor="w", padx=15, pady=10)

        ctk.CTkCheckBox(
            options_frame,
            text="Preserve metadata (recommended)",
            variable=self.metadata_var,
            font=ctk.CTkFont(size=12),
            checkbox_width=22,
            checkbox_height=22,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
        ).pack(anchor="w", padx=15, pady=10)

    def _setup_audio_tab(self, parent):
        """Setup audio settings tab"""
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        self._create_section_header(scroll, "🎵 Default Audio Settings")

        settings_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_light"], corner_radius=8)
        settings_frame.pack(fill="x", pady=10)

        # Default format
        self._create_option_row(
            settings_frame,
            "Default Format:",
            "audio_format",
            ["mp3", "wav", "flac", "ogg", "aac", "m4a"],
            self.audio_format_var,
        )

        # Default codec
        self._create_option_row(
            settings_frame,
            "Default Codec:",
            "audio_codec",
            ["auto", "libmp3lame", "aac", "flac", "libvorbis"],
            self.audio_codec_var,
        )

        # Default bitrate
        self._create_option_row(
            settings_frame,
            "Default Bitrate:",
            "audio_bitrate",
            ["128k", "160k", "192k", "256k", "320k"],
            self.audio_bitrate_var,
        )

    def _setup_video_tab(self, parent):
        """Setup video settings tab"""
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        self._create_section_header(scroll, "🎬 Default Video Settings")

        settings_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_light"], corner_radius=8)
        settings_frame.pack(fill="x", pady=10)

        # Default format
        self._create_option_row(
            settings_frame,
            "Default Format:",
            "video_format",
            ["mp4", "mkv", "avi", "mov", "webm"],
            self.video_format_var,
        )

        # Default video codec
        self._create_option_row(
            settings_frame,
            "Video Codec:",
            "video_codec",
            ["libx264", "libx265", "libvpx-vp9", "mpeg4"],
            self.video_codec_var,
        )

        # Default preset
        self._create_option_row(
            settings_frame,
            "Encoding Preset:",
            "video_preset",
            ["veryfast", "fast", "medium", "slow", "slower"],
            self.video_preset_var,
        )

        # Default CRF
        self._create_option_row(
            settings_frame,
            "Default CRF:",
            "video_crf",
            ["18", "20", "23", "26", "28"],
            self.video_crf_var,
        )

    def _setup_advanced_tab(self, parent):
        """Setup advanced settings tab"""
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        self._create_section_header(scroll, "🚀 Advanced Settings")

        settings_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_light"], corner_radius=8)
        settings_frame.pack(fill="x", pady=10)

        # Hardware acceleration
        self._create_option_row(
            settings_frame,
            "Hardware Accel:",
            "hwaccel",
            ["auto", "none", "cuda", "qsv", "dxva2"],
            self.hwaccel_var,
        )

        # Warning
        warning_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_medium"], corner_radius=8)
        warning_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(
            warning_frame,
            text="⚠️ Advanced settings may affect performance and compatibility.\nOnly change if you know what you're doing.",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"],
            justify="center",
        ).pack(pady=15)

    def _create_section_header(self, parent, text):
        """Create section header"""
        ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_primary"],
        ).pack(anchor="w", pady=(10, 5))

    def _create_option_row(self, parent, label_text, var_name, values, variable):
        """Create option row"""
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", padx=15, pady=8)

        ctk.CTkLabel(
            row_frame,
            text=label_text,
            font=ctk.CTkFont(size=12),
            width=150,
            anchor="w",
        ).pack(side="left", padx=(0, 10))

        ctk.CTkOptionMenu(
            row_frame,
            variable=variable,
            values=values,
            width=200,
            fg_color=COLORS["bg_dark"],
            button_color=COLORS["primary"],
            button_hover_color=COLORS["primary_hover"],
        ).pack(side="right")

    def _save_settings(self):
        """Save all settings"""
        try:
            # General
            self.config.set("last_output_dir", self.output_dir_var.get())
            self.config.set("advanced.thread_count", self.thread_var.get())
            self.config.set("advanced.overwrite_files", self.overwrite_var.get())
            self.config.set("advanced.preserve_metadata", self.metadata_var.get())

            # Audio
            self.config.set("audio.default_format", self.audio_format_var.get())
            self.config.set("audio.default_codec", self.audio_codec_var.get())
            self.config.set("audio.default_bitrate", self.audio_bitrate_var.get())

            # Video
            self.config.set("video.default_format", self.video_format_var.get())
            self.config.set("video.default_video_codec", self.video_codec_var.get())
            self.config.set("video.default_preset", self.video_preset_var.get())
            self.config.set("video.default_crf", self.video_crf_var.get())

            # Advanced
            self.config.set("advanced.hardware_acceleration", self.hwaccel_var.get())

            self.config.save()

            messagebox.showinfo("Success", "Settings saved successfully!")
            self.destroy()

        except (AttributeError, KeyError, ValueError) as e:
            messagebox.showerror("Error", f"Failed to save settings:\n{e!s}")
