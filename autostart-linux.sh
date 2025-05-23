#!/bin/bash
# Bash script to auto-setup and run the URL Shortener/Redirector on Linux (systemd user service)
set -e
REPO="authoritydmc/redirect"
WORKDIR="$HOME/redirect"

# Check for python3
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python3 not found. Installing..."
  if command -v apt >/dev/null 2>&1; then sudo apt update && sudo apt install -y python3 python3-pip git;
  elif command -v dnf >/dev/null 2>&1; then sudo dnf install -y python3 python3-pip git;
  elif command -v yum >/dev/null 2>&1; then sudo yum install -y python3 python3-pip git;
  elif command -v pacman >/dev/null 2>&1; then sudo pacman -Sy python python-pip git --noconfirm;
  else echo "Please install Python 3, pip, and git manually."; exit 1; fi
fi

# Check for git
if ! command -v git >/dev/null 2>&1; then
  echo "Git not found. Installing..."
  if command -v apt >/dev/null 2>&1; then sudo apt update && sudo apt install -y git;
  elif command -v dnf >/dev/null 2>&1; then sudo dnf install -y git;
  elif command -v yum >/dev/null 2>&1; then sudo yum install -y git;
  elif command -v pacman >/dev/null 2>&1; then sudo pacman -Sy git --noconfirm;
  else echo "Please install git manually."; exit 1; fi
fi

# Clone or update repo
if [ ! -d "$WORKDIR" ]; then git clone https://github.com/$REPO.git "$WORKDIR"; else cd "$WORKDIR" && git pull; fi

# Install requirements
pip3 install --user -r "$WORKDIR/requirements.txt"

# Create systemd user service
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/urlshortener.service <<EOF
[Unit]
Description=URL Shortener/Redirector

[Service]
Type=simple
ExecStart=$(command -v python3) $WORKDIR/app.py
WorkingDirectory=$WORKDIR
Restart=always

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now urlshortener.service

echo "Setup complete. The app will run at every login."

# Add 'r' to /etc/hosts (shortcut setup)
bash "$(dirname "$0")/scripts/add-r-host-linux.sh"
