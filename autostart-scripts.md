# Autostart Scripts for URL Shortener/Redirector

Below are ready-to-use scripts for Windows (PowerShell), Linux (Bash), and macOS (Bash/Launchd) to automatically download and run this project from GitHub on every reboot.

Replace `<YOUR_GITHUB_USERNAME>` with your actual GitHub username if you have forked the repo, or use the default `authoritydmc` for the original repo.

---

## Windows (PowerShell, Task Scheduler)

1. Open PowerShell as Administrator.
2. Run this script to create a scheduled task that runs the app on every logon:

```powershell
$repo = "authoritydmc/r"
$workdir = "$env:USERPROFILE\url-shortener"
$py = "python"

if (-not (Test-Path $workdir)) { git clone https://github.com/$repo.git $workdir }
else { cd $workdir; git pull }

$action = New-ScheduledTaskAction -Execute $py -Argument "app.py" -WorkingDirectory $workdir
$trigger = New-ScheduledTaskTrigger -AtLogOn
Register-ScheduledTask -TaskName "URLShortenerAutoStart" -Action $action -Trigger $trigger -Force
```

- This will clone (or update) the repo and set up a Task Scheduler entry to run the app at every logon.
- Make sure Python is in your PATH and dependencies are installed (`pip install -r requirements.txt`).

---

## Linux (Bash, systemd user service)

1. Save this as `~/.config/systemd/user/urlshortener.service`:

```ini
[Unit]
Description=URL Shortener/Redirector

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/$USER/url-shortener/app.py
WorkingDirectory=/home/$USER/url-shortener
Restart=always

[Install]
WantedBy=default.target
```

2. Use this script to clone/update the repo and enable the service:

```bash
REPO="authoritydmc/r"
WORKDIR="$HOME/url-shortener"
if [ ! -d "$WORKDIR" ]; then git clone https://github.com/$REPO.git "$WORKDIR"; else cd "$WORKDIR" && git pull; fi
pip3 install --user -r "$WORKDIR/requirements.txt"
systemctl --user daemon-reload
systemctl --user enable --now urlshortener.service
```

---

## macOS (Bash + Launchd)

1. Save this as `~/Library/LaunchAgents/com.urlshortener.autostart.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.urlshortener.autostart</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/$USER/url-shortener/app.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/$USER/url-shortener</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

2. Use this script to clone/update the repo and load the LaunchAgent:

```bash
REPO="authoritydmc/r"
WORKDIR="$HOME/url-shortener"
if [ ! -d "$WORKDIR" ]; then git clone https://github.com/$REPO.git "$WORKDIR"; else cd "$WORKDIR" && git pull; fi
pip3 install --user -r "$WORKDIR/requirements.txt"
launchctl unload ~/Library/LaunchAgents/com.urlshortener.autostart.plist 2>/dev/null
launchctl load ~/Library/LaunchAgents/com.urlshortener.autostart.plist
```

---

## Notes
- All scripts assume Python 3 is installed and available as `python` or `python3`.
- You may need to adjust the Python path or working directory for your environment.
- For other platforms, adapt the above scripts as needed.
- For updates, just re-run the script or pull the latest code.
