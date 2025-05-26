# URL Shortener/Redirector [![Docker Image CI](https://github.com/authoritydmc/r/actions/workflows/deploy-prod-main.yml/badge.svg)](https://github.com/authoritydmc/r/actions/workflows/deploy-prod-main.yml)[![Docker Image CI](https://github.com/authoritydmc/r/actions/workflows/deploy-develop.yml/badge.svg)](https://github.com/authoritydmc/r/actions/workflows/deploy-develop.yml) [![Validate](https://github.com/authoritydmc/r/actions/workflows/validate.yml/badge.svg)](https://github.com/authoritydmc/r/actions/workflows/validate.yml)

A modern, self-hostable URL shortener and redirector with a beautiful UI, Docker support, and secure config management. Easily create, manage, and share custom short URLs for your team or company.

---

## Table of Contents
- [Features](#features)
- [Quick Start](#quick-start)
  - [Docker Compose (Recommended)](#docker-compose-recommended)
  - [Docker (Pull Prebuilt Image)](#docker-pull-prebuilt-image)
  - [Manual (Python)](#manual-python)
- [Hostname Setup for r/ Shortcuts](#hostname-setup-for-r-shortcuts)
  - [Quick Hostname Setup (Recommended)](#quick-hostname-setup-recommended)
  - [Manual Hostname Setup](#manual-hostname-setup)
- [Configuration](#configuration)
- [Data Persistence](#data-persistence)
- [Reverse Proxy Example](#reverse-proxy-example-nginx)
- [Troubleshooting](#troubleshooting)
- [Production Deployment](#production-deployment)
- [Development & Testing](#development--testing)
- [Project Structure](#project-structure)
- [Upstream Shortcut Checking](#upstream-shortcut-existence-checking--upstream-config)
- [Company-Wide Installation & Team Usage](#company-wide-installation--team-usage)
- [Version & Credits](#version--credits)
- [License](#license)

---

## Features

- **Modern UI**: Clean, responsive dashboard and success pages using Tailwind CSS and SVG/FontAwesome icons.
- **Config as JSON**: All settings stored in `data/redirect.config.json` (auto-created with secure defaults).
- **Secure by Default**: Random admin password generated on first run.
- **Docker-Ready**: Official image [`rajlabs/redirector`](https://hub.docker.com/r/rajlabs/redirector) with persistent data and easy volume/bind mount support.
- **Reverse Proxy Friendly**: Works behind Nginx, Traefik, etc. (see below).
- **Robust Testing**: Pytest-based tests for config and DB logic.
- **Audit & Stats**: Tracks access count, creation/update times, and IPs for each shortcut.
- **Dynamic Shortcuts**: Supports static and dynamic (parameterized) redirects.
- **Version Info**: `/version` page shows live version, commit info, and all accessible URLs (with copy/open buttons).

---

## Quick Start

### 1. Docker Compose (Recommended)

A `docker-compose.yml` is provided for easy setup with Redis:

```sh
docker compose up --build
```

- This will build and start two containers:
  - `app`: The Flask URL shortener/redirector (port 80)
  - `redis`: Redis server (port 6379)
- Data is stored in the `data/` folder on your host and mounted into the app container.
- The app will connect to Redis at `redis:6379` (service name in Docker Compose).
- The config file is `data/redirect.config.json`.

#### Updating

To update, pull the latest code and run:

```sh
docker compose up --build -d
```

#### Stopping

```sh
docker compose down
```

### 2. Docker (Pull Prebuilt Image)

You can run the app using the official image from Docker Hub: [`rajlabs/redirector`](https://hub.docker.com/r/rajlabs/redirector)

#### With Docker Redis (separate container)

First, start Redis:

```sh
docker run -d --name redis --restart unless-stopped -p 6379:6379 redis:7.2-alpine
```

Then run the app, connecting to Redis by container name:

```sh
docker run -d --name redirector --restart unless-stopped \
  -p 80:80 \
  -v redirector_data:/app/data \
  -e REDIS_HOST=redis \
  -e REDIS_PORT=6379 \
  --link redis:redis \
  rajlabs/redirector
```

- This uses a Docker named volume (`redirector_data`) for persistent data.
- The app will connect to Redis at `redis:6379`.

#### With a Host Directory (custom location)

To store data in a specific folder on your host:

```sh
docker run -d --name redirector --restart unless-stopped \
  -p 80:80 \
  -v /absolute/path/to/your/data:/app/data \
  -e REDIS_HOST=redis \
  -e REDIS_PORT=6379 \
  --link redis:redis \
  rajlabs/redirector
```

Replace `/absolute/path/to/your/data` with your desired directory.

#### Without Redis (SQLite only)

If you do not want to use Redis, set `"enabled": false` in `data/redirect.config.json` under the `redis` section, or omit the Redis environment variables.

---

### 3. Manual (Python)

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

## Hostname Setup for r/ Shortcuts

### Quick Hostname Setup (Recommended)
To use URLs like `http://r/google` on your local machine, add `r` to your hosts file. Use the provided script for your OS (no need for full autostart or Docker restart):

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

### Manual Hostname Setup
If you prefer to edit your hosts file manually:

- **Windows:**
  1. Open Notepad as Administrator.
  2. Open the file: `C:\Windows\System32\drivers\etc\hosts`
  3. Add this line at the end:
     ```
     127.0.0.1   r
     ```
  4. Save the file. Now you can use `http://r/shortcut` in your browser.

- **Linux/macOS:**
  1. Edit `/etc/hosts` with sudo:
     ```sh
     sudo nano /etc/hosts
     ```
  2. Add this line at the end:
     ```
     127.0.0.1   r
     ```
  3. Save and close. Now you can use `http://r/shortcut` in your browser.

> **Note:** On first run, if you have just set up the `r` hostname (via hosts file or DNS), make sure to access `http://r/` (not just `r/`) in your browser at least once. This ensures your browser recognizes `r` as a valid domain and flushes any old cache or search behavior.

---

## Configuration

- All config is in `data/redirect.config.json` (auto-created if missing):
  - `port`: Port to run the app (default: 80)
  - `admin_password`: Admin password (random on first run)
  - `auto_redirect_delay`: Delay (seconds) before auto-redirect (default: 0)
  - `delete_requires_password`: Require password to delete shortcuts (default: true)
  - `upstreams`: List of upstream redirectors (see below)
  - `redis`: Redis config (enabled, host, port)

- Change config by editing the file or using the UI (where available).

---

## Docker Compose Details

- The app and Redis run as separate services.
- The app connects to Redis using the hostname `redis` (as set in `docker-compose.yml`).
- Ports:
  - `80:80` maps the app's internal port 80 to your host's port 80.
  - `6379:6379` exposes Redis for debugging (optional; not needed for app to work).
- Data is persisted in the `data/` directory on your host.
- If you change the Redis config, update `data/redirect.config.json` accordingly (e.g., set `"host": "redis"`).

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
  - Or, view/edit `data/redirect.config.json` directly.
  - To view the admin password in Docker, run:
    ```sh
    docker exec redirector cat /app/data/redirect.config.json
    ```
    Look for the `admin_password` field in the output.
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

---

## Upstream Shortcut Existence Checking & Upstream Config

This app supports checking for existing shortcuts in external upstreams (like Bitly, go/, etc.) before allowing creation or editing of a shortcut. This helps prevent conflicts and ensures you don't create a shortcut that already exists in your organization's or a public shortener's namespace.

### How Upstream Checking Works
- When you attempt to create or edit a shortcut, the app checks all configured upstreams to see if the shortcut already exists.
- If any upstream returns a result (i.e., the shortcut exists), you are shown a log of the check and are not allowed to create or edit the shortcut.
- If all upstreams fail (i.e., the shortcut does not exist in any upstream), you are allowed to proceed.
- The check is performed in real time, and a log of each upstream's response (including status code and verdict) is shown in the UI.
- If a shortcut is found in an upstream, you are automatically redirected to that upstream's URL after a short delay.

### Upstream Configuration
- Upstreams are configured in the `data/redirect.config.json` file under the `upstreams` key.
- Each upstream requires:
  - `name`: A label for the upstream (e.g., "bitly", "go")
  - `base_url`: The base URL to check (e.g., `https://bit.ly/`)
  - `fail_url`: The URL that is returned when a shortcut does not exist (used to detect non-existence)
  - `fail_status_code`: The HTTP status code that indicates a failed lookup (e.g., `404`)
- Example config:

```json
"upstreams": [
  {
    "name": "bitly",
    "base_url": "https://bit.ly/",
    "fail_url": "https://bitly.com/404",
    "fail_status_code": 404
  },
  {
    "name": "go",
    "base_url": "http://go/",
    "fail_url": "http://go/404",
    "fail_status_code": 404
  }
]
```

### Managing Upstreams in the UI
- Go to **Upstream Config** in the navigation bar (or visit `/admin/upstreams` after logging in as admin).
- You can add, edit, or delete upstreams using a simple table form.
- Changes are saved to the config file and take effect immediately.

### Real-Time Upstream Check UI
- When you try to create or edit a shortcut, you are first shown a real-time log of upstream checks.
- Each upstream is checked in sequence, and the log updates as results come in.
- If a shortcut is found in any upstream, you are redirected to that URL; otherwise, you are allowed to proceed with creation.

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

## Version & Credits

- See `/version` in the app for live version, commit info, and accessible URLs.
- Created by [@authoritydmc](https://github.com/authoritydmc) and contributors.

---

## License

MIT

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

## Accessing Config Data in a Docker Named Volume (macOS, Windows, Linux)

> **Note:** On macOS (and some environments), Docker named volumes are not directly accessible from the host filesystem. To read or copy config files (like `redirect.config.json`), you need to use an interactive terminal inside the running container.

**Steps:**

1. Find your running container's name (default is `redirector`):
   ```sh
   docker ps
   ```
2. Start an interactive shell in the container:
   ```sh
   docker exec -it redirector sh
   ```
3. View the config file:
   ```sh
   cat /app/data/redirect.config.json
   ```
4. (Optional) Copy the file to your host:
   ```sh
   docker cp redirector:/app/data/redirect.config.json ./redirect.config.json
   ```

This method works on macOS, Windows, and Linux when using Docker named volumes.

---

#### Updating Config in a Running Docker Container

If you want to update the config file inside your running Docker container with a new or edited version from your local machine, you can use the `docker cp` command:

1. Edit your local config file (e.g., `data/redirect.config.json`).
2. Copy it into the running container (replace `redirector` with your container name if different):
   ```sh
   docker cp data/redirect.config.json redirector:/app/data/redirect.config.json
   ```
3. (Optional) Restart the container to ensure the app reloads the new config:
   ```sh
   docker restart redirector
   ```

This will overwrite the config file inside the container with your local version.

---

