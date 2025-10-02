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
                check=False, stdout=subprocess.PIPE,
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
                        cmd.extend(["-qp_i", str(params["cq"]),
                                   "-qp_p", str(params["cq"])])

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

        except (subprocess.SubprocessError, OSError, IOError) as e:
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
                ["ffprobe", "-hide_banner", "-v", "quiet",
                 "-print_format", "json", "-show_format",
                 "-show_streams", file_path],
                check=False, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                return json.loads(result.stdout)

        except (subprocess.SubprocessError, OSError, json.JSONDecodeError) as e:
            logger.error(f"Failed to get file info: {e}")

        return {}
