# URL Shortener & Redirector

A modern, cross-platform, self-hosted URL shortener and redirector with a beautiful web UI, dynamic shortcut support, and easy management. Built with Python Flask and SQLite, designed for personal and small team use.

---

## Features

- **Static & Dynamic Shortcuts**: Create simple or parameterized redirects (e.g., `/r/meetwith/raj` → `https://g.co/meet/raj`).
- **Visual Dashboard**: Manage all shortcuts in a clean, interactive web UI.
- **Real-Time Editing**: Edit shortcuts with instant feedback, type detection, and suggestions.
- **Dynamic Shortcut Help**: Users get clear guidance if they visit a dynamic shortcut without providing a variable.
- **Configurable Security**: Deletion can require a password (if set in config).
- **Cross-Platform Autostart**: Scripts for Windows, Linux, and macOS to run the app at login/boot.
- **Step-by-Step Tutorial**: In-app guide at `/tutorial`.
- **No Cloud Required**: All data stays on your machine.

---

## Quick Start

1. **Install Python 3** (if not already installed).
2. **Clone the repository** and install dependencies:
   ```pwsh
   git clone <repo-url>
   cd r
   pip install -r requirements.txt
   ```
3. **Run the app:**
   ```pwsh
   python app.py
   ```
   The server will be available at [http://localhost/r/](http://localhost/r/) (or your configured port).

---

## Dashboard Overview

The dashboard lists all your shortcuts, with options to edit, delete, or test each one. Navigation links to Version, Tutorial, and README are provided.

![Dashboard](assets/dashboard.png)

---

## Creating & Editing Shortcuts

- **To create or edit:** Go to `/r/edit/<shortcut>` (e.g., `/r/edit/meetwith`).
- The edit page provides real-time feedback:
  - **Type detection**: Instantly shows if your shortcut is static (green) or dynamic (blue).
  - **Auto-prefix**: Adds `https://` if you forget it.
  - **Dynamic variable help**: Shows the variable name if your target uses `{variable}`.

![Edit Page](assets/edit.png)

---

## Dynamic Shortcuts

- Use curly braces in the target URL (e.g., `https://g.co/meet/{name}`) to create a dynamic shortcut.
- Visiting `/r/meetwith/raj` will redirect to `https://g.co/meet/raj`.
- If a user visits a dynamic shortcut without providing a variable, a helpful message appears:

![Dynamic Shortcut Help](assets/dynamic-no-arg-provided.png)

---

## Authentication & Security

- **Editing**: Anyone with access to the web UI can create or edit shortcuts.
- **Deleting**: If a password is set in the config and `delete_requires_password` is true, deletion requires authentication.
- **Config file**: `redirect.config.json` (auto-created on first run) allows you to set the port, redirect delay, and security options.

---

## In-App Tutorial

For a step-by-step guide with screenshots, visit `/tutorial` in your running app.

---

## Version Info

Check the app version and update status from the dashboard:

![Version Page](assets/version.png)

---

## Autostart on Boot (Cross-Platform)

Scripts are provided to set up the app to run at login or system boot:

- **Windows**: `autostart-windows.ps1`
- **Linux**: `autostart-linux.sh`
- **macOS**: `autostart-macos.sh`

Each script:
- Checks/installs Python and Git
- Clones or updates the repo
- Installs requirements
- Sets up the app to run at login/reboot using the platform's native scheduler

See `autostart-scripts.md` for details.

---

## Custom Domain or Local DNS

To use a friendly shortcut like `r.local`:

- **Windows**: Edit `C:\Windows\System32\drivers\etc\hosts` and add:
  ```
  127.0.0.1   r.local
  ```
- **macOS/Linux**: Edit `/etc/hosts` and add the same line.
- Access via `http://r.local/r/google`

---

## Troubleshooting

### Port Already in Use
If you see an error like `OSError: [Errno 98] Address already in use`, change the port in `redirect.config.json` and restart the app.

### Permissions
- Ports below 1024 may require admin privileges. For development, use a higher port (e.g., 5000).

---

## Security Note
This app is intended for local/private network use. Do **not** expose it to the public internet without proper authentication.

---

## License
MIT
