# Muxolotl - The Ultimate Media Converter

Muxolotl is a powerful, fast, and lightweight desktop application for converting audio and video files. Built with Python and Qt6, it leverages the full potential of FFmpeg to provide maximum flexibility and performance.

## Features

- **Full FFmpeg Support**: Convert to any audio or video format supported by your FFmpeg build.
- **Advanced Parameter Control**: Manually specify FFmpeg arguments for fine-grained control over the conversion process.
- **Modern & Responsive UI**: A clean and intuitive user interface that is easy to use.
- **High Performance**: Multithreaded processing ensures the UI never freezes, even during heavy conversions.
- **Standalone Application**: No need to install Python or any dependencies. Just download and run the executable.
- **Batch Processing**: Convert multiple files at once.

## Getting Started

### For Users

1.  Go to the [Releases](https://github.com/Politrees/muxolotl/releases) page.
2.  Download the latest `Muxolotl.zip` file.
3.  Unzip the archive and run `Muxolotl.exe`.

### For Developers

1.  **Prerequisites**:
    - Python 3.9+
    - FFmpeg (must be available in your system's PATH or placed in `src/assets/`)

2.  **Clone the repository**:
    ```bash
    git clone https://github.com/Politrees/muxolotl.git
    cd muxolotl
    ```

3.  **Create a virtual environment and install dependencies**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

4.  **Run the application**:
    ```bash
    python src/main.py
    ```

## Building from Source

To create a standalone `.exe` file, use the provided build script (on Windows):

```bash
build.bat
```

The final executable will be located in the `dist/` directory.

## License

This project is licensed under the MIT License - see the LICENSE file for details.