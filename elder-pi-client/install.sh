#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="elder-pi-client"
USER_SERVICE_DIR="${HOME}/.config/systemd/user"
TOKEN_DIR="${HOME}/.config/elder-pi"
TOKEN_FILE="${TOKEN_DIR}/device-token"

echo "Installing elder-pi-client..."

mkdir -p "$USER_SERVICE_DIR"
mkdir -p "$TOKEN_DIR"

if [ ! -f "$TOKEN_FILE" ]; then
    echo "Creating example token file at ${TOKEN_FILE}"
    echo "REPLACE_WITH_DEVICE_TOKEN" > "$TOKEN_FILE"
    chmod 600 "$TOKEN_FILE"
fi

cat > "${USER_SERVICE_DIR}/${SERVICE_NAME}.service" <<EOF
[Unit]
Description=Elder Pi Video Call Client
After=graphical-session.target network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 ${SCRIPT_DIR}/launcher.py
WorkingDirectory=${SCRIPT_DIR}
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME"

echo "Installation complete. Start with:"
echo "  systemctl --user start ${SERVICE_NAME}"
