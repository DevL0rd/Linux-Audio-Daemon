#!/bin/bash
set -e

REPO_DIR=$(pwd)
if [ ! -f "$REPO_DIR/src/daemon.py" ]; then
    echo "Please run this script from the repository directory."
    exit 1
fi

echo "Setting up udev rules for ASUS ROG devices..."
echo 'SUBSYSTEM=="hidraw", ATTRS{idVendor}=="0b05", ATTRS{idProduct}=="1afa", GROUP="users", MODE="0664"' | sudo tee /etc/udev/rules.d/99-rog-headset.rules > /dev/null

sudo udevadm control --reload-rules
sudo udevadm trigger

echo "Setting up systemd user service..."
mkdir -p ~/.config/systemd/user

cat <<EOF > ~/.config/systemd/user/smart-audio-manager.service
[Unit]
Description=Smart Audio Manager (Priority Routing)
After=pipewire.service wireplumber.service

[Service]
Type=simple
WorkingDirectory=$REPO_DIR
ExecStart=/usr/bin/python3 $REPO_DIR/src/daemon.py
Restart=always
RestartSec=3
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONPATH=$REPO_DIR/src

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now smart-audio-manager.service

echo ""
echo "Done! The service is now running in the background."
echo "Check config.json to edit device priorities and icons!"
echo "Logs: journalctl --user -u smart-audio-manager.service -f"
