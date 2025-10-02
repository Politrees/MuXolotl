"""FFmpeg wrapper for MuXolotl
Provides low-level FFmpeg command construction and execution
"""

import json
import re
import subprocess
from collections.abc import Callable

from utils.logger import get_logger

logger = get_logger()


class FFmpegWrapper:
    """Wrapper for FFmpeg operations"""

    # Comprehensive bitstream filters for all known codecs
    BITSTREAM_FILTERS = {
        # Video codecs
        "h264": {
            "avi": "h264_mp4toannexb",
            "mpegts": "h264_mp4toannexb",
            "mpeg": "h264_mp4toannexb",
            "vob": "h264_mp4toannexb",
        },
        "hevc": {
            "avi": "hevc_mp4toannexb",
            "mpegts": "hevc_mp4toannexb",
            "mpeg": "hevc_mp4toannexb",
        },
        "mpeg4": {
            "mpegts": "mpeg4_unpack_bframes",
        },
        # Audio codecs
        "aac": {
            "mpegts": "aac_adtstoasc",
            "mpeg": "aac_adtstoasc",
        },
        "mp3": {
            "mpegts": "mp3decomp",
        },
    }

    def __init__(self):
        """Initialize FFmpeg wrapper"""
        self._verify_ffmpeg()
        self.current_process = None
        self.should_cancel = False

    def _verify_ffmpeg(self):
        """Verify FFmpeg is available"""
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,
            )
            logger.debug("FFmpeg verified successfully")
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            logger.error(f"FFmpeg not found or not working: {e}")
            raise RuntimeError("FFmpeg is not available. Please install FFmpeg.") from e

    def cancel(self):
        """Cancel current operation"""
        self.should_cancel = True
        if self.current_process:
            try:
                self.current_process.terminate()
                logger.info("Conversion cancelled by user")
            except (OSError, subprocess.SubprocessError):
                pass

    def _get_bitstream_filter(self, codec: str, output_format: str) -> str | None:
        """Get required bitstream filter for codec and format combination

        Args:
            codec: Video/audio codec name
            output_format: Output format name (e.g., 'avi', 'mpegts')

        Returns:
            Bitstream filter name or None

        """
        # Normalize codec and format
        codec_base = codec.lower().split("_")[0] if "_" in codec else codec.lower()
        fmt = output_format.lower()

        if codec_base in self.BITSTREAM_FILTERS:
            return self.BITSTREAM_FILTERS[codec_base].get(fmt)

        return None

    def build_command(
        self,
        input_file: str,
        output_file: str,
        params: dict[str, any],
    ) -> list[str]:
        """Build FFmpeg command from parameters

        Args:
            input_file: Input file path
            output_file: Output file path
            params: Dictionary of FFmpeg parameters

        Returns:
            List of command arguments

        """
        cmd = ["ffmpeg", "-hide_banner", "-y"]

        # Hardware acceleration for decoding
        if params.get("hwaccel"):
            cmd.extend(["-hwaccel", params["hwaccel"]])

        # Input file
        cmd.extend(["-i", input_file])

        # Video codec
        if params.get("video_codec"):
            if params["video_codec"] == "copy":
                cmd.extend(["-c:v", "copy"])

                # Add bitstream filter if needed for copy
                if params.get("format") and params.get("input_video_codec"):
                    bsf = self._get_bitstream_filter(params["input_video_codec"], params["format"])
                    if bsf:
                        cmd.extend(["-bsf:v", bsf])
                        logger.debug(f"Added video bitstream filter: {bsf}")
            else:
                cmd.extend(["-c:v", params["video_codec"]])

                # Hardware encoder quality (for nvenc, qsv, amf)
                if params.get("cq") is not None:
                    codec = params["video_codec"]
                    if "nvenc" in codec:
                        cmd.extend(["-cq", str(params["cq"])])
                    elif "qsv" in codec:
                        cmd.extend(["-global_quality", str(params["cq"])])
                    elif "amf" in codec:
                        cmd.extend(["-qp_i", str(params["cq"]), "-qp_p", str(params["cq"])])

                # Software encoder quality (CRF)
                elif params.get("crf") is not None:
                    cmd.extend(["-crf", str(params["crf"])])

                # Video bitrate
                if params.get("video_bitrate"):
                    cmd.extend(["-b:v", params["video_bitrate"]])

                # Preset
                if params.get("preset"):
                    cmd.extend(["-preset", params["preset"]])

                # Tune (for software encoders)
                if params.get("tune"):
                    cmd.extend(["-tune", params["tune"]])

        # Audio codec
        if params.get("audio_codec"):
            if params["audio_codec"] == "copy":
                cmd.extend(["-c:a", "copy"])

                # Add bitstream filter if needed for copy
                if params.get("format") and params.get("input_audio_codec"):
                    bsf = self._get_bitstream_filter(params["input_audio_codec"], params["format"])
                    if bsf:
                        cmd.extend(["-bsf:a", bsf])
                        logger.debug(f"Added audio bitstream filter: {bsf}")
            else:
                cmd.extend(["-c:a", params["audio_codec"]])

                # Audio bitrate
                if params.get("audio_bitrate"):
                    cmd.extend(["-b:a", params["audio_bitrate"]])

                # Sample rate
                if params.get("sample_rate"):
                    cmd.extend(["-ar", str(params["sample_rate"])])

                # Channels
                if params.get("channels"):
                    cmd.extend(["-ac", str(params["channels"])])

        # Remove video stream (audio extraction)
        if params.get("no_video"):
            cmd.append("-vn")

        # Remove audio stream
        if params.get("no_audio"):
            cmd.append("-an")

        # Threads
        if params.get("threads"):
            cmd.extend(["-threads", str(params["threads"])])

        # Metadata
        if not params.get("preserve_metadata", True):
            cmd.extend(["-map_metadata", "-1"])

        # Output format
        if params.get("format"):
            cmd.extend(["-f", params["format"]])

        # Additional custom parameters
        if params.get("custom_params"):
            cmd.extend(params["custom_params"])

        # Output file
        cmd.append(output_file)

        return cmd

    def execute(
        self,
        command: list[str],
        progress_callback: Callable[[float, str], None] | None = None,
    ) -> bool:
        """Execute FFmpeg command

        Args:
            command: FFmpeg command as list
            progress_callback: Optional callback for progress updates (progress, status)

        Returns:
            True if successful, False otherwise

        """
        self.should_cancel = False

        try:
            logger.debug(f"Executing: {' '.join(command)}")

            with subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
            ) as process:
                self.current_process = process
                duration = None
                output_lines = []

                for line in process.stdout:
                    # Check if cancelled
                    if self.should_cancel:
                        process.terminate()
                        logger.info("Process cancelled by user")
                        return False

                    output_lines.append(line)

                    # Extract duration
                    if duration is None:
                        duration_match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2}\.\d{2})", line)
                        if duration_match:
                            h, m, s = duration_match.groups()
                            duration = int(h) * 3600 + int(m) * 60 + float(s)

                    # Extract progress
                    if progress_callback and duration:
                        time_match = re.search(r"time=(\d{2}):(\d{2}):(\d{2}\.\d{2})", line)
                        if time_match:
                            h, m, s = time_match.groups()
                            current_time = int(h) * 3600 + int(m) * 60 + float(s)
                            progress = min(current_time / duration, 1.0)

                            # Extract speed info
                            speed_match = re.search(r"speed=\s*([\d.]+)x", line)
                            speed_info = f" @ {speed_match.group(1)}x" if speed_match else ""

                            progress_callback(progress, f"Processing... {int(progress * 100)}%{speed_info}")

                process.wait()

                if process.returncode != 0:
                    error_output = "\n".join(output_lines[-20:])
                    logger.error(f"FFmpeg failed with code {process.returncode}:\n{error_output}")
                    return False

            logger.debug("FFmpeg command completed successfully")
            return True

        except (subprocess.SubprocessError, OSError) as e:
            logger.error(f"FFmpeg execution failed: {e}", exc_info=True)
            return False
        finally:
            self.current_process = None

    def get_file_info(self, file_path: str) -> dict[str, any]:
        """Get information about media file

        Args:
            file_path: Path to media file

        Returns:
            Dictionary with file information

        """
        try:
            result = subprocess.run(
                ["ffprobe", "-hide_banner", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", file_path],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                return json.loads(result.stdout)

        except (subprocess.SubprocessError, OSError, json.JSONDecodeError) as e:
            logger.error(f"Failed to get file info: {e}")

        return {}

    def can_copy_codec(self, input_file: str, output_format: str, stream_type: str = "audio") -> tuple[bool, str | None]:
        """Universally check if codec can be copied to output format

        This method works for ALL codecs by attempting a test conversion

        Args:
            input_file: Path to input file
            output_format: Target output format
            stream_type: 'audio' or 'video'

        Returns:
            Tuple of (can_copy: bool, codec_name: str | None)

        """
        try:
            # Get file info
            info = self.get_file_info(input_file)
            if not info or "streams" not in info:
                return False, None

            # Find stream
            target_stream = None
            for stream in info["streams"]:
                if stream.get("codec_type") == stream_type:
                    target_stream = stream
                    break

            if not target_stream:
                return False, None

            codec_name = target_stream.get("codec_name", "").lower()

            # Known impossible conversions (raw/uncompressed to compressed)
            if stream_type == "audio":
                pcm_codecs = {"pcm_s16le", "pcm_s24le", "pcm_s32le", "pcm_f32le", "pcm_f64le", "pcm_u8", "pcm_s16be", "pcm_s24be"}
                compressed_formats = {"mp3", "aac", "m4a", "ogg", "opus", "wma", "ac3", "dts", "ape", "tta"}

                if codec_name in pcm_codecs and output_format.lower() in compressed_formats:
                    logger.debug(f"Cannot copy PCM to compressed format: {codec_name} → {output_format}")
                    return False, codec_name

            # Try to perform a quick test conversion (0.5 second)
            test_result = self._test_copy_conversion(input_file, output_format, stream_type)

            return test_result, codec_name

        except (KeyError, ValueError, TypeError) as e:
            logger.debug(f"Copy check failed: {e}")
            return False, None

    def _test_copy_conversion(self, input_file: str, output_format: str, stream_type: str) -> bool:
        """Test if copy conversion will work by running quick FFmpeg test

        Args:
            input_file: Input file path
            output_format: Output format
            stream_type: 'audio' or 'video'

        Returns:
            True if copy will work, False otherwise

        """
        try:
            # Build test command (convert only 0.5 second)
            cmd = [
                "ffmpeg",
                "-v",
                "error",
                "-i",
                input_file,
                "-t",
                "0.5",  # Only 0.5 seconds
                "-c",
                "copy",
                "-f",
                output_format,
                "-",  # Output to stdout (null output)
            ]

            # Run test
            result = subprocess.run(
                cmd,
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
            )

            # Check for specific errors
            if result.returncode == 0:
                logger.debug(f"Copy test passed for {stream_type} → {output_format}")
                return True

            error_output = result.stderr.lower()

            # Known error patterns that indicate copy won't work
            error_patterns = [
                "invalid",
                "incompatible",
                "codec not currently supported",
                "bitstream filter",
                "malformed",
                "could not write header",
            ]

            for pattern in error_patterns:
                if pattern in error_output:
                    logger.debug(f"Copy not possible: {error_output[:100]}")
                    return False

            # If error but not critical, might still work
            return True

        except (subprocess.TimeoutExpired, OSError) as e:
            logger.debug(f"Copy test failed: {e}")
            return False
