# URL Shortener/Redirector

A simple Python Flask-based URL redirector with support for static and dynamic redirects, using SQLite for storage.

## Features
- Static redirects: `/r/google` → `https://www.google.com`
- Dynamic redirects: `/r/meetwith/raj` → `https://g.co/meet/raj`
- Easy configuration via SQLite database
- Cross-platform: Windows, macOS, Linux

## Setup

### 1. Install dependencies

```sh
pip install -r requirements.txt
```

### 2. Initialize the database

The database is auto-initialized on first run. To manually initialize:

```sh
python app.py
```

### 3. Run the server

```sh
python app.py
```

The server will be available at http://localhost:5000/r/

## Adding Redirects

You can add redirects directly to the SQLite database (`redirects.db`). Example using Python:

```
import sqlite3
conn = sqlite3.connect('redirects.db')
cursor = conn.cursor()
# Static redirect
cursor.execute("INSERT INTO redirects (type, pattern, target) VALUES (?, ?, ?)", ('static', 'google', 'https://www.google.com'))
# Dynamic redirect
cursor.execute("INSERT INTO redirects (type, pattern, target) VALUES (?, ?, ?)", ('dynamic', 'meetwith', 'https://g.co/meet/{name}'))
conn.commit()
conn.close()
```

## Auto Start on Boot

### Windows
- Use Task Scheduler to create a task that runs `pythonw.exe app.py` at logon.

### macOS
- Use `launchctl` with a plist file in `~/Library/LaunchAgents/` to run the script at login.

### Linux
- Use `systemd` user service or add to `crontab -@reboot`.

## Assigning `r/` using Local DNS

### Windows
- Edit `C:\Windows\System32\drivers\etc\hosts` and add:
  ```
  127.0.0.1   r.local
  ```
- Access via `http://r.local:5000/r/google`

### macOS/Linux
- Edit `/etc/hosts` and add:
  ```
  127.0.0.1   r.local
  ```
- Access via `http://r.local:5000/r/google`

For browser shortcut, you can also use custom search engines in Chrome/Firefox to map `r/` to `http://localhost:5000/r/%s`.

---

**Security note:** This is a local tool. Do not expose to the public internet without authentication.
