"""Audio conversion module for MuXolotl"""

import os
from collections.abc import Callable
from pathlib import Path

from utils.logger import get_logger

from .ffmpeg_wrapper import FFmpegWrapper
from .format_detector import FormatDetector

logger = get_logger()


class AudioConverter:
    """Handle audio file conversions"""

    # Format to FFmpeg format mapping
    FORMAT_MAPPING = {
        "mp3": "mp3",
        "wav": "wav",
        "flac": "flac",
        "ogg": "ogg",
        "oga": "ogg",
        "opus": "ogg",
        "spx": "ogg",
        "aac": "adts",
        "m4a": "mp4",
        "m4b": "mp4",
        "m4r": "mp4",
        "ac3": "ac3",
        "aiff": "aiff",
        "aif": "aiff",
        "aifc": "aiff",
        "caf": "caf",
        "au": "au",
        "amr": "amr",
        "dts": "dts",
        "mp2": "mp2",
        "wma": "asf",
        "wv": "wv",
        "mka": "matroska",
        "ape": "ape",
        "tta": "tta",
        "w64": "w64",
    }

    # Recommended codecs for formats
    CODEC_MAPPING = {
        "mp3": "libmp3lame",
        "wav": "pcm_s16le",
        "flac": "flac",
        "ogg": "libvorbis",
        "opus": "libopus",
        "spx": "libspeex",
        "aac": "aac",
        "m4a": "aac",
        "ac3": "ac3",
        "aiff": "pcm_s16be",
        "wma": "wmav2",
        "amr": "libopencore_amrnb",
        "dts": "dca",
        "mp2": "mp2",
        "wv": "wavpack",
        "ape": "ape",
        "tta": "tta",
    }

    def __init__(self):
        """Initialize audio converter"""
        self.ffmpeg = FFmpegWrapper()
        self.detector = FormatDetector()
        self.available_codecs = self.detector.get_audio_codecs()

    def convert(
        self,
        input_file: str,
        output_dir: str,
        output_format: str,
        codec: str = "auto",
        bitrate: str = "192k",
        sample_rate: int | None = None,
        channels: int | None = None,
        quality: str | None = None,
        preserve_metadata: bool = True,
        progress_callback: Callable[[float, str], None] | None = None,
    ) -> str | None:
        """Convert audio file

        Args:
            input_file: Path to input file
            output_dir: Directory for output file
            output_format: Output format extension
            codec: Audio codec ('auto' for automatic selection)
            bitrate: Audio bitrate (e.g., '192k', '320k')
            sample_rate: Sample rate in Hz (e.g., 44100, 48000)
            channels: Number of channels (1=mono, 2=stereo)
            quality: Quality setting (format-specific)
            preserve_metadata: Whether to preserve metadata
            progress_callback: Optional callback for progress updates

        Returns:
            Path to output file or None if failed

        """
        try:
            # Validate input
            if not os.path.exists(input_file):
                logger.error(f"Input file not found: {input_file}")
                return None

            # Create output directory
            os.makedirs(output_dir, exist_ok=True)

            # Generate output filename
            input_path = Path(input_file)
            output_filename = f"{input_path.stem}.{output_format}"
            output_file = os.path.join(output_dir, output_filename)

            # Determine codec
            if codec == "auto":
                codec = self._get_best_codec(output_format)

            # Validate codec
            if codec and codec not in self.available_codecs and codec != "copy":
                logger.warning(f"Codec {codec} not available, using auto-selection")
                codec = self._get_best_codec(output_format)

            # Build parameters
            params = {
                "audio_codec": codec,
                "audio_bitrate": bitrate if bitrate != "auto" else None,
                "sample_rate": sample_rate,
                "channels": channels,
                "no_video": True,  # Remove video streams
                "preserve_metadata": preserve_metadata,
                "format": self.FORMAT_MAPPING.get(output_format, output_format),
            }

            # Add quality settings
            if quality:
                params["custom_params"] = self._get_quality_params(output_format, quality)

            # Build and execute command
            command = self.ffmpeg.build_command(input_file, output_file, params)

            if progress_callback:
                progress_callback(0.1, "Starting conversion...")

            success = self.ffmpeg.execute(command, progress_callback)

            if success and os.path.exists(output_file):
                logger.info(f"Successfully converted: {output_file}")
                if progress_callback:
                    progress_callback(1.0, "Completed!")
                return output_file
            logger.error(f"Conversion failed for: {input_file}")
            return None

        except (OSError, IOError, ValueError) as e:
            logger.error(f"Audio conversion error: {e}", exc_info=True)
            return None

    def _get_best_codec(self, fmt: str) -> str:
        """Get best available codec for format"""
        # Try recommended codec
        recommended = self.CODEC_MAPPING.get(fmt)
        if recommended and recommended in self.available_codecs:
            return recommended

        # Fallback codecs
        fallback_map = {
            "mp3": ["libmp3lame", "mp3"],
            "ogg": ["libvorbis", "vorbis"],
            "opus": ["libopus", "opus"],
            "aac": ["aac", "libfdk_aac"],
            "m4a": ["aac", "libfdk_aac"],
            "flac": ["flac"],
            "wav": ["pcm_s16le", "pcm_s24le", "pcm_s32le"],
            "wma": ["wmav2", "wmav1"],
        }

        for codec in fallback_map.get(fmt, []):
            if codec in self.available_codecs:
                return codec

        # Last resort
        return "copy"

    def _get_quality_params(self, fmt: str, quality: str) -> list:
        """Get quality-specific parameters"""
        params = []

        if fmt == "mp3":
            # MP3 VBR quality (0-9, lower is better)
            quality_map = {"highest": "0", "high": "2", "medium": "4", "low": "6"}
            q = quality_map.get(quality, "2")
            params.extend(["-q:a", q])

        elif fmt in ("ogg", "opus"):
            # Vorbis/Opus quality
            quality_map = {"highest": "10", "high": "8", "medium": "6", "low": "4"}
            q = quality_map.get(quality, "8")
            params.extend(["-q:a", q])

        elif fmt == "flac":
            # FLAC compression level (0-12)
            quality_map = {"highest": "12", "high": "8", "medium": "5", "low": "0"}
            q = quality_map.get(quality, "5")
            params.extend(["-compression_level", q])

        return params

    def get_supported_formats(self) -> list:
        """Get list of supported audio formats"""
        available = self.detector.get_audio_formats()
        return sorted([
            fmt for fmt in self.FORMAT_MAPPING
            if self.FORMAT_MAPPING[fmt] in available or fmt in available
        ])

    def get_file_info(self, file_path: str) -> dict[str, any]:
        """Get audio file information"""
        return self.ffmpeg.get_file_info(file_path)
