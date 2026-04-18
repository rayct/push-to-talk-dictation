# Push-to-Talk Dictation for Linux Mint + WezTerm

A clean, reproducible push-to-talk dictation system for Linux Mint using X11, with seamless integration into WezTerm CLI and GitHub Copilot CLI agent.

## Features

- **Local Speech-to-Text**: Uses OpenAI Whisper (no cloud API needed, works offline)
- **Push-to-Talk Control**: Hold middle mouse button to record
- **X11 Input Injection**: Reliable text injection using xdotool
- **Window Selection**: Manual window picker for precise control
- **Reproducible Setup**: Automated installation script
- **Systemd Integration**: Auto-start on login
- **Isolated Environment**: Clean Python virtual environment

## Requirements

- Linux Mint (or other X11-based Linux)
- Python 3.8+
- Microphone/audio input device
- User in `audio` group (for microphone access)

### System Dependencies

The installation script checks for and helps install:
- `xdotool` - X11 text injection
- `pactl` (PulseAudio) - Audio device management
- `wmctrl` - Window management
- `xwininfo` - Window information

## Quick Start

### 1. Install

```bash
cd /home/ray/Repos/github.com/rayct/push-to-talk-dictation
./install.sh
```

The script will:
- Create a Python virtual environment
- Install all dependencies
- Verify system requirements
- Create wrapper scripts and systemd service
- Optionally enable the service

### 2. Select Target Window

If using WezTerm CLI or GitHub Copilot CLI:

```bash
~/.local/bin/push-to-talk-dict --select-window
```

This launches an interactive picker. Select your target window and it's saved for future runs.

### 3. Start the Daemon

#### Option A: Manual (for testing)
```bash
~/.local/bin/push-to-talk-dict
```

Output will show when it's ready:
```
[INFO] Initializing dictation daemon...
[INFO] Target window: WezTerm
[INFO] Starting mouse listener... (hold middle mouse button to dictate)
```

#### Option B: Systemd Service (auto-start on login)
```bash
systemctl --user start push-to-talk-dict.service
systemctl --user status push-to-talk-dict.service
```

### 4. Use It

1. Hold the **middle mouse button** (wheel click)
2. Speak clearly into your microphone
3. Release the mouse button when done
4. Text is transcribed and automatically injected into the target window

## Configuration

Edit `config.yaml` to customize:

```yaml
# Whisper model: tiny, base, small, medium, large
whisper_model: "base"

# Audio settings
audio:
  sample_rate: 16000
  chunk_size: 1024
  channels: 1

# Injection delay (milliseconds between keypresses)
injection:
  delay_ms: 50

# Window persistence
window:
  persist_selection: true
  remember_by: "WM_NAME"

# Logging
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  file: "~/.local/share/push-to-talk-dict/dictation.log"
```

## Troubleshooting

### "Failed to start recording: OSError"
The user is not in the `audio` group. Fix with:
```bash
sudo usermod -aG audio $USER
# Then logout and log back in
```

### "xdotool not found"
Install xdotool:
```bash
sudo apt install xdotool
```

### "DISPLAY not set, X11 may not be running"
Ensure you're running on X11 (not Wayland):
```bash
echo $DISPLAY  # Should show something like :0
```

### Text not injecting into WezTerm
The daemon needs to know which window to target. Run:
```bash
~/.local/bin/push-to-talk-dict --select-window
```

Or check the saved window is still valid:
```bash
cat ~/.local/share/push-to-talk-dict/selected_window.json
```

### Microphone not working
List available audio devices:
```bash
pactl list sources short
```

Check which device index should be used in `config.yaml`:
```yaml
audio:
  device_index: 1  # Change to your microphone index
```

### Systemd service not starting
Check logs:
```bash
journalctl --user -u push-to-talk-dict.service -f
```

Common issues:
- `DISPLAY` not set: Try starting manually first, then troubleshoot environment
- Permission denied: Check file permissions in `~/.local/bin/push-to-talk-dict`

### First run takes a long time
Whisper model is being downloaded (~500MB for "base" model). This happens only on first run.

Subsequent runs will use the cached model.

## Commands

### Main daemon
```bash
~/.local/bin/push-to-talk-dict [--config CONFIG_FILE]
```

### Select target window interactively
```bash
~/.local/bin/push-to-talk-dict --select-window
```

### List available windows
```bash
~/.local/bin/push-to-talk-dict --list-windows
```

### Check system requirements
```bash
./sysinfo_check.py
```

### View daemon logs
```bash
# Manual daemon
journalctl --user -u push-to-talk-dict.service -f

# Or check log file
tail -f ~/.local/share/push-to-talk-dict/dictation.log
```

## Development

### Project Structure

```
push-to-talk-dictation/
├── install.sh              # Installation script
├── sysinfo_check.py        # System requirement checker
├── config.yaml             # Configuration file
├── requirements.txt        # Python dependencies
├── dictation_daemon.py     # Main daemon (coordinator)
├── mouse_listener.py       # Middle mouse button detection
├── audio_capture.py        # Microphone recording
├── transcriber.py          # Whisper transcription
├── x11_injector.py         # X11 text injection
├── window_manager.py       # Window selection and persistence
└── README.md               # This file
```

### Testing Components

Test individual components:

```bash
# Activate venv first
source venv/bin/activate

# Test system requirements
python3 sysinfo_check.py

# Test audio capture (manual)
python3 -c "from audio_capture import AudioCapture; ac = AudioCapture(); print(ac.list_devices())"

# Test X11 injection
python3 -c "from x11_injector import X11Injector; inj = X11Injector(); print(inj.list_windows())"

# Test window manager
python3 -c "from window_manager import WindowManager; wm = WindowManager(); wm.pick_window_interactive()"
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│         dictation_daemon.py (Main Coordinator)              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────┐   │
│  │   Mouse      │  │   Audio        │  │  Window      │   │
│  │   Listener   │→ │   Capture      │→ │  Manager     │   │
│  │              │  │                │  │              │   │
│  │ (pynput)     │  │ (PyAudio)      │  │ (xdotool)    │   │
│  └──────────────┘  └────────────────┘  └──────────────┘   │
│         │                  │                    │            │
│         └──────────────────┼────────────────────┘            │
│                            ↓                                 │
│                    ┌────────────────┐                       │
│                    │  Transcriber   │                       │
│                    │  (Whisper)     │                       │
│                    └────────────────┘                       │
│                            ↓                                 │
│                    ┌────────────────┐                       │
│                    │  X11 Injector  │                       │
│                    │  (xdotool)     │                       │
│                    └────────────────┘                       │
│                            ↓                                 │
│                    ┌────────────────┐                       │
│                    │  Target Window │                       │
│                    │  (WezTerm CLI) │                       │
│                    └────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

## Performance Notes

- **Whisper model size**: Trade-off between speed and accuracy
  - `tiny`: Fastest, lower accuracy (~0.5s per 10s audio)
  - `base`: Balanced (default, ~1s per 10s audio)
  - `small`: Better accuracy (~2s per 10s audio)
  - `medium`: High accuracy (~5s per 10s audio)
  - `large`: Best accuracy (~10s per 10s audio)

- **Audio delay**: Configurable in `config.yaml` via `injection.delay_ms`
  - Lower = faster input but may overwhelm terminal
  - Higher = slower input but more reliable
  - Default (50ms) works well for most terminals

## License

MIT License

## Contributing

Issues and PRs welcome!

## Support

For issues:
1. Check logs: `journalctl --user -u push-to-talk-dict.service -f`
2. Run system check: `./sysinfo_check.py`
3. Test manually: `~/.local/bin/push-to-talk-dict --select-window`
4. Check GitHub issues or documentation

## Useful Links

- [OpenAI Whisper](https://github.com/openai/whisper)
- [WezTerm](https://wezfurlong.org/wezterm/)
- [pynput](https://github.com/moses-palmer/pynput)
- [xdotool](https://www.semicomplete.com/projects/xdotool/)
