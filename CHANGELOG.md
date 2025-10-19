# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2025-01-19

### Added
- Comprehensive README.md with installation, configuration, and usage documentation
- CONTRIBUTING.md with development workflow and code standards
- CHANGELOG.md following Keep a Changelog format

### Changed
- **Breaking**: Moved main.py to foxhole_stockpiles package directory for proper packaging
- Cleaned up pyproject.toml dependencies (removed unused packages)
- Updated build.cmd to reference new main.py location
- Default server URL changed to backend.com

### Removed
- requirements.txt (now using pyproject.toml)

### Fixed
- Documentation now correctly describes INI-based configuration
- Entry point configuration in pyproject.toml

## [0.5.0] - 2024-08-20

### Changed
- **Breaking**: Refactored settings to use Pydantic Settings for configuration management
- Moved options to "Settings" menu for better organization
- Increased ReadTimeout from 30 to 60 seconds
- Capture button now disabled by default if options are not set

### Added
- `set_keybind`: Define the keybind from settings menu
- `set_token`: Define the token from settings menu, shows profile URL if not set
- Text logging when options are saved

### Dependencies
- Updated h11 from 0.14.0 to 0.16.0

## [0.4.0] - 2024-07-20

### Added
- Logs textarea to display all events instead of toast notifications (better for fullscreen gaming)
- Capture button now changes colors when clicked for improved accessibility (colorblind support)

### Changed
- Internal variable refactoring for better code organization

### Fixed
- Reverted locale forcing fix as it didn't solve the user's issue

## [0.3.0] - 2024-04-02

### Added
- Toast notifications for user feedback
- Full URL configuration support in config file (removed base URL)

### Changed
- Removed library `mss` and updated dependencies
- Renamed function to avoid name conflict with `print`

### Fixed
- Global hotkey not working when BytesIO is used - moved BytesIO code to separate thread
- Screenshot capture thread timing issues

## [0.2.0] - 2024-03-10

### Added
- Batch file (`build.cmd`) to generate executable
- HTTP client integration to send screenshots to server
- `requirements.txt` with all needed libraries
- Method documentation

### Changed
- Improved response handling when sending images
- Hard-coded URL in GUI (still configurable via INI file)

## [0.1.0] - 2024-02-26

### Added
- Initial release
- Minimal UI with config.ini support
- Three configurable options: key, server, api_key
- Three main buttons: save options, change key (Escape to cancel), enable capture
- Screenshot capture functionality (stores to disk)
- Basic Foxhole window detection

[Unreleased]: https://github.com/xurxogr/foxhole-stockpiles-client/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/xurxogr/foxhole-stockpiles-client/compare/v0.5.0...v1.0.0
[0.5.0]: https://github.com/xurxogr/foxhole-stockpiles-client/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/xurxogr/foxhole-stockpiles-client/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/xurxogr/foxhole-stockpiles-client/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/xurxogr/foxhole-stockpiles-client/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/xurxogr/foxhole-stockpiles-client/releases/tag/v0.1.0
