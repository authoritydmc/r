# URL Shortener/Redirector [![Docker Image CI](https://github.com/authoritydmc/r/actions/workflows/deploy.yml/badge.svg)](https://github.com/authoritydmc/r/actions/workflows/deploy.yml) [![Validate](https://github.com/authoritydmc/r/actions/workflows/validate.yml/badge.svg)](https://github.com/authoritydmc/r/actions/workflows/validate.yml)

A modern, self-hostable URL shortener and redirector with a beautiful UI, Docker support, and secure config management. Easily create, manage, and share custom short URLs for your team or company.

---



## Features

- **Modern UI**: Clean, responsive dashboard and success pages using Tailwind CSS and SVG/FontAwesome icons.
- **Config as JSON**: All settings stored in `data/redirect.json.config` (auto-created with secure defaults).
- **Secure by Default**: Random admin password generated on first run.
- **Docker-Ready**: Official image [`rajlabs/redirector`](https://hub.docker.com/r/rajlabs/redirector) with persistent data and easy volume/bind mount support.
- **Reverse Proxy Friendly**: Works behind Nginx, Traefik, etc. (see below).
- **Robust Testing**: Pytest-based tests for config and DB logic.
- **Audit & Stats**: Tracks access count, creation/update times, and IPs for each shortcut.
- **Dynamic Shortcuts**: Supports static and dynamic (parameterized) redirects.
- **Version Info**: `/version` page shows live version, commit info, and all accessible URLs (with copy/open buttons).

---

## Quick Start

### 1. Docker (Recommended)

#### Using a named volume (managed by Docker)

```sh
docker run -d --restart unless-stopped -p 80:80 -v redirector_data:/app/data --name redirector rajlabs/redirector
```
- Data is stored in the Docker-managed volume:
  - **Linux/macOS:** `/var/lib/docker/volumes/redirector_data/_data`
  - **Windows (Docker Desktop):** `\\wsl$\docker-desktop-data\data\docker\volumes\redirector_data\_data` (access via WSL or Docker Desktop's file explorer)

#### Using your current folder (bind mount, recommended for easy access)

```sh
docker run -d --restart unless-stopped -p 80:80 -v "${PWD}/data:/app/data" --name redirector rajlabs/redirector
```
- This will create (or use) a `data` folder in your current directory for persistent config and DB files.
- Works in PowerShell (Windows) and most modern shells. On Linux/macOS, you can use `$(pwd)/data:/app/data` instead.

- Visit: [http://localhost:80](http://localhost:80)
- The app's data directory inside the container is always `/app/data`.
- Admin password is auto-generated on first run (see container logs or the config file in the data folder).

#### Updating

Just pull the latest image and restart:

```sh
docker pull rajlabs/redirector
docker stop redirector && docker rm redirect
```
> (then re-run the above docker run command)

### 2. Manual (Python)

- Requires Python 3.8+
- Install dependencies:

```sh
pip install -r requirements.txt
```

- Run:

```sh
python app.py
```

- Visit: [http://localhost:80](http://localhost:80)

---

## Configuration

- All config is in `data/redirect.json.config` (auto-created if missing):
  - `port`: Port to run the app (default: 80)
  - `admin_password`: Admin password (random on first run)
  - `auto_redirect_delay`: Delay (seconds) before auto-redirect (default: 0)
  - `delete_requires_password`: Require password to delete shortcuts (default: true)

- Change config by editing the file or using the UI (where available).

---

## Data Persistence

- All data (config, DB) is in the `data/` directory.
- For Docker, always use a bind mount or volume for `/app/data` to persist data.

---

## Reverse Proxy Example (Nginx)

```
server {
    listen 80;
    server_name your.domain.com;

    location / {
        proxy_pass http://localhost:8080; # or whatever port you mapped
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Troubleshooting

- **Can't find admin password?**
  - Check the first lines of the container or app logs for the generated password.
  - Or, view/edit `data/redirect.json.config` directly.
- **Port already in use?**
  - Change the `port` in the config file or Docker port mapping.
- **Data not persisting?**
  - Ensure you are mounting the `data/` directory as a Docker volume or bind mount.
- **Reverse proxy issues?**
  - Make sure to set the correct headers (see above) and check your proxy config.

---

## Production Deployment

For production, always use a production-grade WSGI server instead of Flask's built-in server.

### Docker (Recommended)

The official Docker image runs with Gunicorn (production WSGI server) by default. No extra steps needed.

### Manual (Python)

- **Development mode:**
  - Run with Flask's built-in server (for local testing only):
    ```sh
    python app.py --debug
    ```
- **Production mode:**
  - Use Gunicorn (Linux/macOS):
    ```sh
    pip install gunicorn
    gunicorn -w 4 -b 0.0.0.0:80 app:app
    ```
  - Use Waitress (Windows):
    ```sh
    pip install waitress
    waitress-serve --port=80 app:app
    ```

- The app prints an ASCII art banner and clearly shows whether it is running in DEV or PROD mode at startup.
- By default, `python app.py` runs in production mode (debug=False). Use `--debug` for development.

---

## Development & Testing

- Run tests:

```sh
pytest
```

- Lint:

```sh
flake8 app/
```

---

## Running Tests

To run all tests for this app, use the following command from the project root:

```
python -m pytest tests --maxfail=2 --disable-warnings -v
```

If you see an error like `No module named pytest`, install pytest first:

```
pip install pytest
```

This will run all unit and integration tests, including those for the version endpoint and utility functions. Ensure you have all dependencies installed (see requirements.txt) and that you are in the project root directory.

---

## Version & Credits

- See `/version` in the app for live version, commit info, and accessible URLs.
- Created by [@authoritydmc](https://github.com/authoritydmc) and contributors.

---

## License

MIT

---

## Screenshots

| Dashboard | Version Page | Edit Shortcut | Dynamic Shortcut (No Arg) |
|-----------|-------------|--------------|---------------------------|
| ![Dashboard](assets/dashboard.png) | ![Version](assets/version.png) | ![Edit](assets/edit.png) | ![Dynamic No Arg](assets/dynamic-no-arg-provided.png) |

---

## Custom Hostname Setup (Local `r/` Shortcuts)

To use URLs like `http://r/google` on your local machine, map `r` to `127.0.0.1` in your hosts file:

**Windows:**
1. Open Notepad as Administrator.
2. Open the file: `C:\Windows\System32\drivers\etc\hosts`
3. Add this line at the end:
   ```
   127.0.0.1   r
   ```
4. Save the file. Now you can use `http://r/shortcut` in your browser.

**Linux/macOS:**
1. Edit `/etc/hosts` with sudo:
   ```sh
   sudo nano /etc/hosts
   ```
2. Add this line at the end:
   ```
   127.0.0.1   r
   ```
3. Save and close. Now you can use `http://r/shortcut` in your browser.

> **Note:** On first run, if you have just set up the `r` hostname (via hosts file or DNS), make sure to access `http://r/` (not just `r/`) in your browser at least once. This ensures your browser recognizes `r` as a valid domain and flushes any old cache or search behavior. This step is only needed if you are using the custom `r/` shortcut setup described above.

---

## Automated Hostname Setup (r/ shortcut)

To automatically add the `r` hostname for local shortcuts, use the provided script for your OS:

- **Windows:**
  - Run in PowerShell as Administrator:
    ```powershell
    ./autostart-windows.ps1
    ```
    This will set up the app and call `scripts/add-r-host-windows.ps1` to add `127.0.0.1   r` to your hosts file (if you have admin rights), or print instructions if not.
- **macOS:**
  - Run in Terminal:
    ```sh
    bash autostart-macos.sh
    ```
    This will set up the app and call `scripts/add-r-host-macos.sh` to add `127.0.0.1   r` to `/etc/hosts` (if you have sudo/root), or print instructions if not.
- **Linux:**
  - Run in Terminal:
    ```sh
    bash autostart-linux.sh
    ```
    This will set up the app and call `scripts/add-r-host-linux.sh` to add `127.0.0.1   r` to `/etc/hosts` (if you have sudo/root), or print instructions if not.

You can also run the scripts in `scripts/` directly to only add the host entry.

---

## Add `r` Hostname Only (Shortcut Setup)

If you only want to add the `r` hostname for local shortcuts (without running the full autostart setup), use the provided script for your OS:

- **Windows:**
  - Run in PowerShell as Administrator:
    ```powershell
    ./scripts/add-r-host-windows.ps1
    ```
- **macOS:**
  - Run in Terminal:
    ```sh
    bash scripts/add-r-host-macos.sh
    ```
- **Linux:**
  - Run in Terminal:
    ```sh
    bash scripts/add-r-host-linux.sh
    ```

Each script will attempt to add `127.0.0.1   r` to your hosts file if you have the necessary privileges, or print instructions if not.

---

## Company-Wide Installation & Team Usage

To make `r/` shortcuts available to your entire team or company:

1. **Deploy the app on a central server** (on-prem or cloud VM/container).
   - Use a static IP or DNS name (e.g., `r.company.com`).
   - Run behind a reverse proxy (see Nginx example above) for clean URLs.
2. **Configure DNS:**
   - Set up an internal DNS record so `r` (or `r.company.com`) points to the server's IP.
   - Your IT team can add a DNS A record for `r` in your internal DNS system.
   - All users on the network will be able to use `http://r/shortcut` or `http://r.company.com/shortcut`.
3. **(Optional) Use hosts file for small teams:**
   - Each user can add the server's IP and `r` to their hosts file as above.
4. **Secure the admin interface:**
   - Use a strong admin password (auto-generated by default).
   - Optionally, restrict admin access by IP or VPN.
5. **Share the base URL:**
   - Tell your team to use `http://r/shortcut` for all shared links.

This setup allows everyone in your organization to use simple, memorable shortcuts like `r/google` or `r/docs` from any device on the network.

---

## Project Structure

Your Flask app expects static files (images, CSS, JS, etc.) to be in the `app/static/` directory. For example:

```
project-root/
├── app/
│   ├── __init__.py
│   ├── routes.py
│   ├── utils.py
│   ├── version.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   └── ...
│   └── static/
│       └── assets/
│           ├── logo.png
│           └── ...
├── requirements.txt
├── Dockerfile
└── ...
```

- Reference static assets in templates using:
  ```html
  <img src="{{ url_for('static', filename='assets/logo.png') }}" alt="Logo">
  ```
- Place all images and static files in `app/static/assets/` for Flask to serve them correctly.
