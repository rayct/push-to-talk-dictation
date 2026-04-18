# Quick Start Guide - Push-to-Talk Dictation

## 5-Minute Setup

### 1. Install (2 minutes)
```bash
cd /home/ray/Repos/github.com/rayct/push-to-talk-dictation
./install.sh
```

Follow the prompts. It will:
- Create virtual environment
- Install dependencies
- Check system requirements
- Set up systemd service (optional)

### 2. Select Window (1 minute)
```bash
~/.local/bin/push-to-talk-dict --select-window
```

Pick your WezTerm or target window from the list.

### 3. Run (instant)
```bash
~/.local/bin/push-to-talk-dict
```

You should see:
```
[INFO] Daemon initialized successfully
[INFO] Starting mouse listener... (hold middle mouse button to dictate)
```

### 4. Test (1 minute)
1. Focus your target window (WezTerm, terminal, etc.)
2. **Hold the middle mouse button** (wheel click)
3. Say something like: "hello world"
4. Release the mouse button
5. Text should appear in your window

## Systemd Service (Auto-Start)

After installation, the daemon can auto-start on login:

```bash
# Enable auto-start
systemctl --user enable push-to-talk-dict.service

# Start it now
systemctl --user start push-to-talk-dict.service

# Check status
systemctl --user status push-to-talk-dict.service

# View logs
journalctl --user -u push-to-talk-dict.service -f
```

## Common Adjustments

### Slower/Faster Text Input
Edit `config.yaml`:
```yaml
injection:
  delay_ms: 50  # Increase to 100+ for slower input
```

### Smaller/Larger Whisper Model
```yaml
whisper_model: "base"  # Options: tiny, base, small, medium, large
```

Smaller = faster, larger = more accurate.

### Specific Microphone
List devices:
```bash
pactl list sources short
```

Find your microphone index, then edit `config.yaml`:
```yaml
audio:
  device_index: 2  # Your microphone index
```

## Troubleshooting

### "User not in audio group"
```bash
sudo usermod -aG audio $USER
# Logout and login again
```

### "xdotool not found"
```bash
sudo apt install xdotool
```

### "DISPLAY not set"
Make sure you're on X11 (not Wayland):
```bash
echo $DISPLAY  # Should show :0 or similar
```

### First run slow
Whisper model is downloading (~500MB). This only happens once.

### Text not appearing
- Make sure target window is selected: `~/.local/bin/push-to-talk-dict --select-window`
- Check window is still active: `~/.local/bin/push-to-talk-dict --list-windows`
- View logs: `journalctl --user -u push-to-talk-dict.service -f`

## Integration with Copilot CLI

Since this is designed for the GitHub Copilot CLI, voice input works great for:
- Asking questions naturally
- Dictating code descriptions
- Voice-driven debugging with the agent

Just hold middle mouse button in WezTerm while running copilot!

## Project Files

- `dictation_daemon.py` - Main coordinator
- `mouse_listener.py` - Middle button detection
- `audio_capture.py` - Microphone recording
- `transcriber.py` - Whisper transcription
- `x11_injector.py` - Text injection
- `window_manager.py` - Window selection
- `config.yaml` - Configuration
- `install.sh` - Automated setup
- `test_components.py` - Component tests

## Next Steps

1. **Test components**: `python3 test_components.py`
2. **View logs**: `tail -f ~/.local/share/push-to-talk-dict/dictation.log`
3. **Change settings**: Edit `config.yaml`
4. **Systemd troubleshooting**: `systemctl --user status push-to-talk-dict.service`

## Support

For more detailed info, see `README.md`.
