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

    # Format to FFmpeg format mapping (COMPLETE)
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
        "eac3": "eac3",
        "aiff": "aiff",
        "aif": "aiff",
        "aifc": "aiff",
        "caf": "caf",
        "au": "au",
        "amr": "amr",
        "awb": "amr",
        "dts": "dts",
        "mp2": "mp2",
        "mp1": "mp2",
        "wma": "asf",
        "wv": "wv",
        "mka": "matroska",
        "ape": "ape",
        "tta": "tta",
        "w64": "w64",
        "tak": "tak",
        "ofs": "ofs",
        "mpc": "mpc",
        "alac": "mp4",
    }

    # COMPLETE codec compatibility matrix: format -> [preferred_codec, fallback1, fallback2, ...]
    FORMAT_CODEC_COMPATIBILITY = {
        "mp3": ["libmp3lame", "mp3"],
        "wav": ["pcm_s16le", "pcm_s24le", "pcm_s32le", "pcm_f32le", "pcm_f64le"],
        "flac": ["flac"],
        "ogg": ["libvorbis", "vorbis", "libopus", "opus", "flac"],
        "oga": ["libvorbis", "vorbis", "libopus", "opus"],
        "opus": ["libopus", "opus"],
        "spx": ["libspeex"],
        "aac": ["aac", "libfdk_aac"],
        "m4a": ["aac", "libfdk_aac", "alac"],
        "m4b": ["aac", "libfdk_aac"],
        "m4r": ["aac", "libfdk_aac"],
        "alac": ["alac", "aac"],
        "ac3": ["ac3", "eac3"],
        "eac3": ["eac3", "ac3"],
        "aiff": ["pcm_s16be", "pcm_s24be", "pcm_s32be"],
        "aif": ["pcm_s16be", "pcm_s24be"],
        "aifc": ["pcm_s16be", "pcm_s24be"],
        "caf": ["aac", "pcm_s16le", "alac"],
        "au": ["pcm_s16be", "pcm_mulaw", "pcm_alaw"],
        "amr": ["libopencore_amrnb", "amr_nb"],
        "awb": ["libopencore_amrwb", "amr_wb"],
        "dts": ["dca"],
        "mp2": ["mp2", "mp2fixed"],
        "mp1": ["mp2", "mp2fixed"],
        "wma": ["wmav2", "wmav1"],
        "wv": ["wavpack"],
        "mka": ["aac", "libopus", "flac", "libvorbis", "ac3"],  # Matroska supports many
        "ape": ["ape"],  # Usually decode-only
        "tta": ["tta"],  # Usually decode-only
        "w64": ["pcm_s16le", "pcm_s24le"],
        "tak": ["tak"],  # Usually decode-only
        "mpc": ["musepack"],  # Usually decode-only
    }

    # Experimental codecs that need -strict -2
    EXPERIMENTAL_CODECS = {
        "vorbis",  # Native vorbis (not libvorbis)
        "opus",    # Native opus (not libopus)
        "aac",     # Native aac in some builds
    }

    # Read-only formats (can decode but usually can't encode)
    READ_ONLY_FORMATS = {"ape", "tak", "mpc", "ofs"}

    def __init__(self):
        """Initialize audio converter"""
        self.ffmpeg = FFmpegWrapper()
        self.detector = FormatDetector()
        self.available_codecs = self.detector.get_audio_codecs()
        self.available_encoders = self.detector.get_audio_encoders()

        # Combine both for checking
        self.all_available = self.available_codecs | self.available_encoders

        # Debug: log available encoders
        logger.debug(f"Found {len(self.all_available)} audio codecs/encoders")

        # Warn if critical encoders are missing
        self._check_critical_encoders()

    def _check_critical_encoders(self):
        """Check and warn about missing critical encoders"""
        critical_encoders = {
            "libmp3lame": "MP3",
            "aac": "AAC/M4A",
            "flac": "FLAC",
        }

        important_encoders = {
            "libvorbis": "OGG Vorbis",
            "vorbis": "OGG Vorbis (native)",
            "libopus": "Opus",
        }

        for encoder, format_name in critical_encoders.items():
            if encoder not in self.all_available:
                logger.warning(f"⚠️ Critical encoder '{encoder}' for {format_name} not found!")

        vorbis_found = any(e in self.all_available for e in ["libvorbis", "vorbis"])
        opus_found = any(e in self.all_available for e in ["libopus", "opus"])

        if not vorbis_found:
            logger.warning("⚠️ No Vorbis encoder found! OGG conversion may fail.")
        if not opus_found:
            logger.warning("⚠️ No Opus encoder found! Opus conversion may fail.")

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

            # Check if output format is read-only
            if output_format in self.READ_ONLY_FORMATS:
                logger.warning(f"Format {output_format} is usually read-only, conversion may fail")

            # Create output directory
            os.makedirs(output_dir, exist_ok=True)

            # Generate output filename
            input_path = Path(input_file)
            output_filename = f"{input_path.stem}.{output_format}"
            output_file = os.path.join(output_dir, output_filename)

            # Determine codec
            if codec == "auto":
                codec = self._get_best_codec(output_format)
            elif codec == "copy":
                # Validate if copy is possible
                if not self._can_copy_audio(input_file, output_format):
                    logger.warning(f"Cannot copy codec for {input_file} → {output_format}, using auto-selection")
                    codec = self._get_best_codec(output_format)

            # Validate codec availability
            if codec not in self.all_available and codec != "copy":
                logger.warning(f"Codec {codec} not available, using auto-selection")
                codec = self._get_best_codec(output_format)

            # Use fallback conversion
            return self._convert_with_fallback(
                input_file=input_file,
                output_file=output_file,
                output_format=output_format,
                codec=codec,
                bitrate=bitrate,
                sample_rate=sample_rate,
                channels=channels,
                quality=quality,
                preserve_metadata=preserve_metadata,
                progress_callback=progress_callback,
            )

        except (OSError, ValueError) as e:
            logger.error(f"Audio conversion error: {e}", exc_info=True)
            return None

    def _convert_with_fallback(
        self,
        input_file: str,
        output_file: str,
        output_format: str,
        codec: str,
        bitrate: str | None,
        sample_rate: int | None,
        channels: int | None,
        quality: str | None,
        preserve_metadata: bool,
        progress_callback: Callable[[float, str], None] | None,
    ) -> str | None:
        """Convert with automatic fallback if codec fails"""

        # Get all compatible codecs for this format
        compatible_codecs = self.FORMAT_CODEC_COMPATIBILITY.get(output_format, [codec])

        # Build list of codecs to try
        codecs_to_try = []

        # Start with requested codec if valid
        if codec in compatible_codecs:
            codecs_to_try.append(codec)

        # Add all compatible codecs that are available
        for compatible_codec in compatible_codecs:
            if compatible_codec in self.all_available and compatible_codec not in codecs_to_try:
                codecs_to_try.append(compatible_codec)

        # If no codecs available, try the first compatible one anyway
        if not codecs_to_try and compatible_codecs:
            codecs_to_try.append(compatible_codecs[0])
            logger.warning(f"No available encoder found for {output_format}, trying {compatible_codecs[0]} anyway")

        # Try each codec until one succeeds
        for attempt, current_codec in enumerate(codecs_to_try, 1):
            if attempt > 1:
                logger.warning(f"Trying fallback codec: {current_codec} (attempt {attempt}/{len(codecs_to_try)})")
                if progress_callback:
                    progress_callback(0.05, f"⚠️ Retrying with {current_codec}...")

            # Build parameters
            params = {
                "audio_codec": current_codec,
                "audio_bitrate": bitrate if current_codec != "copy" else None,
                "sample_rate": sample_rate if current_codec != "copy" else None,
                "channels": channels if current_codec != "copy" else None,
                "no_video": True,
                "preserve_metadata": preserve_metadata,
                "format": self.FORMAT_MAPPING.get(output_format, output_format),
            }

            # Add input codec info for bitstream filters
            if current_codec == "copy":
                info = self.ffmpeg.get_file_info(input_file)
                if info and "streams" in info:
                    for stream in info["streams"]:
                        if stream.get("codec_type") == "audio":
                            params["input_audio_codec"] = stream.get("codec_name", "")
                            break

            # Add quality settings or experimental flags
            custom_params = []

            if quality and current_codec != "copy":
                custom_params.extend(self._get_quality_params(output_format, quality))

            # Add experimental flag for experimental codecs
            if current_codec in self.EXPERIMENTAL_CODECS:
                custom_params.extend(["-strict", "-2"])
                logger.debug(f"Added -strict -2 for experimental codec {current_codec}")

            if custom_params:
                params["custom_params"] = custom_params

            # Build and execute command
            command = self.ffmpeg.build_command(input_file, output_file, params)

            if progress_callback and attempt == 1:
                progress_callback(0.1, "Starting conversion...")

            success = self.ffmpeg.execute(command, progress_callback)

            if success and os.path.exists(output_file):
                if attempt > 1:
                    logger.info(f"✅ Conversion succeeded with fallback codec: {current_codec}")
                else:
                    logger.info(f"✅ Successfully converted: {output_file}")
                if progress_callback:
                    progress_callback(1.0, "Completed!")
                return output_file

            # Check if we should try next fallback
            if attempt < len(codecs_to_try):
                logger.warning(f"❌ Codec {current_codec} failed, trying next fallback...")
                # Clean up failed output
                if os.path.exists(output_file):
                    try:
                        os.remove(output_file)
                    except OSError:
                        pass
            else:
                logger.error(f"❌ All {len(codecs_to_try)} codec attempts failed for: {input_file}")
                return None

        return None

    def _can_copy_audio(self, input_file: str, output_format: str) -> bool:
        """Check if audio codec can be copied without re-encoding"""
        can_copy, codec_name = self.ffmpeg.can_copy_codec(input_file, output_format, "audio")

        if not can_copy:
            logger.debug(f"Audio copy not possible: {codec_name} → {output_format}")

        return can_copy

    def _get_best_codec(self, fmt: str) -> str:
        """Get best available codec for format"""

        # Get compatible codecs for this format
        compatible = self.FORMAT_CODEC_COMPATIBILITY.get(fmt, [])

        if not compatible:
            logger.warning(f"No codec mapping for format {fmt}, using generic")
            return "pcm_s16le"

        # Find first available compatible codec
        for codec in compatible:
            if codec in self.all_available:
                logger.debug(f"Selected codec {codec} for format {fmt}")
                return codec

        # If no available codec found, return first compatible (will try with -strict -2)
        logger.warning(f"No available encoder for {fmt}, will try {compatible[0]} with experimental flag")
        return compatible[0]

    def _get_quality_params(self, fmt: str, quality: str) -> list:
        """Get quality-specific parameters"""
        params = []

        if fmt == "mp3":
            # MP3 VBR quality (0-9, lower is better)
            quality_map = {"highest": "0", "high": "2", "medium": "4", "low": "6"}
            q = quality_map.get(quality, "2")
            params.extend(["-q:a", q])

        elif fmt in ("ogg", "oga", "opus"):
            # Vorbis/Opus quality
            quality_map = {"highest": "10", "high": "8", "medium": "6", "low": "4"}
            q = quality_map.get(quality, "8")
            params.extend(["-q:a", q])

        elif fmt == "flac":
            # FLAC compression level (0-12)
            quality_map = {"highest": "12", "high": "8", "medium": "5", "low": "0"}
            q = quality_map.get(quality, "5")
            params.extend(["-compression_level", q])

        elif fmt in ("aac", "m4a"):
            # AAC VBR quality
            quality_map = {"highest": "2", "high": "3", "medium": "4", "low": "5"}
            q = quality_map.get(quality, "4")
            params.extend(["-q:a", q])

        return params

    def get_supported_formats(self) -> list:
        """Get list of supported audio formats"""
        available = self.detector.get_audio_formats()

        # Filter out read-only formats if no encoder available
        supported = []
        for fmt in self.FORMAT_MAPPING:
            # Check if format is available in FFmpeg
            if self.FORMAT_MAPPING[fmt] in available or fmt in available:
                # Check if we have at least one encoder for this format
                compatible_codecs = self.FORMAT_CODEC_COMPATIBILITY.get(fmt, [])
                has_encoder = any(codec in self.all_available for codec in compatible_codecs)

                if has_encoder or fmt not in self.READ_ONLY_FORMATS:
                    supported.append(fmt)

        return sorted(supported)

    def get_file_info(self, file_path: str) -> dict[str, any]:
        """Get audio file information"""
        return self.ffmpeg.get_file_info(file_path)
