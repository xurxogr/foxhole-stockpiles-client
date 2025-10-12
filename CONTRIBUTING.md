# Contributing to Foxhole Stockpiles Client

Thank you for your interest in contributing to Foxhole Stockpiles Client! This document provides guidelines for contributing to the project.

## Ways to Contribute

- **Report Bugs**: Open an issue describing the problem, steps to reproduce, and your environment
- **Suggest Features**: Open an issue describing the feature and its use case
- **Submit Pull Requests**: Fix bugs, add features, or improve documentation
- **Improve Documentation**: Help make the docs clearer and more comprehensive

## Reporting Bugs

When reporting bugs, please include:

1. **Environment Information**:
   - Python version (`python --version`)
   - Operating system (Windows version)
   - Installation method (pip, standalone executable, etc.)
   - Relevant package versions

2. **Steps to Reproduce**:
   - Exact actions that trigger the issue
   - Screenshots of the client UI (if applicable)
   - Expected vs actual behavior

3. **Error Output**:
   - Full error messages and stack traces
   - Log output (check logs directory if available)

## Submitting Pull Requests

### Development Setup

1. **Fork and clone the repository**:
   ```bash
   git clone https://github.com/your-username/foxhole-stockpiles-client.git
   cd foxhole-stockpiles-client
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   ```

3. **Install development dependencies**:
   ```bash
   pip install -e .[dev,windows]
   ```

4. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

### Code Quality Standards

This project follows strict code quality guidelines:

- **Linting**: Code must pass `ruff check`
- **Type Checking**: Code must pass `mypy` type checks
- **Formatting**: Code is formatted with `ruff format`
- **Docstrings**: Use Google-style docstrings for all public functions/classes

### Running Quality Checks

```bash
# Run linter
ruff check foxhole_stockpiles/

# Run type checker
mypy foxhole_stockpiles/

# Run all pre-commit hooks
pre-commit run --all-files
```

### Pull Request Process

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Follow the existing code style
   - Update documentation as needed
   - Ensure code passes quality checks

3. **Ensure all checks pass**:
   ```bash
   ruff check foxhole_stockpiles/
   mypy foxhole_stockpiles/
   pre-commit run --all-files
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Brief description of changes"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request**:
   - Provide a clear description of the changes
   - Reference any related issues
   - Ensure CI checks pass

### Commit Message Guidelines

- Use clear, descriptive commit messages
- Start with a verb (Add, Fix, Update, Remove, etc.)
- Keep the first line under 72 characters
- Reference issue numbers when applicable

Examples:
```
Add keyboard shortcut for quick capture
Fix window detection for multi-monitor setups
Update UI layout for better usability
```

## Code Style Guidelines

- **Type Hints**: All functions must have type hints
- **Pydantic Models**: Use Pydantic for data validation and settings
- **Error Handling**: Raise specific exceptions with clear error messages
- **Logging**: Use Python's logging module for debugging
- **Code Style**: Follow existing patterns in the codebase

## Documentation Guidelines

- Update README.md for user-facing changes
- Add docstrings to all public functions and classes
- Include examples in docstrings when helpful

## Windows-Specific Considerations

This project is primarily designed for Windows:

- Use `pathlib.Path` for cross-platform path handling
- Test on Windows 10 and Windows 11
- Consider multi-monitor setups when working with window detection
- Handle high-DPI displays appropriately

## Building Executable

To build a standalone executable:

```bash
# Using the build script (Windows)
build.cmd
```

The executable will be created in the `dist/` directory.

## License

By contributing to Foxhole Stockpiles Client, you agree that your contributions will be licensed under the MIT License.
