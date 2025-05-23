#!/bin/bash
# Bash script to auto-setup and run the URL Shortener/Redirector on macOS (Launchd)
set -e
REPO="authoritydmc/r"
WORKDIR="$HOME/url-shortener"

# Check for python3
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python3 not found. Installing via Homebrew..."
  if ! command -v brew >/dev/null 2>&1; then
    echo "Homebrew not found. Please install Homebrew and rerun this script."
    exit 1
  fi
  brew install python3 git
fi

# Check for git
if ! command -v git >/dev/null 2>&1; then
  echo "Git not found. Installing via Homebrew..."
  if ! command -v brew >/dev/null 2>&1; then
    echo "Homebrew not found. Please install Homebrew and rerun this script."
    exit 1
  fi
  brew install git
fi

# Clone or update repo
if [ ! -d "$WORKDIR" ]; then git clone https://github.com/$REPO.git "$WORKDIR"; else cd "$WORKDIR" && git pull; fi

# Install requirements
pip3 install --user -r "$WORKDIR/requirements.txt"

# Create LaunchAgent plist
PLIST=~/Library/LaunchAgents/com.urlshortener.autostart.plist
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.urlshortener.autostart</string>
    <key>ProgramArguments</key>
    <array>
        <string>$(command -v python3)</string>
        <string>$WORKDIR/app.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$WORKDIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF

launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"

echo "Setup complete. The app will run at every login."
# (No changes needed for autostart scripts unless you want to change the default port or add environment variable support. If you want to add that, let me know!)
