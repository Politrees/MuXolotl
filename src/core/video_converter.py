"""Video conversion module for MuXolotl"""

import os
from collections.abc import Callable
from pathlib import Path

from utils.logger import get_logger

from .ffmpeg_wrapper import FFmpegWrapper
from .format_detector import FormatDetector
from .gpu_detector import GPUDetector

logger = get_logger()


class VideoConverter:
    """Handle video file conversions with complete format and hardware encoding support"""

    # Format to FFmpeg format mapping (COMPLETE)
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
        "m2v": "mpeg2video",
        "ts": "mpegts",
        "m2ts": "mpegts",
        "mts": "mpegts",
        "mxf": "mxf",
        "3gp": "3gp",
        "3g2": "3g2",
        "asf": "asf",
        "wmv": "asf",
        "vob": "vob",
        "divx": "avi",
        "f4v": "flv",
        "rm": "rm",
        "rmvb": "rm",
        "swf": "swf",
        "wtv": "wtv",
        "yuv": "rawvideo",
    }

    # COMPLETE video codec compatibility: format -> [preferred, fallback1, fallback2, ...]
    FORMAT_VIDEO_CODEC_COMPATIBILITY = {
        "mp4": ["h264_nvenc", "h264_amf", "h264_qsv", "libx264", "hevc_nvenc", "hevc_amf", "hevc_qsv", "libx265", "mpeg4"],
        "m4v": ["h264_nvenc", "h264_amf", "h264_qsv", "libx264", "mpeg4"],
        "mov": ["h264_nvenc", "h264_amf", "h264_qsv", "libx264", "hevc_nvenc", "libx265", "prores_ks", "prores"],
        "avi": ["libx264", "mpeg4", "msmpeg4v3", "msmpeg4v2", "h264_nvenc", "h264_amf"],
        "mkv": ["h264_nvenc", "h264_amf", "h264_qsv", "libx264", "hevc_nvenc", "hevc_amf", "hevc_qsv", "libx265", "vp9_qsv", "libvpx-vp9", "av1_nvenc", "av1_amf", "libsvtav1"],
        "webm": ["vp9_qsv", "libvpx-vp9", "vp8", "libvpx", "av1_nvenc", "av1_amf", "libsvtav1"],
        "flv": ["libx264", "h264_nvenc", "h264_amf", "flv1", "h263"],
        "ogv": ["libtheora", "theora"],
        "mpeg": ["mpeg2video", "mpeg1video"],
        "mpg": ["mpeg2video", "mpeg1video"],
        "m2v": ["mpeg2video"],
        "ts": ["h264_nvenc", "h264_amf", "h264_qsv", "libx264", "hevc_nvenc", "hevc_amf", "libx265", "mpeg2video"],
        "m2ts": ["h264_nvenc", "h264_amf", "h264_qsv", "libx264", "hevc_nvenc", "hevc_amf", "libx265", "mpeg2video"],
        "mts": ["h264_nvenc", "h264_amf", "libx264", "mpeg2video"],
        "mxf": ["mpeg2video", "dnxhd", "prores_ks", "prores"],
        "3gp": ["libx264", "h264_nvenc", "h264_amf", "h263", "mpeg4"],
        "3g2": ["libx264", "h264_nvenc", "h264_amf", "h263", "mpeg4"],
        "wmv": ["wmv2", "wmv1", "msmpeg4v3"],
        "asf": ["wmv2", "wmv1", "msmpeg4v3"],
        "vob": ["mpeg2video"],
        "divx": ["mpeg4", "libx264"],
        "f4v": ["libx264", "h264_nvenc", "h264_amf"],
        "yuv": ["rawvideo"],
    }

    # COMPLETE audio codec compatibility for video formats
    FORMAT_AUDIO_CODEC_COMPATIBILITY = {
        "mp4": ["aac", "libfdk_aac", "ac3", "eac3", "mp3"],
        "m4v": ["aac", "libfdk_aac", "ac3"],
        "mov": ["aac", "libfdk_aac", "pcm_s16le", "pcm_s24le", "alac"],
        "avi": ["libmp3lame", "mp3", "ac3", "aac", "pcm_s16le"],
        "mkv": ["aac", "libopus", "opus", "ac3", "eac3", "dts", "flac", "libvorbis", "libmp3lame"],
        "webm": ["libopus", "opus", "libvorbis", "vorbis"],
        "flv": ["libmp3lame", "mp3", "aac"],
        "ogv": ["libvorbis", "vorbis", "libopus", "opus"],
        "mpeg": ["mp2", "mp3", "ac3"],
        "mpg": ["mp2", "mp3", "ac3"],
        "m2v": ["mp2", "ac3"],
        "ts": ["aac", "mp2", "ac3", "eac3"],
        "m2ts": ["aac", "ac3", "dts", "eac3"],
        "mts": ["aac", "ac3"],
        "mxf": ["pcm_s16le", "pcm_s24le"],
        "3gp": ["aac", "amr_nb"],
        "3g2": ["aac", "amr_nb"],
        "wmv": ["wmav2", "wmav1"],
        "asf": ["wmav2", "wmav1"],
        "vob": ["ac3", "mp2"],
        "divx": ["mp3", "ac3"],
        "f4v": ["aac"],
    }

    # Experimental codecs that need -strict -2
    EXPERIMENTAL_CODECS = {
        "vorbis",
        "opus",
        "aac",  # In some FFmpeg builds
        "theora",
    }

    def __init__(self):
        """Initialize video converter"""
        self.ffmpeg = FFmpegWrapper()
        self.detector = FormatDetector()

        # Detect GPU hardware
        self.gpu_detector = GPUDetector()

        self.available_video_codecs = self.detector.get_video_codecs()
        self.available_video_encoders = self.detector.get_video_encoders()
        self.available_audio_codecs = self.detector.get_audio_codecs()
        self.available_audio_encoders = self.detector.get_audio_encoders()
        self.available_hwaccels = self.detector.get_hwaccels()
        self.working_hwaccels = None

        # Combine encoders and codecs for checking
        self.all_video_available = self.available_video_codecs | self.available_video_encoders
        self.all_audio_available = self.available_audio_codecs | self.available_audio_encoders

        # Detect hardware encoders using GPU info
        logger.info(f"🎮 GPU Status: {self.gpu_detector.get_gpu_summary()}")
        logger.debug("Detecting hardware encoders...")
        self.hardware_encoders = self._detect_hardware_encoders()

        # Log summary
        logger.debug(f"Found {len(self.all_video_available)} video encoders")
        logger.debug(f"Found {len(self.all_audio_available)} audio encoders")

    def _detect_hardware_encoders(self) -> dict[str, str | None]:
        """Detect available hardware encoders using GPU detection

        Returns:
            Dictionary mapping codec types to best available encoder

        """
        encoders = {
            "h264": None,
            "hevc": None,
            "vp9": None,
            "av1": None,
        }

        # Get recommended encoders based on detected GPU
        recommended = self.gpu_detector.get_recommended_encoders()

        # Test H.264 encoders in priority order
        for encoder in recommended["h264"]:
            if encoder in self.all_video_available:
                if self.detector.test_encoder(encoder, self.gpu_detector):
                    encoders["h264"] = encoder
                    if any(hw in encoder for hw in ["nvenc", "qsv", "amf", "videotoolbox"]):
                        logger.info(f"✅ Hardware H.264 encoder: {encoder}")
                    else:
                        logger.debug(f"Using H.264 encoder: {encoder}")
                    break
                else:
                    logger.debug(f"Encoder {encoder} available but failed test")

        # Test HEVC encoders
        for encoder in recommended["hevc"]:
            if encoder in self.all_video_available:
                if self.detector.test_encoder(encoder, self.gpu_detector):
                    encoders["hevc"] = encoder
                    if any(hw in encoder for hw in ["nvenc", "qsv", "amf", "videotoolbox"]):
                        logger.info(f"✅ Hardware HEVC encoder: {encoder}")
                    break

        # Test VP9 encoders
        for encoder in recommended["vp9"]:
            if encoder in self.all_video_available:
                if self.detector.test_encoder(encoder, self.gpu_detector):
                    encoders["vp9"] = encoder
                    break

        # Test AV1 encoders
        for encoder in recommended["av1"]:
            if encoder in self.all_video_available:
                if self.detector.test_encoder(encoder, self.gpu_detector):
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
            elif "amf" in encoder:
                info.append("H.264: AMD GPU (Fast)")
            elif "qsv" in encoder:
                info.append("H.264: Intel Quick Sync (Fast)")
            elif "videotoolbox" in encoder:
                info.append("H.264: Apple Hardware (Fast)")
            else:
                info.append("H.264: CPU (Slow)")

        if self.hardware_encoders["hevc"]:
            encoder = str(self.hardware_encoders["hevc"])
            if any(hw in encoder for hw in ["nvenc", "qsv", "amf"]):
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
            elif video_codec == "copy":
                # Validate if copy is possible
                if not self._can_copy_video(input_file, output_format):
                    logger.warning(f"Cannot safely copy video codec for {output_format}, using auto-selection")
                    video_codec = self._get_best_video_codec(output_format)

            if audio_codec == "auto":
                audio_codec = self._get_best_audio_codec(output_format)

            # Try conversion with automatic fallback
            return self._convert_with_fallback(
                input_file=input_file,
                output_file=output_file,
                output_format=output_format,
                video_codec=video_codec,
                audio_codec=audio_codec,
                video_bitrate=video_bitrate,
                audio_bitrate=audio_bitrate,
                crf=crf,
                preset=preset,
                resolution=resolution,
                fps=fps,
                hwaccel=hwaccel,
                preserve_metadata=preserve_metadata,
                tune=tune,
                progress_callback=progress_callback,
            )

        except (OSError, ValueError) as e:
            logger.error(f"Video conversion error: {e}", exc_info=True)
            return None

    def _convert_with_fallback(
        self,
        input_file: str,
        output_file: str,
        output_format: str,
        video_codec: str,
        audio_codec: str,
        video_bitrate: str,
        audio_bitrate: str,
        crf: int | None,
        preset: str,
        resolution: str | None,
        fps: int | None,
        hwaccel: str,
        preserve_metadata: bool,
        tune: str | None,
        progress_callback: Callable[[float, str], None] | None,
    ) -> str | None:
        """Convert with automatic fallback if encoders fail"""

        # Get compatible video codecs for this format
        compatible_video = self.FORMAT_VIDEO_CODEC_COMPATIBILITY.get(output_format, [video_codec])
        compatible_audio = self.FORMAT_AUDIO_CODEC_COMPATIBILITY.get(output_format, [audio_codec])

        # Build list of video codecs to try
        video_codecs_to_try = []
        if video_codec in compatible_video:
            video_codecs_to_try.append(video_codec)

        for codec in compatible_video:
            if codec in self.all_video_available and codec not in video_codecs_to_try:
                video_codecs_to_try.append(codec)

        # If no available codecs, try first compatible anyway
        if not video_codecs_to_try and compatible_video:
            video_codecs_to_try.append(compatible_video[0])

        # Build list of audio codecs to try
        audio_codecs_to_try = []
        if audio_codec in compatible_audio:
            audio_codecs_to_try.append(audio_codec)

        for codec in compatible_audio:
            if codec in self.all_audio_available and codec not in audio_codecs_to_try:
                audio_codecs_to_try.append(codec)

        if not audio_codecs_to_try and compatible_audio:
            audio_codecs_to_try.append(compatible_audio[0])

        # Try each video codec
        for v_attempt, current_video_codec in enumerate(video_codecs_to_try, 1):
            # Try each audio codec with current video codec
            for a_attempt, current_audio_codec in enumerate(audio_codecs_to_try, 1):
                attempt = v_attempt if a_attempt == 1 else f"{v_attempt}.{a_attempt}"

                if v_attempt > 1 or a_attempt > 1:
                    logger.warning(f"Trying fallback: video={current_video_codec}, audio={current_audio_codec} (attempt {attempt})")
                    if progress_callback:
                        progress_callback(0.05, f"⚠️ Retrying with different codecs...")

                # Determine hardware acceleration
                actual_hwaccel = None
                if hwaccel == "auto":
                    actual_hwaccel = self._get_best_hwaccel()
                elif hwaccel != "none":
                    if self._verify_hwaccel(hwaccel):
                        actual_hwaccel = hwaccel

                # Build parameters
                params = {
                    "video_codec": current_video_codec,
                    "audio_codec": current_audio_codec,
                    "video_bitrate": video_bitrate if video_bitrate != "auto" else None,
                    "audio_bitrate": audio_bitrate,
                    "preset": preset,
                    "hwaccel": actual_hwaccel,
                    "preserve_metadata": preserve_metadata,
                    "format": self.FORMAT_MAPPING.get(output_format, output_format),
                    "tune": tune,
                }

                # Add input codec info for bitstream filters
                if current_video_codec == "copy" or current_audio_codec == "copy":
                    info = self.ffmpeg.get_file_info(input_file)
                    if info and "streams" in info:
                        for stream in info["streams"]:
                            if stream.get("codec_type") == "video" and current_video_codec == "copy":
                                params["input_video_codec"] = stream.get("codec_name", "")
                            if stream.get("codec_type") == "audio" and current_audio_codec == "copy":
                                params["input_audio_codec"] = stream.get("codec_name", "")

                # Add CRF for quality-based encoding
                if crf is not None and current_video_codec != "copy":
                    if any(hw in current_video_codec for hw in ["nvenc", "qsv", "amf"]):
                        params["cq"] = 51 - crf if "nvenc" in current_video_codec else crf
                    else:
                        params["crf"] = crf

                # Add custom parameters
                custom_params = []

                if resolution:
                    custom_params.extend(["-s", resolution])

                if fps:
                    custom_params.extend(["-r", str(fps)])

                # Format-specific optimizations
                if output_format in ["mp4", "m4v", "mov"]:
                    custom_params.extend(["-movflags", "+faststart"])

                # Experimental codecs
                if current_audio_codec in self.EXPERIMENTAL_CODECS:
                    custom_params.extend(["-strict", "-2"])
                    logger.debug(f"Added -strict -2 for experimental audio codec {current_audio_codec}")

                if custom_params:
                    params["custom_params"] = custom_params

                # Build and execute command
                command = self.ffmpeg.build_command(input_file, output_file, params)

                if progress_callback and v_attempt == 1 and a_attempt == 1:
                    progress_callback(0.1, "Starting conversion...")

                success = self.ffmpeg.execute(command, progress_callback)

                if success and os.path.exists(output_file):
                    if v_attempt > 1 or a_attempt > 1:
                        logger.info(f"✅ Conversion succeeded with fallback codecs: video={current_video_codec}, audio={current_audio_codec}")
                    else:
                        logger.info(f"✅ Successfully converted: {output_file}")
                    if progress_callback:
                        progress_callback(1.0, "Completed!")
                    return output_file

                # Clean up failed output
                if os.path.exists(output_file):
                    try:
                        os.remove(output_file)
                    except OSError:
                        pass

        logger.error(f"❌ All codec combinations failed for: {input_file}")
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

            # Add experimental flag if needed
            if audio_codec in self.EXPERIMENTAL_CODECS:
                params["custom_params"] = ["-strict", "-2"]

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

        except (OSError, ImportError) as e:
            logger.error(f"Audio extraction error: {e}", exc_info=True)
            return None

    def _can_copy_video(self, input_file: str, output_format: str) -> bool:
        """Check if video codec can be copied without re-encoding"""
        can_copy, codec_name = self.ffmpeg.can_copy_codec(input_file, output_format, "video")

        if not can_copy:
            logger.debug(f"Video copy not possible: {codec_name} → {output_format}")

        return can_copy

    def _verify_hwaccel(self, hwaccel: str) -> bool:
        """Verify if a hardware acceleration method works"""
        if self.working_hwaccels is None:
            self.working_hwaccels = self.detector.get_working_hwaccels()

        return hwaccel in self.working_hwaccels

    def _get_best_video_codec(self, fmt: str) -> str:
        """Get best available video codec for format (prefer hardware)"""
        compatible = self.FORMAT_VIDEO_CODEC_COMPATIBILITY.get(fmt, [])

        if not compatible:
            logger.warning(f"No codec mapping for format {fmt}, using libx264")
            return "libx264"

        # Find first available compatible codec
        for codec in compatible:
            if codec in self.all_video_available:
                logger.debug(f"Selected video codec {codec} for format {fmt}")
                return codec

        # If no available codec, return first compatible
        logger.warning(f"No available video encoder for {fmt}, will try {compatible[0]}")
        return compatible[0]

    def _get_best_audio_codec(self, fmt: str) -> str:
        """Get best available audio codec for format"""
        compatible = self.FORMAT_AUDIO_CODEC_COMPATIBILITY.get(fmt, [])

        if not compatible:
            logger.warning(f"No audio codec mapping for format {fmt}, using aac")
            return "aac"

        # Find first available compatible codec
        for codec in compatible:
            if codec in self.all_audio_available:
                logger.debug(f"Selected audio codec {codec} for format {fmt}")
                return codec

        # If no available codec, return first compatible
        logger.warning(f"No available audio encoder for {fmt}, will try {compatible[0]}")
        return compatible[0]

    def _get_best_hwaccel(self) -> str | None:
        """Get best available hardware acceleration for decoding"""
        # First, try GPU detector recommendation
        recommended = self.gpu_detector.get_recommended_hwaccel()

        if recommended:
            if self.working_hwaccels is None:
                self.working_hwaccels = self.detector.get_working_hwaccels()

            if recommended in self.working_hwaccels:
                logger.debug(f"Using recommended hardware acceleration: {recommended}")
                return recommended

        # Fallback to priority order
        if self.working_hwaccels is None:
            self.working_hwaccels = self.detector.get_working_hwaccels()

        priority = ["cuda", "d3d11va", "dxva2", "qsv", "videotoolbox", "vaapi"]

        for hwaccel in priority:
            if hwaccel in self.working_hwaccels:
                logger.debug(f"Using hardware acceleration: {hwaccel}")
                return hwaccel

        return None

    def get_supported_formats(self) -> list:
        """Get list of supported video formats"""
        available = self.detector.get_video_formats()

        # Filter formats that have at least one encoder
        supported = []
        for fmt in self.FORMAT_MAPPING:
            if self.FORMAT_MAPPING[fmt] in available or fmt in available:
                # Check if we have at least one video encoder
                compatible = self.FORMAT_VIDEO_CODEC_COMPATIBILITY.get(fmt, [])
                has_encoder = any(codec in self.all_video_available for codec in compatible)

                if has_encoder:
                    supported.append(fmt)

        return sorted(supported)

    def get_file_info(self, file_path: str) -> dict[str, any]:
        """Get video file information"""
        return self.ffmpeg.get_file_info(file_path)
