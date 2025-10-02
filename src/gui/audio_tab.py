"""
Modern Audio conversion tab for MuXolotl
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import threading
from pathlib import Path

from core.audio_converter import AudioConverter
from core.format_detector import FormatDetector
from .tooltip import TOOLTIPS, create_tooltip
from utils.logger import get_logger

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
    "border": "#475569"
}

class AudioTab:
    """Modern Audio conversion tab"""
    
    def __init__(self, parent, config):
        """Initialize audio tab"""
        self.parent = parent
        self.config = config
        self.converter = AudioConverter()
        self.detector = FormatDetector()
        self.input_files = []
        self.is_converting = False
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup modern UI - compact and beautiful"""
        # Configure grid
        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_columnconfigure(1, weight=2)
        
        # === LEFT PANEL - File Management ===
        left_panel = ctk.CTkFrame(self.parent, fg_color=COLORS["bg_light"], corner_radius=10)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        
        # Header
        header = ctk.CTkLabel(
            left_panel,
            text="📁 Input Files",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        header.pack(pady=(15, 10), padx=15)
        
        # File list with custom styling
        file_frame = ctk.CTkFrame(left_panel, fg_color=COLORS["bg_medium"], corner_radius=8)
        file_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        
        self.file_listbox = ctk.CTkTextbox(
            file_frame,
            font=ctk.CTkFont(size=11),
            fg_color=COLORS["bg_medium"],
            text_color=COLORS["text_secondary"],
            wrap="word"
        )
        self.file_listbox.pack(fill="both", expand=True, padx=2, pady=2)
        self.file_listbox.insert("1.0", "Click 'Add Files' to select audio files")
        self.file_listbox.configure(state="disabled")
        
        # Setup drag and drop
        self._setup_drag_drop()
        
        # Buttons
        btn_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        add_btn = ctk.CTkButton(
            btn_frame,
            text="➕ Add Files",
            command=self._add_files,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            height=35,
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        add_btn.pack(fill="x", pady=2)
        
        clear_btn = ctk.CTkButton(
            btn_frame,
            text="🗑️ Clear All",
            command=self._clear_files,
            fg_color=COLORS["bg_dark"],
            hover_color=COLORS["border"],
            height=35,
            corner_radius=8,
            font=ctk.CTkFont(size=12)
        )
        clear_btn.pack(fill="x", pady=2)
        
        # === RIGHT PANEL - Settings & Conversion ===
        right_panel = ctk.CTkFrame(self.parent, fg_color=COLORS["bg_light"], corner_radius=10)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        
        # Create scrollable frame for settings
        scroll_frame = ctk.CTkScrollableFrame(
            right_panel,
            fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["primary"]
        )
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Settings header
        settings_header = ctk.CTkLabel(
            scroll_frame,
            text="⚙️ Conversion Settings",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        settings_header.pack(pady=(5, 15), anchor="w")
        
        # Settings in a grid layout
        settings_container = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        settings_container.pack(fill="x", pady=5)
        
        # Format
        self._create_setting_row(
            settings_container,
            "Output Format",
            "format",
            self.converter.get_supported_formats(),
            self.config.get("audio.default_format", "mp3"),
            row=0,
            tooltip=TOOLTIPS["audio_format"]
        )
        
        # Codec
        codecs = ["copy (fast)", "auto"] + sorted(list(self.detector.get_audio_codecs()))[:10]
        self._create_setting_row(
            settings_container,
            "Codec",
            "codec",
            codecs,
            "copy (fast)",
            row=1,
            tooltip=TOOLTIPS["audio_codec"]
        )
        
        # Bitrate
        self._create_setting_row(
            settings_container,
            "Bitrate",
            "bitrate",
            ["Original", "64k", "96k", "128k", "160k", "192k", "256k", "320k"],
            "Original",
            row=2,
            tooltip=TOOLTIPS["audio_bitrate"]
        )
        
        # Sample Rate
        self._create_setting_row(
            settings_container,
            "Sample Rate",
            "sample_rate",
            ["Original", "44100 Hz", "48000 Hz", "96000 Hz"],
            "Original",
            row=3,
            tooltip=TOOLTIPS["audio_sample_rate"]
        )
        
        # Channels
        self._create_setting_row(
            settings_container,
            "Channels",
            "channels",
            ["Original", "Mono", "Stereo"],
            "Original",
            row=4,
            tooltip=TOOLTIPS["audio_channels"]
        )
        
        # Separator
        separator = ctk.CTkFrame(scroll_frame, height=2, fg_color=COLORS["border"])
        separator.pack(fill="x", pady=15)
        
        # Output directory
        output_label = ctk.CTkLabel(
            scroll_frame,
            text="💾 Output Directory",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_primary"]
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
            height=35
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
            font=ctk.CTkFont(size=16)
        )
        browse_btn.pack(side="right", padx=5, pady=5)
        
        # Progress section
        progress_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        progress_frame.pack(fill="x", pady=15)
        
        self.status_label = ctk.CTkLabel(
            progress_frame,
            text="Ready to convert",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        )
        self.status_label.pack(pady=(0, 8))
        
        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            height=8,
            corner_radius=4,
            fg_color=COLORS["bg_medium"],
            progress_color=COLORS["primary"]
        )
        self.progress_bar.pack(fill="x", pady=5)
        self.progress_bar.set(0)
        
        # Convert buttons frame
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
            font=ctk.CTkFont(size=15, weight="bold")
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
            font=ctk.CTkFont(size=14, weight="bold")
        )
    
    def _create_setting_row(self, parent, label_text, var_name, values, default, row, tooltip=None):
        """Create a compact setting row with tooltip"""
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.grid(row=row, column=0, sticky="ew", pady=5)
        parent.grid_columnconfigure(0, weight=1)
        
        label = ctk.CTkLabel(
            row_frame,
            text=label_text + ":",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
            width=100,
            anchor="w"
        )
        label.pack(side="left", padx=(0, 10))
        
        # Add tooltip to label
        if tooltip:
            create_tooltip(label, tooltip)
        
        var = ctk.StringVar(value=default if default in values else values[0])
        setattr(self, f"{var_name}_var", var)
        
        menu = ctk.CTkOptionMenu(
            row_frame,
            variable=var,
            values=values,
            fg_color=COLORS["bg_medium"],
            button_color=COLORS["primary"],
            button_hover_color=COLORS["primary_hover"],
            dropdown_fg_color=COLORS["bg_dark"],
            font=ctk.CTkFont(size=11),
            dropdown_font=ctk.CTkFont(size=11),
            height=32,
            corner_radius=6
        )
        menu.pack(side="left", fill="x", expand=True)
        
        # Add tooltip to menu
        if tooltip:
            create_tooltip(menu, tooltip)
    
    def _setup_drag_drop(self):
        """Setup drag and drop for files - Windows compatible"""
        # Make the textbox accept drops
        widget = self.file_listbox
        
        # Bind mouse events for visual feedback
        widget.bind('<Enter>', lambda e: widget.configure(border_width=2))
        widget.bind('<Leave>', lambda e: widget.configure(border_width=0))
        
        # Try multiple DnD methods
        try:
            # Method 1: tkinterdnd2
            widget.drop_target_register('DND_Files')
            widget.dnd_bind('<<Drop>>', self._on_drop_dnd2)
            logger.debug("Drag & drop enabled (tkinterdnd2)")
            return
        except:
            pass
        
        try:
            # Method 2: Windows specific
            import tkinter as tk
            
            def handle_drop(event):
                files = widget.tk.splitlist(event.data)
                self._process_dropped_files(files)
            
            widget.bind('<Drop>', handle_drop)
            logger.debug("Drag & drop enabled (Windows)")
            return
        except:
            pass
        
        logger.debug("Drag & drop not available")
    
    def _on_drop_dnd2(self, event):
        """Handle drop event from tkinterdnd2"""
        try:
            files = self._parse_drop_data(event.data)
            self._process_dropped_files(files)
        except Exception as e:
            logger.error(f"Drag and drop error: {e}")
    
    def _parse_drop_data(self, data):
        """Parse dropped file data (handles various formats)"""
        files = []
        
        # Remove outer braces and split
        data = data.strip()
        
        # Method 1: Parse Windows style {path1} {path2}
        if '{' in data:
            import re
            matches = re.findall(r'\{([^}]+)\}', data)
            files.extend(matches)
        
        # Method 2: Space separated paths
        if not files:
            parts = data.split()
            for part in parts:
                part = part.strip('{}')
                if part:
                    files.append(part)
        
        # Method 3: Single file
        if not files and data:
            files.append(data.strip('{}'))
        
        return files
    
    def _process_dropped_files(self, files):
        """Process dropped files"""
        audio_extensions = {'.mp3', '.wav', '.flac', '.ogg', '.aac', '.m4a', 
                          '.wma', '.opus', '.ape', '.tta', '.wv', '.ac3', 
                          '.dts', '.mp2', '.au', '.amr'}
        
        added = 0
        for file_path in files:
            file_path = file_path.strip()
            if os.path.isfile(file_path):
                ext = os.path.splitext(file_path)[1].lower()
                if ext in audio_extensions:
                    if file_path not in self.input_files:
                        self.input_files.append(file_path)
                        added += 1
        
        if added > 0:
            self._update_file_list()
            logger.debug(f"Added {added} files via drag & drop")
    
    def _add_files(self):
        """Add files to conversion list"""
        files = filedialog.askopenfilenames(
            title="Select Audio Files",
            filetypes=[
                ("Audio Files", "*.mp3 *.wav *.flac *.ogg *.aac *.m4a *.wma *.opus *.ape *.tta"),
                ("All Files", "*.*")
            ]
        )
        
        if files:
            for file in files:
                if file not in self.input_files:
                    self.input_files.append(file)
            self._update_file_list()
    
    def _clear_files(self):
        """Clear file list"""
        self.input_files = []
        self._update_file_list()
    
    def _update_file_list(self):
        """Update file listbox"""
        self.file_listbox.configure(state="normal")
        self.file_listbox.delete("1.0", "end")
        
        if self.input_files:
            for idx, file in enumerate(self.input_files, 1):
                filename = Path(file).name
                try:
                    size = os.path.getsize(file) / (1024 * 1024)
                    self.file_listbox.insert("end", f"{idx}. {filename}\n")
                    self.file_listbox.insert("end", f"   Size: {size:.1f} MB\n\n")
                except:
                    self.file_listbox.insert("end", f"{idx}. {filename}\n\n")
        else:
            self.file_listbox.insert("end", "Click 'Add Files' to select audio files")
        
        self.file_listbox.configure(state="disabled")
    
    def _browse_output_dir(self):
        """Browse for output directory"""
        directory = filedialog.askdirectory(
            title="Select Output Directory",
            initialdir=self.output_dir_var.get()
        )
        
        if directory:
            self.output_dir_var.set(directory)
            self.config.set("last_output_dir", directory)
    
    def _start_conversion(self):
        """Start conversion process"""
        if self.is_converting:
            return
        
        if not self.input_files:
            messagebox.showwarning("No Files", "Please add audio files to convert")
            return
        
        if not self.output_dir_var.get():
            messagebox.showwarning("No Output Directory", "Please select an output directory")
            return
        
        self.is_converting = True
        self.convert_button.pack_forget()
        self.cancel_button.pack(fill="x")
        
        thread = threading.Thread(target=self._convert_files, daemon=True)
        thread.start()
    
    def _cancel_conversion(self):
        """Cancel ongoing conversion"""
        if self.is_converting:
            response = messagebox.askyesno(
                "Cancel Conversion",
                "Are you sure you want to cancel the conversion?"
            )
            if response:
                # Signal cancellation
                self.converter.ffmpeg.cancel()
                self._update_status(0, "⏳ Cancelling...")
    
    def _convert_files(self):
        """Convert all files"""
        total = len(self.input_files)
        successful = 0
        
        for idx, input_file in enumerate(self.input_files, 1):
            # Check if cancelled
            if not self.is_converting:
                break
            
            try:
                self._update_status(
                    (idx - 1) / total,
                    f"Converting {idx}/{total}: {Path(input_file).name}"
                )
                
                # Get codec
                codec_str = self.codec_var.get()
                if "copy" in codec_str.lower():
                    codec = "copy"
                elif codec_str == "auto":
                    codec = "auto"
                else:
                    codec = codec_str
                
                # Get bitrate
                bitrate_str = self.bitrate_var.get()
                if bitrate_str == "Original" or codec == "copy":
                    bitrate = None
                else:
                    bitrate = bitrate_str
                
                # Get sample rate
                sample_rate_str = self.sample_rate_var.get()
                if "Original" in sample_rate_str or codec == "copy":
                    sample_rate = None
                else:
                    sample_rate = int(sample_rate_str.split()[0])
                
                # Get channels
                channels_str = self.channels_var.get()
                if "Original" in channels_str or codec == "copy":
                    channels = None
                elif "Mono" in channels_str:
                    channels = 1
                elif "Stereo" in channels_str:
                    channels = 2
                else:
                    channels = None
                
                result = self.converter.convert(
                    input_file=input_file,
                    output_dir=self.output_dir_var.get(),
                    output_format=self.format_var.get(),
                    codec=codec,
                    bitrate=bitrate,
                    sample_rate=sample_rate,
                    channels=channels,
                    preserve_metadata=True,
                    progress_callback=lambda p, s: self._update_status((idx - 1 + p) / total, s)
                )
                
                if result:
                    successful += 1
                
            except Exception as e:
                logger.error(f"Conversion failed for {input_file}: {e}")
        
        # Final status
        if self.is_converting:
            self._update_status(1.0, f"✅ Completed! {successful}/{total} files converted")
            
            if successful > 0:
                messagebox.showinfo(
                    "Success",
                    f"Successfully converted {successful} out of {total} files!\n\nOutput: {self.output_dir_var.get()}"
                )
            else:
                messagebox.showerror("Error", "No files were converted successfully")
        else:
            self._update_status(0, "❌ Conversion cancelled")
        
        # Reset UI
        self.is_converting = False
        self.cancel_button.pack_forget()
        self.convert_button.pack(fill="x")
    
    def _update_status(self, progress, message):
        """Update progress bar and status"""
        self.progress_bar.set(progress)
        self.status_label.configure(text=message)