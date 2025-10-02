"""GPU detection and hardware acceleration for MuXolotl"""

import platform
import subprocess

from utils.logger import get_logger

logger = get_logger()


class GPUDetector:
    """Detect available GPUs and hardware acceleration capabilities"""

    def __init__(self):
        """Initialize GPU detector"""
        self.system = platform.system()
        self.gpu_info = None
        self._detect_gpu()

    def _detect_gpu(self):
        """Detect available GPUs in the system"""
        self.gpu_info = {
            "nvidia": False,
            "amd": False,
            "intel": False,
            "apple": False,
            "nvidia_model": None,
            "amd_model": None,
            "intel_model": None,
        }

        if self.system == "Windows":
            self._detect_gpu_windows()
        elif self.system == "Darwin":  # macOS
            self._detect_gpu_macos()
        elif self.system == "Linux":
            self._detect_gpu_linux()

        # Log detected GPUs
        detected = []
        if self.gpu_info["nvidia"]:
            detected.append(f"NVIDIA ({self.gpu_info['nvidia_model'] or 'Unknown'})")
        if self.gpu_info["amd"]:
            detected.append(f"AMD ({self.gpu_info['amd_model'] or 'Unknown'})")
        if self.gpu_info["intel"]:
            detected.append(f"Intel ({self.gpu_info['intel_model'] or 'Unknown'})")
        if self.gpu_info["apple"]:
            detected.append("Apple Silicon")

        if detected:
            logger.info(f"🎮 Detected GPUs: {', '.join(detected)}")
        else:
            logger.warning("⚠️ No discrete GPU detected")

    def _detect_gpu_windows(self):
        """Detect GPU on Windows using WMIC"""
        try:
            # Try wmic first (faster)
            result = subprocess.run(
                ["wmic", "path", "win32_VideoController", "get", "name"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )

            output = result.stdout.lower()

            if "nvidia" in output or "geforce" in output or "quadro" in output or "rtx" in output:
                self.gpu_info["nvidia"] = True
                # Extract model
                for line in result.stdout.splitlines():
                    if any(x in line.lower() for x in ["nvidia", "geforce", "rtx", "gtx"]):
                        self.gpu_info["nvidia_model"] = line.strip()
                        break

            if "amd" in output or "radeon" in output or "rx " in output:
                self.gpu_info["amd"] = True
                for line in result.stdout.splitlines():
                    if any(x in line.lower() for x in ["amd", "radeon", "rx "]):
                        self.gpu_info["amd_model"] = line.strip()
                        break

            if ("intel" in output and "hd" in output) or "iris" in output or "arc" in output:
                self.gpu_info["intel"] = True
                for line in result.stdout.splitlines():
                    if "intel" in line.lower():
                        self.gpu_info["intel_model"] = line.strip()
                        break

        except (subprocess.SubprocessError, OSError, subprocess.TimeoutExpired) as e:
            logger.debug(f"WMIC detection failed: {e}")

            # Fallback to DirectX diagnostic
            try:
                result = subprocess.run(
                    ["dxdiag", "/t", "dxdiag_output.txt"],
                    check=False,
                    capture_output=True,
                    timeout=10,
                )
                # Parse dxdiag output if needed
            except (subprocess.SubprocessError, OSError):
                pass

    def _detect_gpu_linux(self):
        """Detect GPU on Linux"""
        try:
            # Try lspci
            result = subprocess.run(
                ["lspci"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )

            output = result.stdout.lower()

            if "nvidia" in output:
                self.gpu_info["nvidia"] = True
                for line in result.stdout.splitlines():
                    if "nvidia" in line.lower() and "vga" in line.lower():
                        self.gpu_info["nvidia_model"] = line.split(":")[-1].strip()
                        break

            if "amd" in output or "radeon" in output:
                self.gpu_info["amd"] = True
                for line in result.stdout.splitlines():
                    if ("amd" in line.lower() or "radeon" in line.lower()) and "vga" in line.lower():
                        self.gpu_info["amd_model"] = line.split(":")[-1].strip()
                        break

            if "intel" in output:
                self.gpu_info["intel"] = True

        except (subprocess.SubprocessError, OSError, subprocess.TimeoutExpired):
            pass

    def _detect_gpu_macos(self):
        """Detect GPU on macOS"""
        try:
            result = subprocess.run(
                ["system_profiler", "SPDisplaysDataType"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )

            output = result.stdout.lower()

            if "amd" in output or "radeon" in output:
                self.gpu_info["amd"] = True
            if "nvidia" in output:
                self.gpu_info["nvidia"] = True
            if "intel" in output:
                self.gpu_info["intel"] = True
            if "apple" in output or "m1" in output or "m2" in output or "m3" in output:
                self.gpu_info["apple"] = True

        except (subprocess.SubprocessError, OSError, subprocess.TimeoutExpired):
            pass

    def get_recommended_encoders(self) -> dict[str, list[str]]:
        """Get recommended encoders based on detected hardware

        Returns:
            Dictionary with encoder priorities for each codec type

        """
        encoders = {
            "h264": [],
            "hevc": [],
            "vp9": [],
            "av1": [],
        }

        # H.264 encoders based on detected GPU
        if self.gpu_info["nvidia"]:
            encoders["h264"].extend(["h264_nvenc"])
        if self.gpu_info["amd"]:
            encoders["h264"].extend(["h264_amf"])
        if self.gpu_info["intel"]:
            encoders["h264"].extend(["h264_qsv"])
        if self.gpu_info["apple"]:
            encoders["h264"].extend(["h264_videotoolbox"])

        # Always add software fallback
        encoders["h264"].append("libx264")

        # HEVC encoders
        if self.gpu_info["nvidia"]:
            encoders["hevc"].extend(["hevc_nvenc"])
        if self.gpu_info["amd"]:
            encoders["hevc"].extend(["hevc_amf"])
        if self.gpu_info["intel"]:
            encoders["hevc"].extend(["hevc_qsv"])
        if self.gpu_info["apple"]:
            encoders["hevc"].extend(["hevc_videotoolbox"])

        encoders["hevc"].append("libx265")

        # VP9
        if self.gpu_info["intel"]:
            encoders["vp9"].append("vp9_qsv")
        encoders["vp9"].append("libvpx-vp9")

        # AV1
        if self.gpu_info["nvidia"]:
            encoders["av1"].append("av1_nvenc")
        if self.gpu_info["intel"]:
            encoders["av1"].append("av1_qsv")
        if self.gpu_info["amd"]:
            encoders["av1"].append("av1_amf")

        encoders["av1"].extend(["libsvtav1", "libaom-av1"])

        return encoders

    def get_recommended_hwaccel(self) -> str | None:
        """Get recommended hardware acceleration for decoding

        Returns:
            Hardware acceleration method or None

        """
        if self.gpu_info["nvidia"]:
            return "cuda"
        if self.gpu_info["intel"]:
            return "qsv"
        if self.gpu_info["amd"]:
            if self.system == "Windows":
                return "d3d11va"  # Better for AMD on Windows
            return "vaapi"
        if self.gpu_info["apple"]:
            return "videotoolbox"

        return None

    def has_hardware_encoding(self) -> bool:
        """Check if any hardware encoding is available"""
        return any(
            [
                self.gpu_info["nvidia"],
                self.gpu_info["amd"],
                self.gpu_info["intel"],
                self.gpu_info["apple"],
            ]
        )

    def get_gpu_summary(self) -> str:
        """Get human-readable GPU summary"""
        parts = []

        if self.gpu_info["nvidia"]:
            model = self.gpu_info["nvidia_model"] or "GPU"
            parts.append(f"🟢 GPU: {model}")

        if self.gpu_info["amd"]:
            model = self.gpu_info["amd_model"] or "GPU"
            parts.append(f"🔴 GPU: {model}")

        if self.gpu_info["intel"]:
            model = self.gpu_info["intel_model"] or "iGPU"
            parts.append(f"🔵 GPU: {model}")

        if self.gpu_info["apple"]:
            parts.append("🍎 Apple Silicon")

        if not parts:
            return "💻 CPU Only"

        return " | ".join(parts)
