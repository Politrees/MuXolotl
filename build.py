"""Build script for MuXolotl
Creates standalone executable using PyInstaller
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def clean_build_dirs():
    """Clean previous build directories"""
    dirs_to_clean = ["build", "dist", "__pycache__"]
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name}...")
            shutil.rmtree(dir_name)

    # Remove spec file
    spec_file = "MuXolotl.spec"
    if os.path.exists(spec_file):
        os.remove(spec_file)


def check_dependencies():
    """Check if required dependencies are installed"""
    required = ["customtkinter", "Pillow", "PyInstaller"]
    missing = []

    for package in required:
        try:
            __import__(package.lower().replace("-", "_"))
        except ImportError:
            missing.append(package)

    if missing:
        print(f"Missing dependencies: {', '.join(missing)}")
        print("Installing missing dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)


def download_ffmpeg():
    """Download FFmpeg (you can customize this to automatically download FFmpeg)
    For now, it just checks if FFmpeg is available
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
        )
        if result.returncode == 0:
            print("✓ FFmpeg found")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    print("⚠ FFmpeg not found in PATH")
    print("Please install FFmpeg manually or place ffmpeg.exe in the project directory")
    return False


def create_icon():
    """Create application icon if not exists"""
    icon_path = Path("assets/icon.ico")

    if not icon_path.exists():
        print("Creating default icon...")
        os.makedirs("assets", exist_ok=True)

        # Create a simple icon using PIL
        try:
            img = Image.new("RGB", (256, 256), color="#1F6AA5")
            draw = ImageDraw.Draw(img)

            # Draw simple text
            try:
                font = ImageFont.truetype("arial.ttf", 80)
            except OSError:
                font = ImageFont.load_default()

            text = "MX"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            position = ((256 - text_width) // 2, (256 - text_height) // 2)
            draw.text(position, text, fill="white", font=font)

            img.save(icon_path)
            print(f"✓ Icon created at {icon_path}")
        except OSError as e:
            print(f"Could not create icon: {e}")


def build_executable():
    """Build executable using PyInstaller"""
    system = platform.system()

    # Base PyInstaller command
    cmd = [
        "pyinstaller",
        "--name=MuXolotl",
        "--onefile",
        "--windowed",
        "--clean",
    ]

    # Add icon
    icon_path = Path("assets/icon.ico")
    if icon_path.exists():
        if system in ("Windows", "Darwin"):
            cmd.append("--icon=assets/icon.ico")

    # Add data files
    cmd.extend(
        [
            "--add-data=src:src",
            "--add-data=assets:assets",  # Add this line to include assets folder
        ],
    )

    # Hidden imports
    hidden_imports = [
        "customtkinter",
        "PIL",
        "PIL._tkinter_finder",
    ]

    for imp in hidden_imports:
        cmd.append(f"--hidden-import={imp}")

    # Entry point
    cmd.append("main.py")

    print("Building executable...")
    print(f"Command: {' '.join(cmd)}")

    try:
        subprocess.check_call(cmd)
        print("\n✓ Build successful!")

        # Show output location
        if system == "Windows":
            exe_path = Path("dist/MuXolotl.exe")
        elif system == "Darwin":
            exe_path = Path("dist/MuXolotl.app")
        else:
            exe_path = Path("dist/MuXolotl")

        if exe_path.exists():
            print(f"\n📦 Executable location: {exe_path.absolute()}")
            print(f"📊 File size: {exe_path.stat().st_size / (1024 * 1024):.1f} MB")

        return True

    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed: {e}")
        return False


def create_readme_dist():
    """Create README for distribution"""
    readme_content = """
# MuXolotl - Universal Media Converter

## Quick Start

1. Run MuXolotl executable
2. Select your media files
3. Choose output format and settings
4. Click Convert!

## Requirements

- FFmpeg must be installed and available in system PATH
- Or place ffmpeg.exe in the same directory as MuXolotl

## Download FFmpeg

Windows: https://www.gyan.dev/ffmpeg/builds/
macOS: `brew install ffmpeg`
Linux: `sudo apt install ffmpeg`

## Support

For issues and feature requests:
https://github.com/Politrees/MuXolotl/issues

## License

MIT License - See LICENSE file
"""

    dist_dir = Path("dist")
    if dist_dir.exists():
        with open(dist_dir / "README.txt", "w", encoding="utf-8") as f:
            f.write(readme_content.strip())
        print("✓ Distribution README created")


def main():
    """Main build process"""
    print("=" * 60)
    print("MuXolotl Build Script")
    print("=" * 60)
    print()

    # Step 1: Clean
    print("[1/6] Cleaning previous builds...")
    clean_build_dirs()
    print()

    # Step 2: Check dependencies
    print("[2/6] Checking dependencies...")
    check_dependencies()
    print()

    # Step 3: Check FFmpeg
    print("[3/6] Checking FFmpeg...")
    download_ffmpeg()
    print()

    # Step 4: Create icon
    print("[4/6] Creating application icon...")
    create_icon()
    print()

    # Step 5: Build
    print("[5/6] Building executable...")
    if not build_executable():
        sys.exit(1)
    print()

    # Step 6: Create distribution README
    print("[6/6] Creating distribution files...")
    create_readme_dist()
    print()

    print("=" * 60)
    print("✓ Build process completed successfully!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Test the executable in dist/ directory")
    print("2. Ensure FFmpeg is available")
    print("3. Create GitHub release with the executable")


if __name__ == "__main__":
    main()
