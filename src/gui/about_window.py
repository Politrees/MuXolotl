"""About window for MuXolotl"""

import os
import sys
import webbrowser

import customtkinter as ctk
from PIL import Image

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


class AboutWindow(ctk.CTkToplevel):
    """About/Info window"""

    def __init__(self, parent):
        """Initialize about window"""
        super().__init__(parent)

        self.title("About MuXolotl")
        self.geometry("600x700")
        self.resizable(False, False)

        # Set window icon
        self.iconbitmap(self._get_resource_path("assets/icon.ico"))

        # Center window
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 600) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 700) // 2
        self.geometry(f"+{x}+{y}")

        # Make modal
        self.transient(parent)
        self.grab_set()

        self._setup_ui()

    def _get_resource_path(self, relative_path):
        """Get absolute path to resource"""
        try:
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def _setup_ui(self):
        """Setup UI"""
        # Main container
        main_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_dark"])
        main_frame.pack(fill="both", expand=True)

        # Scrollable content
        scroll_frame = ctk.CTkScrollableFrame(
            main_frame,
            fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
        )
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # === HEADER WITH ICON ===
        header_frame = ctk.CTkFrame(scroll_frame, fg_color=COLORS["bg_medium"], corner_radius=12)
        header_frame.pack(fill="x", pady=(0, 20))

        # load icon
        icon_image = Image.open(self._get_resource_path("assets/icon.ico"))
        icon_image = icon_image.resize((80, 80), Image.Resampling.LANCZOS)
        icon_photo = ctk.CTkImage(light_image=icon_image, dark_image=icon_image, size=(80, 80))

        icon_label = ctk.CTkLabel(header_frame, image=icon_photo, text="")
        icon_label.pack(pady=(20, 10))

        # App name
        app_name = ctk.CTkLabel(
            header_frame,
            text="MuXolotl",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=COLORS["text_primary"],
        )
        app_name.pack(pady=(0, 5))

        # Tagline
        tagline = ctk.CTkLabel(
            header_frame,
            text="Universal Media Converter",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_secondary"],
        )
        tagline.pack(pady=(0, 10))

        # Version
        version = ctk.CTkLabel(
            header_frame,
            text="Version 0.0.1",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["primary"],
        )
        version.pack(pady=(0, 20))

        # === DESCRIPTION ===
        desc_frame = ctk.CTkFrame(scroll_frame, fg_color=COLORS["bg_medium"], corner_radius=10)
        desc_frame.pack(fill="x", pady=(0, 15))

        desc_text = ctk.CTkLabel(
            desc_frame,
            text="A powerful, flexible, and lightning-fast media converter\n"
            "supporting hundreds of audio and video formats.\n\n"
            "Features hardware acceleration, batch processing,\n"
            "and advanced customization options.",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
            justify="center",
        )
        desc_text.pack(pady=20, padx=20)

        # === KEY FEATURES ===
        features_frame = ctk.CTkFrame(scroll_frame, fg_color=COLORS["bg_medium"], corner_radius=10)
        features_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            features_frame,
            text="✨ Key Features",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_primary"],
        ).pack(pady=(15, 10), anchor="w", padx=20)

        features = [
            "🎵 30+ Audio Formats Supported",
            "🎬 25+ Video Formats Supported",
            "🚀 Hardware GPU Acceleration (NVIDIA, AMD, Intel)",
            "⚙️ Advanced Manual Configuration",
            "📦 Batch Processing",
            "💾 Preserves Original Quality",
            "🔧 Customizable Bitrate, Codec, Sample Rate",
            "⚡ Speed Profiles (Ultra Fast to High Quality)",
            "🎯 Smart Auto-Detection",
        ]

        for feature in features:
            ctk.CTkLabel(
                features_frame,
                text=feature,
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_secondary"],
                anchor="w",
            ).pack(anchor="w", padx=30, pady=2)

        ctk.CTkLabel(features_frame, text="").pack(pady=5)  # Spacer

        # === POWERED BY ===
        powered_frame = ctk.CTkFrame(scroll_frame, fg_color=COLORS["bg_medium"], corner_radius=10)
        powered_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            powered_frame,
            text="🔧 Powered By",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_primary"],
        ).pack(pady=(15, 10), anchor="w", padx=20)

        technologies = [
            "• FFmpeg - Universal media framework",
            "• Python 3.8+ - Core language",
            "• CustomTkinter - Modern UI framework",
            "• Pillow - Image processing",
        ]

        for tech in technologies:
            ctk.CTkLabel(
                powered_frame,
                text=tech,
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_secondary"],
                anchor="w",
            ).pack(anchor="w", padx=30, pady=2)

        ctk.CTkLabel(powered_frame, text="").pack(pady=5)

        # === LINKS ===
        links_frame = ctk.CTkFrame(scroll_frame, fg_color=COLORS["bg_medium"], corner_radius=10)
        links_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            links_frame,
            text="🔗 Links & Resources",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_primary"],
        ).pack(pady=(15, 10), anchor="w", padx=20)

        # Links grid
        links_grid = ctk.CTkFrame(links_frame, fg_color="transparent")
        links_grid.pack(fill="x", padx=20, pady=(0, 15))

        links = [
            ("🌐 GitHub Repository", "https://github.com/Politrees/MuXolotl"),
            ("📖 Documentation", "https://github.com/Politrees/MuXolotl/README.md"),
            ("🐛 Report Bug", "https://github.com/Politrees/MuXolotl/issues"),
            ("💡 Feature Request", "https://github.com/Politrees/MuXolotl/issues/new"),
            ("⭐ Star on GitHub", "https://github.com/Politrees/MuXolotl/stargazers"),
        ]

        for text, url in links:
            btn = ctk.CTkButton(
                links_grid,
                text=text,
                command=lambda u=url: webbrowser.open(u),
                fg_color=COLORS["bg_light"],
                hover_color=COLORS["primary"],
                corner_radius=8,
                height=35,
                anchor="w",
                font=ctk.CTkFont(size=11),
            )
            btn.pack(fill="x", pady=3)

        # === LICENSE ===
        license_frame = ctk.CTkFrame(scroll_frame, fg_color=COLORS["bg_medium"], corner_radius=10)
        license_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            license_frame,
            text="📜 License",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_primary"],
        ).pack(pady=(15, 10), anchor="w", padx=20)

        license_text = ctk.CTkLabel(
            license_frame,
            text="MIT License\n\n"
            "Copyright (c) 2024 Politrees\n\n"
            "Permission is hereby granted, free of charge, to any person\n"
            "obtaining a copy of this software to use, modify, and distribute\n"
            "it freely under the terms of the MIT License.",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_secondary"],
            justify="center",
        )
        license_text.pack(pady=(0, 15), padx=20)

        # === CREDITS ===
        credits_frame = ctk.CTkFrame(scroll_frame, fg_color=COLORS["bg_medium"], corner_radius=10)
        credits_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            credits_frame,
            text="👥 Credits",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_primary"],
        ).pack(pady=(15, 10), anchor="w", padx=20)

        credits_text = ctk.CTkLabel(
            credits_frame,
            text="Developed with ❤️ by the Politrees\n\n"
            "Special thanks to:\n"
            "• FFmpeg developers for the incredible framework\n"
            "• CustomTkinter team for the beautiful UI library\n"
            "• All contributors and users",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"],
            justify="center",
        )
        credits_text.pack(pady=(0, 15), padx=20)

        # === CLOSE BUTTON ===
        close_button = ctk.CTkButton(
            scroll_frame,
            text="Close",
            command=self.destroy,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        close_button.pack(fill="x", pady=(5, 10))
