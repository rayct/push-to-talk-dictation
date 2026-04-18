#!/bin/bash
# Installation script for push-to-talk dictation daemon
# Usage: ./install.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv"
INSTALL_PREFIX="${HOME}/.local"
BIN_DIR="${INSTALL_PREFIX}/bin"
SERVICE_DIR="${HOME}/.config/systemd/user"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
info() {
    echo -e "${GREEN}[INFO]${NC} $@"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $@"
}

error() {
    echo -e "${RED}[ERROR]${NC} $@"
    exit 1
}

# Check Python version
info "Checking Python version..."
python3 --version || error "Python 3 not found"

# Create virtual environment
info "Creating virtual environment at ${VENV_DIR}..."
python3 -m venv "${VENV_DIR}" || error "Failed to create venv"

# Activate venv
source "${VENV_DIR}/bin/activate"

# Upgrade pip
info "Upgrading pip..."
pip install --quiet --upgrade pip setuptools wheel || error "Failed to upgrade pip"

# Install dependencies
info "Installing Python dependencies..."
pip install --quiet -r "${SCRIPT_DIR}/requirements.txt" || error "Failed to install dependencies"

# Run system checks
info "Running system checks..."
python3 "${SCRIPT_DIR}/sysinfo_check.py" || warn "Some system checks failed (see above)"

# Create user directories
info "Creating user directories..."
mkdir -p "${HOME}/.cache/whisper"
mkdir -p "${HOME}/.local/share/push-to-talk-dict"
mkdir -p "${SERVICE_DIR}"

# Create wrapper script
info "Creating wrapper script..."
mkdir -p "${BIN_DIR}"
cat > "${BIN_DIR}/push-to-talk-dict" << 'EOF'
#!/bin/bash
# Wrapper script for push-to-talk dictation daemon

SCRIPT_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
VENV_DIR="${SCRIPT_DIR}/../opt/push-to-talk-dict/venv"
DAEMON_DIR="${SCRIPT_DIR}/../opt/push-to-talk-dict"

# Try multiple possible locations
if [ ! -d "$VENV_DIR" ]; then
    VENV_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && cd ../../opt/push-to-talk-dict && pwd)/venv"
fi

if [ ! -d "$VENV_DIR" ]; then
    # Fallback: look in current repo
    VENV_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)/../../../push-to-talk-dictation/venv"
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment not found"
    exit 1
fi

source "${VENV_DIR}/bin/activate"
cd "${DAEMON_DIR}" || cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../../opt/push-to-talk-dict"

exec python3 dictation_daemon.py "$@"
EOF
chmod +x "${BIN_DIR}/push-to-talk-dict"

# Create systemd service
info "Creating systemd service..."
SERVICE_FILE="${SERVICE_DIR}/push-to-talk-dict.service"
mkdir -p "${SERVICE_DIR}"

cat > "${SERVICE_FILE}" << EOF
[Unit]
Description=Push-to-Talk Dictation Daemon
After=display-manager.service
PartOf=graphical-session.target

[Service]
Type=simple
ExecStart=${BIN_DIR}/push-to-talk-dict
Restart=on-failure
RestartSec=5
Environment="DISPLAY=:0"
Environment="XAUTHORITY=%h/.Xauthority"

[Install]
WantedBy=graphical-session.target
EOF

# Install optional X11 detection for DISPLAY
cat >> "${SERVICE_FILE}" << 'EOF'

# Dynamic DISPLAY detection
Environment="PYTHONUNBUFFERED=1"
EOF

chmod 644 "${SERVICE_FILE}"

# Create helper script to set DISPLAY
cat > "${BIN_DIR}/push-to-talk-dict-service" << 'EOF'
#!/bin/bash
# Helper script to start daemon with correct DISPLAY

# Detect DISPLAY from currently running X11
if [ -z "$DISPLAY" ]; then
    # Try to detect running X display
    for pid in $(pgrep -u $USER); do
        export $(grep -z DISPLAY /proc/$pid/environ | tr '\0' '\n')
        if [ -n "$DISPLAY" ]; then
            break
        fi
    done
fi

# Fallback
if [ -z "$DISPLAY" ]; then
    export DISPLAY=:0
fi

export XAUTHORITY="${HOME}/.Xauthority"

"${BASH_SOURCE%/*}/push-to-talk-dict" "$@"
EOF
chmod +x "${BIN_DIR}/push-to-talk-dict-service"

# Summary
echo ""
info "Installation complete!"
echo ""
echo "Next steps:"
echo "  1. Install systemd service:"
echo "     systemctl --user daemon-reload"
echo "     systemctl --user enable push-to-talk-dict.service"
echo ""
echo "  2. Select target window:"
echo "     ${BIN_DIR}/push-to-talk-dict --select-window"
echo ""
echo "  3. Start the daemon:"
echo "     systemctl --user start push-to-talk-dict.service"
echo "     # OR manually:"
echo "     ${BIN_DIR}/push-to-talk-dict"
echo ""
echo "  4. Check status:"
echo "     systemctl --user status push-to-talk-dict.service"
echo ""
echo "  5. View logs:"
echo "     journalctl --user -u push-to-talk-dict.service -f"
echo ""

# Ask to proceed with systemd setup
read -p "Enable systemd service now? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    info "Enabling systemd service..."
    systemctl --user daemon-reload
    systemctl --user enable push-to-talk-dict.service
    info "Systemd service enabled"
    
    read -p "Start daemon now? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        systemctl --user start push-to-talk-dict.service
        sleep 2
        systemctl --user status push-to-talk-dict.service --no-pager
    fi
fi

info "Installation complete!"
