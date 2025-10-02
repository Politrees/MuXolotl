"""Format detection and validation for MuXolotl"""

import re
import subprocess

from utils.logger import get_logger

logger = get_logger()


class FormatDetector:
    """Detect and validate available formats"""

    def __init__(self):
        """Initialize format detector"""
        self._audio_formats = None
        self._video_formats = None
        self._audio_codecs = None
        self._video_codecs = None
        self._audio_encoders = None
        self._video_encoders = None
        self._hwaccels = None
        self._working_hwaccels = None

    def _run_ffmpeg(self, args: list[str]) -> str:
        """Run FFmpeg command and return output"""
        try:
            result = subprocess.run(
                ["ffmpeg"] + args,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=5,
            )
            return result.stdout
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError) as e:
            logger.error(f"FFmpeg command failed: {e}")
            return ""

    def get_audio_formats(self) -> set[str]:
        """Get all available audio formats"""
        if self._audio_formats is not None:
            return self._audio_formats

        output = self._run_ffmpeg(["-hide_banner", "-formats"])
        formats = set()

        # Parse muxer formats (those with E flag)
        for line in output.splitlines():
            if re.match(r"^\s*[D\s]*E\s+", line):
                match = re.search(r"^\s*[D\s]*E\s+([^\s]+)", line)
                if match:
                    format_names = match.group(1)
                    for fmt in format_names.split(","):
                        formats.add(fmt.strip())

        # Common audio format mappings
        audio_formats = {
            "mp3",
            "wav",
            "flac",
            "ogg",
            "aac",
            "m4a",
            "opus",
            "wma",
            "aiff",
            "ac3",
            "dts",
            "amr",
            "ape",
            "tta",
            "wv",
            "mp2",
            "au",
            "caf",
            "w64",
            "spx",
        }

        self._audio_formats = audio_formats & formats
        if not self._audio_formats:
            self._audio_formats = {"mp3", "wav", "flac", "ogg", "aac", "m4a"}

        return self._audio_formats

    def get_video_formats(self) -> set[str]:
        """Get all available video formats"""
        if self._video_formats is not None:
            return self._video_formats

        output = self._run_ffmpeg(["-hide_banner", "-formats"])
        formats = set()

        for line in output.splitlines():
            if re.match(r"^\s*[D\s]*E\s+", line):
                match = re.search(r"^\s*[D\s]*E\s+([^\s]+)", line)
                if match:
                    format_names = match.group(1)
                    for fmt in format_names.split(","):
                        formats.add(fmt.strip())

        # Map extensions to FFmpeg format names
        video_mapping = {
            "mp4": "mp4",
            "mkv": "matroska",
            "avi": "avi",
            "mov": "mov",
            "webm": "webm",
            "flv": "flv",
            "mpeg": "mpeg",
            "mpg": "mpeg",
            "ts": "mpegts",
            "m2ts": "mpegts",
            "mts": "mpegts",
            "mxf": "mxf",
            "3gp": "3gp",
            "3g2": "3g2",
            "wmv": "asf",
            "asf": "asf",
            "vob": "vob",
            "m4v": "mp4",
            # "ogv": "ogg", | don't work
            "f4v": "flv",
        }

        self._video_formats = {ext for ext, fmt in video_mapping.items() if fmt in formats}

        if not self._video_formats:
            self._video_formats = {"mp4", "mkv", "avi", "mov", "webm"}

        return self._video_formats

    def get_audio_codecs(self) -> set[str]:
        """Get all available audio codecs (decoders)"""
        if self._audio_codecs is not None:
            return self._audio_codecs

        output = self._run_ffmpeg(["-hide_banner", "-codecs"])
        codecs = set()

        for line in output.splitlines():
            match = re.match(r"^\s*[D\.][E\.]A[^\s]*\s+([^\s]+)", line)
            if match:
                codecs.add(match.group(1).strip())

        self._audio_codecs = codecs
        return self._audio_codecs

    def get_video_codecs(self) -> set[str]:
        """Get all available video codecs (decoders)"""
        if self._video_codecs is not None:
            return self._video_codecs

        output = self._run_ffmpeg(["-hide_banner", "-codecs"])
        codecs = set()

        for line in output.splitlines():
            match = re.match(r"^\s*[D\.][E\.]V[^\s]*\s+([^\s]+)", line)
            if match:
                codecs.add(match.group(1).strip())

        self._video_codecs = codecs
        return self._video_codecs

    def get_audio_encoders(self) -> set[str]:
        """Get all available audio encoders"""
        if self._audio_encoders is not None:
            return self._audio_encoders

        output = self._run_ffmpeg(["-hide_banner", "-encoders"])
        encoders = set()

        for line in output.splitlines():
            match = re.match(r"^\s*A[^\s]*\s+([^\s]+)", line)
            if match:
                encoders.add(match.group(1).strip())

        self._audio_encoders = encoders
        return self._audio_encoders

    def get_video_encoders(self) -> set[str]:
        """Get all available video encoders"""
        if self._video_encoders is not None:
            return self._video_encoders

        output = self._run_ffmpeg(["-hide_banner", "-encoders"])
        encoders = set()

        for line in output.splitlines():
            match = re.match(r"^\s*V[^\s]*\s+([^\s]+)", line)
            if match:
                encoders.add(match.group(1).strip())

        self._video_encoders = encoders
        return self._video_encoders

    def get_hwaccels(self) -> set[str]:
        """Get all available hardware accelerations"""
        if self._hwaccels is not None:
            return self._hwaccels

        output = self._run_ffmpeg(["-hide_banner", "-hwaccels"])
        hwaccels = set()

        for line in output.splitlines():
            line = line.strip()
            if line and not line.startswith("Hardware"):
                hwaccels.add(line)

        self._hwaccels = hwaccels
        return self._hwaccels

    def test_hwaccel(self, hwaccel: str) -> bool:
        """Test if hardware acceleration actually works

        Args:
            hwaccel: Hardware acceleration method to test

        Returns:
            True if working, False otherwise

        """
        try:
            # Try to create a simple test command
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-v",
                    "error",
                    "-hwaccel",
                    hwaccel,
                    "-f",
                    "lavfi",
                    "-i",
                    "nullsrc=s=256x256:d=0.1",
                    "-f",
                    "null",
                    "-",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )

            # Check if there were errors related to hwaccel
            if result.returncode == 0:
                return True

            error_output = result.stderr.lower()
            # Common error patterns that indicate hwaccel doesn't work
            error_patterns = [
                "cannot load",
                "could not dynamically load",
                "device creation failed",
                "no device available",
                "hardware device setup failed",
                "not found",
                "not supported",
            ]

            for pattern in error_patterns:
                if pattern in error_output:
                    return False

            return True

        except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError) as e:
            logger.debug(f"Hardware acceleration test failed for {hwaccel}: {e}")
            return False

    def get_working_hwaccels(self) -> set[str]:
        """Get only hardware accelerations that actually work

        Returns:
            Set of working hardware acceleration methods

        """
        if self._working_hwaccels is not None:
            return self._working_hwaccels

        available_hwaccels = self.get_hwaccels()
        working = set()

        # Test only once, cache results
        for hwaccel in available_hwaccels:
            if self.test_hwaccel(hwaccel):
                working.add(hwaccel)

        self._working_hwaccels = working

        if working:
            logger.debug(f"Hardware acceleration available: {', '.join(sorted(working))}")
        else:
            logger.debug("No working hardware acceleration found")

        return self._working_hwaccels

    def test_encoder(self, encoder: str, gpu_detector=None) -> bool:
        """Test if encoder actually works with GPU-specific optimizations

        Args:
            encoder: Encoder name to test
            gpu_detector: Optional GPUDetector instance for smarter testing

        Returns:
            True if working, False otherwise

        """
        try:
            is_hardware = any(hw in encoder.lower() for hw in ["nvenc", "qsv", "amf", "vaapi", "videotoolbox"])

            # Build test command
            base_cmd = ["ffmpeg", "-hide_banner", "-v", "error"]

            # Add hardware-specific initialization
            if is_hardware:
                if "amf" in encoder.lower():
                    # AMD AMF needs special handling - use color filter instead of testsrc
                    base_cmd.extend([
                        "-f", "lavfi",
                        "-i", "color=c=black:s=256x256:d=0.1:r=1",
                        "-c:v", encoder,
                    ])
                    logger.debug(f"Testing AMF encoder {encoder} with color filter")

                elif "qsv" in encoder.lower():
                    # Intel QSV - try with hardware device initialization
                    base_cmd.extend([
                        "-init_hw_device", "qsv=hw",
                        "-filter_hw_device", "hw",
                        "-f", "lavfi",
                        "-i", "color=c=black:s=256x256:d=0.1:r=1",
                        "-c:v", encoder,
                    ])
                    logger.debug(f"Testing QSV encoder {encoder} with hw device init")

                elif "nvenc" in encoder.lower():
                    # NVIDIA NVENC
                    base_cmd.extend([
                        "-f", "lavfi",
                        "-i", "color=c=black:s=256x256:d=0.1:r=1",
                        "-c:v", encoder,
                    ])
                    logger.debug(f"Testing NVENC encoder {encoder}")

                elif "videotoolbox" in encoder.lower():
                    # Apple VideoToolbox
                    base_cmd.extend([
                        "-f", "lavfi",
                        "-i", "color=c=black:s=256x256:d=0.1:r=1",
                        "-c:v", encoder,
                    ])
                    logger.debug(f"Testing VideoToolbox encoder {encoder}")

                elif "vaapi" in encoder.lower():
                    # Linux VAAPI
                    base_cmd.extend([
                        "-init_hw_device", "vaapi=hw:/dev/dri/renderD128",
                        "-filter_hw_device", "hw",
                        "-f", "lavfi",
                        "-i", "color=c=black:s=256x256:d=0.1:r=1",
                        "-c:v", encoder,
                    ])
                    logger.debug(f"Testing VAAPI encoder {encoder}")

                else:
                    # Generic hardware
                    base_cmd.extend([
                        "-f", "lavfi",
                        "-i", "testsrc=duration=0.1:size=256x256:rate=1",
                        "-c:v", encoder,
                    ])
            else:
                # Software encoder
                base_cmd.extend([
                    "-f", "lavfi",
                    "-i", "testsrc=duration=0.1:size=256x256:rate=1",
                    "-c:v", encoder,
                ])

            # Complete command
            base_cmd.extend(["-frames:v", "1", "-f", "null", "-"])

            # Run test with appropriate timeout
            timeout = 20 if is_hardware else 10

            result = subprocess.run(
                base_cmd,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
            )

            if result.returncode == 0:
                logger.debug(f"✅ Encoder {encoder} test passed")
                return True

            # Analyze errors
            error_output = result.stderr.lower()

            # Critical errors (encoder definitely doesn't work)
            critical_patterns = [
                "unknown encoder",
                "encoder not found",
                "cannot load",
                "not compiled",
                "could not find encoder",
            ]

            for pattern in critical_patterns:
                if pattern in error_output:
                    logger.debug(f"❌ Encoder {encoder}: {pattern}")
                    return False

            # Hardware-specific errors
            hw_error_patterns = [
                "no device available",
                "failed to open",
                "cannot initialize",
                "not supported",
                "device creation failed",
                "no hwaccel device",
            ]

            for pattern in hw_error_patterns:
                if pattern in error_output:
                    logger.debug(f"⚠️ Encoder {encoder} unavailable: {pattern}")
                    return False

            # Special handling for MFX/QSV errors (these can be flaky)
            if "qsv" in encoder.lower():
                if any(err in error_output for err in ["mfx", "session", "error creating"]):
                    logger.debug(f"⚠️ QSV encoder {encoder} has initialization issues, marking as unavailable")
                    return False

            # Special handling for AMF errors
            if "amf" in encoder.lower():
                if any(err in error_output for err in ["amf", "failed to initialize", "context creation"]):
                    logger.debug(f"⚠️ AMF encoder {encoder} initialization failed")
                    return False

            # If there's an error but not critical, be cautious
            if result.returncode != 0:
                logger.debug(f"⚠️ Encoder {encoder} test returned error {result.returncode}")
                # For hardware encoders, be strict
                if is_hardware:
                    logger.debug(f"❌ Hardware encoder {encoder} failed test, marking unavailable")
                    return False
                # For software encoders, be more lenient
                logger.debug(f"✅ Software encoder {encoder} assumed working despite error")
                return True

            return True

        except subprocess.TimeoutExpired:
            logger.debug(f"⏱️ Encoder {encoder} test timed out")
            return False
        except (subprocess.SubprocessError, OSError) as e:
            logger.debug(f"❌ Encoder test failed for {encoder}: {e}")
            return False
