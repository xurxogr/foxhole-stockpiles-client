# Foxhole Stockpiles Client

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Windows](https://img.shields.io/badge/platform-windows-blue.svg)](https://www.microsoft.com/windows)

A lightweight desktop client for capturing Foxhole stockpile screenshots and sending them to the [Foxhole Stockpiles Server](https://github.com/xurxogr/foxhole-stockpiles) for automated processing.

## Features

- 🖼️ **Automatic Screenshot Capture**: Capture Foxhole stockpile screenshots with customizable hotkeys
- 🎯 **Window Detection**: Automatically detects and focuses the Foxhole game window
- 🚀 **Server Integration**: Seamlessly sends screenshots to the processing server
- ⚙️ **Configurable**: Easy configuration through INI config file
- 🖥️ **Windows Native**: Built specifically for Windows with native window management
- 📦 **Standalone Executable**: Can be built as a single executable file

## Requirements

- **Python 3.12 or higher** (for running from source)
- **Windows 10 or 11**
- **Foxhole Stockpiles Server** running and accessible (see [foxhole-stockpiles](https://github.com/xurxogr/foxhole-stockpiles))

## Installation

### Option 1: Standalone Executable (Recommended for Users)

1. Download the latest `foxhole-client.exe` from [Releases](https://github.com/xurxogr/foxhole-stockpiles-client/releases)
2. Place it in a convenient location
3. Create a `config.ini` file in the same directory (see Configuration section)
4. Run `foxhole-client.exe`

### Option 2: From Source (For Developers)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/xurxogr/foxhole-stockpiles-client.git
   cd foxhole-stockpiles-client
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   # For regular use
   pip install -e .[windows]

   # For development
   pip install -e .[dev,windows]
   ```

4. **Install pre-commit hooks** (optional, for development):
   ```bash
   pre-commit install
   ```

## Configuration

The client is configured using a `config.ini` file located in the `foxhole_stockpiles/` directory (when running from source) or in the same directory as the executable.

### Basic Configuration

Create a `config.ini` file with the following settings:

```ini
[KEYBIND]
key = F9

[SERVER]
url = https://backend.com/fs/ocr/scan_image
token = your-bearer-token-here
```

### Configuration Options

#### [KEYBIND] Section

| Option | Description | Default |
|--------|-------------|---------|
| `key` | Hotkey to trigger screenshot capture | None (required) |

#### [SERVER] Section

| Option | Description | Default |
|--------|-------------|---------|
| `url` | URL of the Foxhole Stockpiles Server OCR endpoint | `https://backend.com/fs/ocr/scan_image` |
| `token` | Bearer token for server authentication | None (required) |

### Example Configuration

```ini
[KEYBIND]
key = F8

[SERVER]
url = https://foxhole-server.example.com/ocr/scan_image
token = my-secret-token-12345
```

## Usage

### Running the Client

**From executable**:
```bash
foxhole-client.exe
```

**From source**:
```bash
python -m foxhole_stockpiles.main
```

Or after installing in editable mode:
```bash
foxhole-client
```

### Using the Client

1. **Start the client**: Launch the application
2. **Play Foxhole**: The client runs in the background
3. **Open a stockpile**: View any stockpile in-game
4. **Press the hotkey**: Default is `F9` (configurable)
5. **Screenshot is captured**: Automatically sent to the server for processing
6. **View results**: Check the server logs/webhooks for processed data

### Hotkey Usage

- The client listens for the configured hotkey (default: `F9`)
- When pressed, it:
  1. Detects the Foxhole game window
  2. Brings it to focus (if needed)
  3. Captures a screenshot
  4. Sends it to the server for processing
  5. Shows a notification with the result

## Building Standalone Executable

To create a standalone executable:

```bash
# Build executable using the build script
build.cmd
```

Note: PyInstaller is included in the dev dependencies. The build script will package the application with all necessary files.

The executable will be created in the `dist/` directory.

## Project Structure

```
foxhole-stockpiles-client/
├── foxhole_stockpiles/
│   ├── core/              # Core utilities and configuration
│   ├── models/            # Data models
│   ├── ui/                # User interface components
│   ├── main.py            # Application entry point
│   └── config.ini         # Configuration file (gitignored)
├── pyproject.toml        # Project configuration
└── build.cmd             # Build script for executable
```

## Development

### Code Quality

The project uses several tools to maintain code quality:

```bash
# Run linter
ruff check foxhole_stockpiles/

# Run type checker
mypy foxhole_stockpiles/

# Format code
ruff format foxhole_stockpiles/

# Run all pre-commit hooks
pre-commit run --all-files
```

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality:

- Trailing whitespace removal
- End-of-file fixer
- YAML syntax checking
- Large file detection
- Debug statement detection
- Ruff linting and formatting
- MyPy type checking

## Troubleshooting

### Window Detection Issues

If the client can't detect the Foxhole window:

1. Check that Foxhole is running
2. The client automatically detects windows with "Foxhole" in the title
3. Ensure the game window title contains "Foxhole"

### Server Connection Issues

If the client can't connect to the server:

1. Verify the server is running and accessible
2. Check the `url` setting in the `[SERVER]` section of your `config.ini` file
3. Ensure the `token` setting matches the server configuration
4. Check firewall settings if using a remote server

### Hotkey Not Working

If the hotkey doesn't respond:

1. Try a different key (avoid keys used by other applications)
2. Run the client as administrator
3. Check for conflicting hotkey assignments

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Related Projects

- [Foxhole Stockpiles Server](https://github.com/xurxogr/foxhole-stockpiles) - The server component for processing screenshots
- [FIR (Foxhole Item Recognition)](https://github.com/GICodeWarrior/fir) - Original inspiration for the project

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues or have questions:

- Open an issue on [GitHub Issues](https://github.com/xurxogr/foxhole-stockpiles-client/issues)
- Check the [Troubleshooting](#troubleshooting) section
- Review the server documentation at [foxhole-stockpiles](https://github.com/xurxogr/foxhole-stockpiles)

## Credits

Created and maintained by Jorge García ([@xurxogr](https://github.com/xurxogr))

This client works in conjunction with the [Foxhole Stockpiles Server](https://github.com/xurxogr/foxhole-stockpiles) for complete stockpile processing functionality.
