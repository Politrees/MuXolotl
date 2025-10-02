"""Video conversion module for MuXolotl - WITH HARDWARE ENCODING SUPPORT"""

import os
from collections.abc import Callable
from pathlib import Path

from utils.logger import get_logger

from .ffmpeg_wrapper import FFmpegWrapper
from .format_detector import FormatDetector

logger = get_logger()


class VideoConverter:
    """Handle video file conversions with hardware encoding support"""

    # Format to FFmpeg format mapping
    FORMAT_MAPPING = {
        "mp4": "mp4",
        "m4v": "mp4",
        "mov": "mov",
        "avi": "avi",
        "mkv": "matroska",
        "webm": "webm",
        "flv": "flv",
        "ogv": "ogg",
        "mpeg": "mpeg",
        "mpg": "mpeg",
        "ts": "mpegts",
        "m2ts": "mpegts",
        "mxf": "mxf",
        "3gp": "3gp",
        "3g2": "3g2",
        "asf": "asf",
        "wmv": "asf",
        "vob": "vob",
    }

    # Recommended audio codecs for video formats
    AUDIO_CODEC_MAPPING = {
        "mp4": "aac",
        "m4v": "aac",
        "mkv": "aac",
        "mov": "aac",
        "webm": "libopus",
        "avi": "mp3",
        "flv": "mp3",
        "ogv": "libvorbis",
        "mpeg": "mp2",
        "mpg": "mp2",
        "wmv": "wmav2",
        "3gp": "aac",
        "ts": "aac",
        "m2ts": "aac",
    }

    def __init__(self):
        """Initialize video converter"""
        self.ffmpeg = FFmpegWrapper()
        self.detector = FormatDetector()
        self.available_video_codecs = self.detector.get_video_codecs()
        self.available_audio_codecs = self.detector.get_audio_encoders()
        self.available_hwaccels = self.detector.get_hwaccels()
        self.working_hwaccels = None

        # Detect hardware encoders
        logger.debug("Detecting hardware encoders...")
        self.hardware_encoders = self._detect_hardware_encoders()

    def _detect_hardware_encoders(self) -> dict[str, str | None]:
        """Detect available hardware encoders

        Returns:
            Dictionary mapping codec types to best available encoder

        """
        encoders = {
            "h264": None,
            "hevc": None,
            "vp9": None,
            "av1": None,
        }

        available_encoders = self.detector.get_video_encoders()

        # H.264 encoders (priority order: best performance first)
        h264_priority = [
            "h264_nvenc",          # NVIDIA (fastest, excellent quality)
            "h264_qsv",            # Intel Quick Sync (very fast)
            "h264_amf",            # AMD (fast)
            "h264_videotoolbox",   # macOS (fast)
            "h264_vaapi",          # Linux VAAPI
            "h264_v4l2m2m",        # Raspberry Pi
            "libx264",             # CPU fallback (slower but universal)
        ]

        for encoder in h264_priority:
            if encoder in available_encoders:
                # Test if encoder actually works
                if self.detector.test_encoder(encoder):
                    encoders["h264"] = encoder
                    encoder_name = str(encoder)  # Ensure it's a string
                    if "nvenc" in encoder_name or "qsv" in encoder_name or "amf" in encoder_name:
                        logger.info(f"🚀 Hardware H.264 encoder found: {encoder}")
                    else:
                        logger.debug(f"Using H.264 encoder: {encoder}")
                    break

        # HEVC/H.265 encoders
        hevc_priority = [
            "hevc_nvenc",
            "hevc_qsv",
            "hevc_amf",
            "hevc_videotoolbox",
            "hevc_vaapi",
            "libx265",
        ]

        for encoder in hevc_priority:
            if encoder in available_encoders:
                if self.detector.test_encoder(encoder):
                    encoders["hevc"] = encoder
                    encoder_name = str(encoder)
                    if "nvenc" in encoder_name or "qsv" in encoder_name or "amf" in encoder_name:
                        logger.info(f"🚀 Hardware HEVC encoder found: {encoder}")
                    break

        # VP9 encoders
        vp9_priority = [
            "vp9_qsv",
            "vp9_vaapi",
            "libvpx-vp9",
        ]

        for encoder in vp9_priority:
            if encoder in available_encoders:
                if self.detector.test_encoder(encoder):
                    encoders["vp9"] = encoder
                    break

        # AV1 encoders (future-proofing)
        av1_priority = [
            "av1_nvenc",
            "av1_qsv",
            "av1_amf",
            "libsvtav1",
            "libaom-av1",
        ]

        for encoder in av1_priority:
            if encoder in available_encoders:
                if self.detector.test_encoder(encoder):
                    encoders["av1"] = encoder
                    break

        return encoders

    def get_encoder_info(self) -> str:
        """Get human-readable info about available encoders"""
        info = []

        if self.hardware_encoders["h264"]:
            encoder = str(self.hardware_encoders["h264"])
            if "nvenc" in encoder:
                info.append("H.264: NVIDIA GPU (Very Fast)")
            elif "qsv" in encoder:
                info.append("H.264: Intel Quick Sync (Fast)")
            elif "amf" in encoder:
                info.append("H.264: AMD GPU (Fast)")
            elif "videotoolbox" in encoder:
                info.append("H.264: Apple Hardware (Fast)")
            else:
                info.append("H.264: CPU (Slow)")

        if self.hardware_encoders["hevc"]:
            encoder = str(self.hardware_encoders["hevc"])
            if "nvenc" in encoder or "qsv" in encoder or "amf" in encoder:
                info.append("HEVC: Hardware Accelerated")

        return " | ".join(info) if info else "CPU encoding only"

    def convert(
        self,
        input_file: str,
        output_dir: str,
        output_format: str,
        video_codec: str = "auto",
        audio_codec: str = "auto",
        video_bitrate: str = "auto",
        audio_bitrate: str = "192k",
        crf: int | None = None,
        preset: str = "medium",
        resolution: str | None = None,
        fps: int | None = None,
        hwaccel: str = "auto",
        preserve_metadata: bool = True,
        tune: str | None = None,
        progress_callback: Callable[[float, str], None] | None = None,
    ) -> str | None:
        """Convert video file with hardware encoding support

        Args:
            input_file: Path to input file
            output_dir: Directory for output file
            output_format: Output format extension
            video_codec: Video codec ('auto' or specific codec)
            audio_codec: Audio codec ('auto' or specific codec)
            video_bitrate: Video bitrate (e.g., '2M', '5M') or 'auto'
            audio_bitrate: Audio bitrate (e.g., '192k', '320k')
            crf: Constant Rate Factor (quality, 0-51, lower is better)
            preset: Encoding preset (ultrafast, fast, medium, slow, etc.)
            resolution: Output resolution (e.g., '1920x1080', '1280x720')
            fps: Output framerate
            hwaccel: Hardware acceleration ('auto', 'none', or specific)
            preserve_metadata: Whether to preserve metadata
            tune: Tune parameter (e.g., 'fastdecode', 'zerolatency')
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

            # Determine codecs
            if video_codec == "auto":
                video_codec = self._get_best_video_codec(output_format)

            if audio_codec == "auto":
                audio_codec = self._get_best_audio_codec(output_format)

            # Determine hardware acceleration for decoding
            actual_hwaccel = None
            if hwaccel == "auto":
                actual_hwaccel = self._get_best_hwaccel()
            elif hwaccel != "none":
                if self._verify_hwaccel(hwaccel):
                    actual_hwaccel = hwaccel
                else:
                    logger.warning(f"Requested hwaccel '{hwaccel}' not available")
                    actual_hwaccel = None

            # Build parameters
            params = {
                "video_codec": video_codec,
                "audio_codec": audio_codec,
                "video_bitrate": video_bitrate if video_bitrate != "auto" else None,
                "audio_bitrate": audio_bitrate,
                "preset": preset,
                "hwaccel": actual_hwaccel,
                "preserve_metadata": preserve_metadata,
                "format": self.FORMAT_MAPPING.get(output_format, output_format),
                "tune": tune,
            }

            # Add CRF for quality-based encoding (not for hardware encoders with fixed bitrate)
            if crf is not None and video_codec != "copy":
                # Hardware encoders use different quality settings
                if "nvenc" in video_codec or "qsv" in video_codec or "amf" in video_codec:
                    # Convert CRF to quality parameter for hardware encoders
                    # CRF 0-51 → Quality 51-0 (inverted for nvenc)
                    params["cq"] = 51 - crf if "nvenc" in video_codec else crf
                else:
                    params["crf"] = crf

            # Add custom parameters for resolution and fps
            custom_params = []

            if resolution:
                custom_params.extend(["-s", resolution])

            if fps:
                custom_params.extend(["-r", str(fps)])

            # Format-specific optimizations
            if output_format in ["mp4", "m4v", "mov"]:
                custom_params.extend(["-movflags", "+faststart"])

            if custom_params:
                params["custom_params"] = custom_params

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
            logger.error(f"Video conversion error: {e}", exc_info=True)
            return None

    def extract_audio(
        self,
        input_file: str,
        output_dir: str,
        output_format: str = "mp3",
        audio_codec: str = "auto",
        audio_bitrate: str = "192k",
        sample_rate: int | None = None,
        progress_callback: Callable[[float, str], None] | None = None,
    ) -> str | None:
        """Extract audio from video file

        Args:
            input_file: Path to input video file
            output_dir: Directory for output file
            output_format: Output audio format
            audio_codec: Audio codec
            audio_bitrate: Audio bitrate
            sample_rate: Sample rate
            progress_callback: Optional callback for progress updates

        Returns:
            Path to output file or None if failed

        """
        from .audio_converter import AudioConverter

        try:
            if not os.path.exists(input_file):
                logger.error(f"Input file not found: {input_file}")
                return None

            os.makedirs(output_dir, exist_ok=True)

            input_path = Path(input_file)
            output_filename = f"{input_path.stem}.{output_format}"
            output_file = os.path.join(output_dir, output_filename)

            # Determine codec
            if audio_codec == "auto":
                audio_conv = AudioConverter()
                audio_codec = audio_conv._get_best_codec(output_format)

            # Audio format mapping
            format_mapping = AudioConverter.FORMAT_MAPPING

            params = {
                "audio_codec": audio_codec,
                "audio_bitrate": audio_bitrate,
                "sample_rate": sample_rate,
                "no_video": True,
                "format": format_mapping.get(output_format, output_format),
            }

            command = self.ffmpeg.build_command(input_file, output_file, params)

            if progress_callback:
                progress_callback(0.1, "Extracting audio...")

            success = self.ffmpeg.execute(command, progress_callback)

            if success and os.path.exists(output_file):
                logger.info(f"Successfully extracted audio: {output_file}")
                if progress_callback:
                    progress_callback(1.0, "Completed!")
                return output_file
            logger.error(f"Audio extraction failed for: {input_file}")
            return None

        except (OSError, IOError, ImportError) as e:
            logger.error(f"Audio extraction error: {e}", exc_info=True)
            return None

    def _verify_hwaccel(self, hwaccel: str) -> bool:
        """Verify if a hardware acceleration method works"""
        if self.working_hwaccels is None:
            self.working_hwaccels = self.detector.get_working_hwaccels()

        return hwaccel in self.working_hwaccels

    def _get_best_video_codec(self, fmt: str) -> str:
        """Get best available video codec for format (prefer hardware)"""
        # For MP4/MKV/AVI/MOV - try to use hardware H.264 encoder
        if fmt in ["mp4", "mkv", "avi", "mov", "m4v", "ts", "m2ts"]:
            if self.hardware_encoders["h264"]:
                return self.hardware_encoders["h264"]

        # For WebM - try VP9 hardware encoder
        if fmt == "webm":
            if self.hardware_encoders["vp9"]:
                return self.hardware_encoders["vp9"]

        # Fallback to software encoders
        fallback_map = {
            "mp4": ["libx264"],
            "mkv": ["libx264", "libx265"],
            "webm": ["libvpx-vp9", "libvpx"],
            "avi": ["libx264", "mpeg4"],
            "mov": ["libx264"],
        }

        for codec in fallback_map.get(fmt, ["libx264"]):
            if codec in self.available_video_codecs:
                return codec

        return "copy"

    def _get_best_audio_codec(self, fmt: str) -> str:
        """Get best available audio codec for format"""
        recommended = self.AUDIO_CODEC_MAPPING.get(fmt)
        if recommended and recommended in self.available_audio_codecs:
            return recommended

        # Fallback
        fallback_map = {
            "mp4": ["aac", "libfdk_aac"],
            "mkv": ["aac", "libopus", "libvorbis"],
            "webm": ["libopus", "libvorbis"],
            "avi": ["libmp3lame", "mp3", "aac"],
        }

        for codec in fallback_map.get(fmt, ["aac"]):
            if codec in self.available_audio_codecs:
                return codec

        return "copy"

    def _get_best_hwaccel(self) -> str | None:
        """Get best available and working hardware acceleration"""
        if self.working_hwaccels is None:
            self.working_hwaccels = self.detector.get_working_hwaccels()

        # Priority order for decoding acceleration
        priority = ["cuda", "qsv", "dxva2", "d3d11va", "videotoolbox", "vaapi"]

        for hwaccel in priority:
            if hwaccel in self.working_hwaccels:
                logger.debug(f"Using hardware acceleration: {hwaccel}")
                return hwaccel

        return None

    def get_supported_formats(self) -> list:
        """Get list of supported video formats"""
        available = self.detector.get_video_formats()
        return sorted([
            fmt for fmt in self.FORMAT_MAPPING
            if self.FORMAT_MAPPING[fmt] in available or fmt in available
        ])

    def get_file_info(self, file_path: str) -> dict[str, any]:
        """Get video file information"""
        return self.ffmpeg.get_file_info(file_path)
