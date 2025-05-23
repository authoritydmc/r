# URL Shortener/Redirector

A simple Python Flask-based URL redirector with support for static and dynamic redirects, using SQLite for storage and a web UI for management.

## Features
- Static redirects: `/r/google` → `https://www.google.com`
- Dynamic redirects: `/r/meetwith/raj` → `https://g.co/meet/raj`
- Easy redirect creation and editing via web UI
- Configurable redirect delay and port
- Cross-platform: Windows, macOS, Linux

## Setup

### 1. Install dependencies

```sh
pip install -r requirements.txt
```

### 2. Initialize and Run the Server
The database and config file are auto-initialized on first run.
```sh
python app.py
```
- The server will be available at `http://localhost/r/` (or the port you configure).

## Configuration (`redirect.config.json`)
A file named `redirect.config.json` is used for configuration. It is auto-created if missing. Example:
```json
{
  "auto_redirect_delay": 0,
  "port": 80
}
```
- `auto_redirect_delay`: Number of seconds to wait before redirecting. If set to 0, redirects are instant. If set to a positive number, users see a countdown page before being redirected.
- `port`: The port the server will run on. Default is 80. Change this if you want to use a different port (e.g., 5000 for development).

## Managing Redirects via Web UI
- To create a new redirect: Visit `/r/xyz` (where `xyz` is your desired shortcut) in your browser. If it doesn't exist, a form will appear to create it.
- To edit an existing redirect: Visit `/r/edit/xyz` to update the shortcut and its target.

## Creating and Editing Shortcuts

- To create or edit a shortcut, go to `/edit/<shortcut>` (e.g. `/edit/meetwith`).
- The edit page provides a form for both creating and updating shortcuts.
- **Real-time suggestions:**
  - The form will automatically detect if your shortcut is **Static** or **Dynamic** and show a colored message (green for static, blue for dynamic).
  - If you forget to add `https://` to your target URL, it will be added automatically.
- **Dynamic shortcuts:**
  - Use curly braces in the target URL (e.g. `https://g.co/meet/{name}`) to create a dynamic shortcut.
  - Visiting `/meetwith/raj` will redirect to `https://g.co/meet/raj`.
- **Static shortcuts:**
  - If you do not use curly braces, the shortcut will always redirect to the same address.

## Dashboard

- The dashboard (`/`) lists all shortcuts and provides links to edit, delete, or test them.
- URL creation is now only available from the edit page.

## Tutorial

- For a step-by-step guide, visit `/tutorial` in your running app.

## Auto Start on Boot

### Windows
- Use Task Scheduler to create a task that runs `pythonw.exe app.py` at logon.
- Or, use Windows Task Scheduler to run a batch file with:
  ```bat
  cd /d D:\codelab\r
  pythonw.exe app.py
  ```
- Or, use Windows Subsystem for Linux (WSL) and add to crontab (see Linux section).

### macOS
- Use `launchctl` with a plist file in `~/Library/LaunchAgents/` to run the script at login.
- Or, add to your user crontab:
  ```sh
  @reboot cd /path/to/your/project && /usr/bin/python3 app.py
  ```

### Linux
- Use a `systemd` user service or add to your user crontab:
  ```sh
  @reboot cd /path/to/your/project && /usr/bin/python3 app.py
  ```
- To edit your crontab, run:
  ```sh
  crontab -e
  ```

## Assigning `r/` using Local DNS

### Windows
- Edit `C:\Windows\System32\drivers\etc\hosts` and add:
  ```
  127.0.0.1   r.local
  ```
- Access via `http://r.local/r/google`

### macOS/Linux
- Edit `/etc/hosts` and add:
  ```
  127.0.0.1   r.local
  ```
- Access via `http://r.local/r/google`

For browser shortcut, you can also use custom search engines in Chrome/Firefox to map `r/` to `http://localhost/r/%s` (or the port you use).

## Troubleshooting: Port Already in Use
If you see an error like `OSError: [Errno 98] Address already in use` or `OSError: [WinError 10013]`, it means the port (default 80) is already being used by another process.

### How to Fix
#### 1. Change the Port
- Edit `redirect.config.json` and set a different port (e.g., 5000):
  ```json
  {
    "auto_redirect_delay": 0,
    "port": 5000
  }
  ```
- Restart the server and access it at the new port (e.g., `http://localhost:5000/r/xyz`).

#### 2. Free the Port
##### Windows
- Open PowerShell as Administrator and run:
  ```powershell
  netstat -ano | findstr :80
  # Note the PID in the last column
  Stop-Process -Id <PID> -Force
  ```
- Or, use Task Manager to find and end the process using the port.

##### macOS/Linux
- Open Terminal and run:
  ```sh
  sudo lsof -i :80
  # Note the PID in the second column
  sudo kill -9 <PID>
  ```
- You may need `sudo` to free system ports.

##### General Advice
- Ports below 1024 may require admin/root privileges. For development, use a higher port (e.g., 5000 or 8080).
- Always restart the server after changing the port.

---
**Security note:** This is a local tool. Do not expose to the public internet without authentication.
