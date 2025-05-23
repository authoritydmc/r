# URL Shortener & Redirector

A modern, cross-platform, self-hosted URL shortener and redirector with a beautiful web UI, dynamic shortcut support, and easy management. Built with Python Flask and SQLite, designed for personal and small team use.

---

## Company-Wide Usage

To use this URL shortener across your company or team:

1. **Deploy the app on a server or always-on workstation** accessible to everyone on your internal network.
2. **Set a static IP or hostname** for the machine running the app (e.g., `r.local` or `shortcuts.company.local`).
3. **Configure DNS or hosts file** for all users:
   - For small teams, add an entry to each user's `hosts` file:
     - **Windows:** `C:\Windows\System32\drivers\etc\hosts`
     - **macOS/Linux:** `/etc/hosts`
     - Example entry:
       ```
       192.168.1.100   r.local
       ```
     Replace `192.168.1.100` with your server's IP address.
   - For larger organizations, set up an internal DNS record for `r.local` or your chosen hostname.
4. **Share the base URL** (e.g., `http://r.local/`) with your team. Users can now access shortcuts like `http://r.local/google` from any device on the network.
5. **Manage shortcuts centrally:**
   - Use the dashboard to add, edit, or remove shortcuts for everyone.
   - Optionally, set a password for deletion to prevent accidental removals.
6. **(Optional) Enable HTTPS:**
   - For extra security, consider running the app behind a reverse proxy (like Nginx) with HTTPS enabled.

---

## Features

- **Static & Dynamic Shortcuts**: Create simple or parameterized redirects (e.g., `/meetwith/raj` → `https://g.co/meet/raj`).
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
   The server will be available at [http://localhost/](http://localhost/) (or your configured port).

---

## Configuration & Settings

All configuration is now managed via the web UI and stored in the app's database (not in a JSON file).

- **Port**: The port is set on first run and can be changed by editing the database or using the admin interface (if available).
- **Redirect Delay**: The auto-redirect delay (in seconds) can be set via the admin UI or by updating the `auto_redirect_delay` config in the database.
- **Admin Password**: The admin password is generated on first run and can be changed from the admin/login page.
- **Delete Requires Password**: You can toggle whether deleting a shortcut requires the admin password from the admin UI.

> **Tip:** If you need to reset a config, you can clear the relevant value from the database using a SQLite editor, or use the admin interface if available.

---

## Dashboard Overview

The dashboard lists all your shortcuts, with options to edit, delete, or test each one. Navigation links to Version, Tutorial, and README are provided.

![Dashboard](assets/dashboard.png)

---

## Creating & Editing Shortcuts

- **To create or edit:** Go to `/edit/<shortcut>` (e.g., `/edit/meetwith`).
- The edit page provides real-time feedback:
  - **Type detection**: Instantly shows if your shortcut is static (green) or dynamic (blue).
  - **Auto-prefix**: Adds `https://` if you forget it.
  - **Dynamic variable help**: Shows the variable name if your target uses `{variable}`.

![Edit Page](assets/edit.png)

---

## Dynamic Shortcuts

- Use curly braces in the target URL (e.g., `https://g.co/meet/{name}`) to create a dynamic shortcut.
- Visiting `/meetwith/raj` will redirect to `https://g.co/meet/raj`.
- If a user visits a dynamic shortcut without providing a variable, a helpful message appears:

![Dynamic Shortcut Help](assets/dynamic-no-arg-provided.png)

---

## Authentication & Security

- **Editing**: Anyone with access to the web UI can create or edit shortcuts.
- **Deleting**: If the "Delete Requires Password" option is enabled, deletion requires the admin password.
- **Configuration**: All settings (port, delay, password) are managed via the web UI and stored in the database. There is no JSON config file.
- **Admin Password**: The password is generated on first run and can be changed from the admin/login page.

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
- Access via `http://r.local/google` (not `/r/google`)

---

## Troubleshooting

### Port Already in Use
If you see an error like `OSError: [Errno 98] Address already in use`, change the port using the admin UI or update the value in the database, then restart the app.

### Permissions
- Ports below 1024 may require admin privileges. For development, use a higher port (e.g., 5000).

### Resetting Configuration
If you need to reset the admin password or other settings, you can do so via the admin UI or by editing the database directly with a SQLite editor.

---

## Security Note
This app is intended for local/private network use. Do **not** expose it to the public internet without proper authentication.

---

## License
MIT
