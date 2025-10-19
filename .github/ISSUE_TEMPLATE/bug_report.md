---
name: Bug Report
about: Report a bug or unexpected behavior
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug Description

A clear and concise description of what the bug is.

## Steps to Reproduce

1. Launch client with configuration: `...`
2. Perform action: `...`
3. See error: `...`

## Expected Behavior

A clear description of what you expected to happen.

## Actual Behavior

What actually happened.

## Environment

**System Information:**
- OS: [e.g., Windows 11 22H2, Windows 10 21H2]
- Python Version: [e.g., 3.12.0] (if running from source)
- Installation Method: [standalone executable, pip install, source]
- Client Version: [e.g., 0.1.0]

**Configuration:**
```json
// Paste relevant configuration from config.json (redact sensitive tokens)
{
  "server_url": "...",
  "capture_hotkey": "...",
  "api_token": "REDACTED"
}
```

## Error Output

```
Paste full error message and stack trace here
```

## Screenshots

If applicable, add screenshots of:
- Error messages
- Client UI
- Game window state

## Additional Context

- Server version and status
- Log files (if available)
- Window detection issues (include window titles)
- Multi-monitor setup (if applicable)
- Any other relevant information

## Possible Solution

If you have ideas on what might be causing this or how to fix it, please share.
