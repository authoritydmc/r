# URL Shortener/Redirector [![Docker Image CI](https://github.com/authoritydmc/r/actions/workflows/docker-image.yml/badge.svg)](https://github.com/authoritydmc/r/actions/workflows/docker-image.yml) [![Python package](https://github.com/authoritydmc/r/actions/workflows/python-package.yml/badge.svg)](https://github.com/authoritydmc/r/actions/workflows/python-package.yml)

A modern, self-hostable URL shortener and redirector with a beautiful UI, Docker support, and secure config management. Easily create, manage, and share custom short URLs for your team or company.

---



## Features

- **Modern UI**: Clean, responsive dashboard and success pages using Tailwind CSS and SVG/FontAwesome icons.
- **Config as JSON**: All settings stored in `data/redirect.json.config` (auto-created with secure defaults).
- **Secure by Default**: Random admin password generated on first run.
- **Docker-Ready**: Official image [`rajlabs/redirect`](https://hub.docker.com/r/rajlabs/redirect) with persistent data and easy volume/bind mount support.
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
docker run -d -p 80:80 -v redirect_data:/app/data --name redirect rajlabs/redirect
```
- Data is stored in the Docker-managed volume:
  - **Linux/macOS:** `/var/lib/docker/volumes/redirect_data/_data`
  - **Windows (Docker Desktop):** `\\wsl$\docker-desktop-data\data\docker\volumes\redirect_data\_data` (access via WSL or Docker Desktop's file explorer)

#### Using your current folder (bind mount, recommended for easy access)

```sh
docker run -d -p 80:80 -v "${PWD}/data:/app/data" --name redirect rajlabs/redirect
```
- This will create (or use) a `data` folder in your current directory for persistent config and DB files.
- Works in PowerShell (Windows) and most modern shells. On Linux/macOS, you can use `$(pwd)/data:/app/data` instead.

- Visit: [http://localhost:80](http://localhost:80)
- The app's data directory inside the container is always `/app/data`.
- Admin password is auto-generated on first run (see container logs or the config file in the data folder).

#### Updating

Just pull the latest image and restart:

```sh
docker pull rajlabs/redirect
docker stop redirect && docker rm redirect
# (then re-run the above docker run command)
```

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
