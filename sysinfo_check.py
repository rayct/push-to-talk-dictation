#!/usr/bin/env python3
"""
System information and requirement checker.
Verifies that the system has all necessary components for push-to-talk dictation.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


class SystemChecker:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.checks_passed = 0
        self.checks_failed = 0

    def check(self, name: str, condition: bool, error_msg: str = "", warning: bool = False):
        """Record a check result."""
        if condition:
            self.checks_passed += 1
            print(f"✓ {name}")
        else:
            self.checks_failed += 1
            if warning:
                self.warnings.append(error_msg or name)
                print(f"⚠ {name} (warning)")
            else:
                self.errors.append(error_msg or name)
                print(f"✗ {name}")

    def run_checks(self):
        """Run all system checks."""
        print("\n=== System Requirements Check ===\n")

        # Python version
        python_version = sys.version_info
        self.check(
            "Python 3.8+",
            python_version >= (3, 8),
            f"Python {python_version.major}.{python_version.minor} found, need 3.8+"
        )

        # X11 detection
        display = os.environ.get('DISPLAY')
        self.check("X11 available", display is not None, "DISPLAY not set, X11 may not be running")

        # Required system packages
        required_packages = {
            'xdotool': 'X11 text injection',
            'pactl': 'PulseAudio control (audio)',
            'xwininfo': 'Window information'
        }

        for pkg, desc in required_packages.items():
            has_pkg = shutil.which(pkg) is not None
            self.check(f"{pkg} installed ({desc})", has_pkg, 
                      f"Missing {pkg}: {desc}. Install with: sudo apt install {pkg.replace('pactl', 'pulseaudio')}")

        # Audio device check
        try:
            result = subprocess.run(['pactl', 'list', 'sources'], 
                                  capture_output=True, timeout=5, text=True)
            has_audio = result.returncode == 0 and 'alsa' in result.stdout.lower()
            self.check("Audio device found", has_audio, 
                      "No audio device detected. Check hardware and drivers.")
        except Exception as e:
            self.check("Audio device check", False, f"Audio check failed: {e}")

        # User in audio group
        try:
            result = subprocess.run(['groups'], capture_output=True, text=True)
            in_audio = 'audio' in result.stdout
            self.check("User in 'audio' group", in_audio,
                      "User not in audio group. Run: sudo usermod -aG audio $USER (requires logout/login)")
        except Exception:
            self.check("User in 'audio' group", False, "Could not check group membership")

        # Directory structure
        dirs_ok = True
        for d in ['models', '.config', '.local/share/push-to-talk-dict']:
            dir_path = Path.home() / f'.{d}' if '/' in d else Path(d)
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"Warning: Could not create {d}: {e}")
                dirs_ok = False
        self.check("User directories writable", dirs_ok)

        print(f"\n=== Summary ===")
        print(f"Passed: {self.checks_passed}")
        print(f"Failed: {self.checks_failed}")
        if self.warnings:
            print(f"Warnings: {len(self.warnings)}")

        return len(self.errors) == 0


if __name__ == "__main__":
    checker = SystemChecker()
    success = checker.run_checks()
    
    if not success:
        print("\n⚠ Some critical checks failed. Please resolve them before continuing.")
        sys.exit(1)
    
    print("\n✓ System checks passed!")
    sys.exit(0)
