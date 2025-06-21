# URL Shortener/Redirector

A modern, self-hostable URL shortener and redirector with a beautiful UI, Docker support, Redis in-memory cache, and robust config management. Easily create, manage, and share custom short URLs for your team or company.

---

## Table of Contents
- [Features](#features)
- [Quick Start](#quick-start)
  - [Docker (Prebuilt Image, Recommended)](#docker-prebuilt-image-recommended)
  - [Docker Compose](#docker-compose)
  - [Manual (Python)](#manual-python)
- [Configuration](#configuration)
- [Database URI Construction Guide](#database-uri-construction-guide)
- [Data Persistence](#data-persistence)
- [Reverse Proxy Example (Nginx)](#reverse-proxy-example-nginx)
- [Upstream Shortcut Checking & Integration](#upstream-shortcut-checking--integration)
- [Admin Config & UI Improvements](#admin-config--ui-improvements)
- [Production Deployment](#production-deployment)
- [Development & Testing](#development--testing)
- [Project Structure](#project-structure)
- [Company-Wide Installation & Team Usage](#company-wide-installation--team-usage)
- [Performance & Optimization](#performance--optimization)
- [Import/Export & Upstream Cache Management](#importexport--upstream-cache-management)
- [Version & Credits](#version--credits)
- [License](#license)

---

## Features

- **Production-ready Docker image**: [`rajlabs/redirector`](https://hub.docker.com/r/rajlabs/redirector) for instant deployment.
- **Redis in-memory cache**: Ultra-fast shortcut and upstream cache lookups for low-latency redirects.
- **Upstream shortcut caching**: Successful upstream lookups are cached in both SQLite and Redis (if enabled) for instant future redirects.
- **Configurable upstream cache**: Enable/disable via `redirect.config.json` (`"upstream_cache": { "enabled": true }`), default enabled.
- **Modern admin UI**: View, resync, and purge upstream cache entries with a beautiful, responsive, and dark-mode-ready interface.
- **Resync All** and **Purge All** actions for upstream cache, with robust error handling and double confirmation for purging.
- **Consistent redirect logic**: Upstream cache hits use the same redirect/delay logic as local shortcuts, including countdown and stats.
- **Audit & Stats**: Tracks access count, creation/update times, and IPs for each shortcut.
- **Dynamic Shortcuts**: Supports static and dynamic (parameterized) redirects.
- **Version Info**: `/version` page shows live version, commit info, and all accessible URLs (with copy/open buttons).

---

## Quick Start

### Docker (Prebuilt Image, Recommended)

#### With Redis (Best Performance)

Start Redis (if you don't have it running):

```sh
docker run -d --name redis --restart unless-stopped -p 6379:6379 redis:7.2-alpine
```

Then run the app, linking to Redis:

```sh
docker run -d --name redirector --restart unless-stopped -p 80:80 -v $PWD/data:/app/data -e REDIS_HOST=redis -e REDIS_PORT=6379 --link redis:redis rajlabs/redirector
```

- Data is stored in the `data/` folder on your host and mounted into the app container.
- The app will connect to Redis at `redis:6379`.
- The config file is `data/redirect.config.json`.

#### Without Redis (slower, but works)

```sh
docker run -d --name redirector --restart unless-stopped -p 80:80 -v $PWD/data:/app/data rajlabs/redirector
```

#### With a Host Directory (custom location)

```sh
docker run -d --name redirector --restart unless-stopped -p 80:80 -v /absolute/path/to/your/data:/app/data -e REDIS_HOST=redis -e REDIS_PORT=6379 --link redis:redis rajlabs/redirector
```

Replace `/absolute/path/to/your/data` with your desired directory.

#### 🚀 **Recommended: With Named Volume (Best for Upgrades & Backups)**

```sh
# Create a persistent named volume (only once)
docker volume create redirector_data

# Run the app with Redis (best performance)
docker run -d --name redirector --restart unless-stopped -p 80:80 -v redirector_data:/app/data -e REDIS_HOST=redis -e REDIS_PORT=6379 --link redis:redis rajlabs/redirector
```

> **Recommended:** Using a Docker named volume (`redirector_data`) keeps your data safe and makes upgrades and backups easy.

---

### Docker Compose

A `docker-compose.yml` is provided for easy setup with Redis:

```sh
docker compose up --build
```

- This will build and start two containers:
  - `app`: Gunicorn + Flask URL shortener/redirector (port 80)
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

---

### Manual (Python)

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

All configuration is managed in the `data/redirect.config.json` file (auto-created if missing). Here is a breakdown of each option:

```json
{
  "port": 80, // Port the app listens on (default: 80)
  "auto_redirect_delay": 300, // Delay (in seconds) before auto-redirect (0 = instant)
  "admin_password": "...", // Admin password (randomly generated on first run)
  "delete_requires_password": true, // Require password to delete shortcuts (recommended: true)
  "upstreams": [ // List of upstream redirectors to check for existing shortcuts
    {
      "name": "bitly", // Name/label for the upstream
      "base_url": "https://go.dev", // Base URL for upstream shortcut checks
      "fail_url": "", // URL returned by upstream when shortcut does not exist (leave blank if not used)
      "fail_status_code": 200 // HTTP status code indicating a failed lookup (e.g., 404 for not found)
    }
  ],
  "redis": {
    "enabled": true, // Enable Redis for in-memory caching (recommended for performance)
    "host": "localhost", // Redis server hostname (use 'redis' for Docker Compose)
    "port": 6379 // Redis server port
  },
  "upstream_cache": {
    "enabled": true // Enable upstream shortcut caching (recommended)
  },
  "database":"sqlite:///data/redirects.db"  //uri for database 
}
```

**Key fields:**
- `port`: The port the app will listen on. Change if you want to run on a different port.
- `auto_redirect_delay`: Number of seconds to wait before redirecting. Set to 0 for instant redirect.
- `admin_password`: The admin password for the web UI. Auto-generated if not set.
- `delete_requires_password`: If true, deleting a shortcut requires the admin password.
- `upstreams`: List of upstream redirectors (e.g., Bitly, go/). Each must have a `name`, `base_url`, and optionally `fail_url` and `fail_status_code` to detect non-existent shortcuts.
- `redis`: Redis config. Set `enabled` to true for best performance. Use `host: redis` in Docker Compose, or `localhost` for local testing.
- `upstream_cache`: Set `enabled` to true to cache successful upstream lookups for fast future redirects.
- `database` : Set `database` uri , read more [here](#database-uri-construction-guide)

You can edit this file directly or use the admin UI for most settings. Changes take effect immediately after saving the file or restarting the app/container.

---

# **Database URI Construction Guide**

This guide explains how to format database connection URIs dynamically for **SQLite, PostgreSQL, and MySQL**.

---

## **1️⃣ Understanding Database URI Format**
A database connection URI follows this general structure:

```
dialect+driver://username:password@host:port/database
```

### **Key Components**
- **dialect** → Type of database (`sqlite`, `postgresql`, `mysql`)
- **driver** → Connection adapter (`pymysql`, `psycopg2`, etc.)
- **username/password** → Authentication credentials
- **host** → Database server location (`localhost`, IP, or domain)
- **port** → Connection port (`5432` for PostgreSQL, `3306` for MySQL)
- **database** → Name or file path (for SQLite)

---

## **2️⃣ Example Database URIs for Different Databases**

### **🔹 SQLite (Local File-Based Database)**
SQLite doesn’t require authentication:
```sh
sqlite:///absolute/path/to/database.db
```
For relative paths:
```sh
sqlite:///data/mydatabase.db  # Stored inside 'data' folder
```

### **🔹 PostgreSQL (Production-Grade Database)**
Use PostgreSQL with credentials:
```sh
postgresql+psycopg2://user:password@localhost:5432/mydatabase
```
For a remote PostgreSQL server:
```sh
postgresql+psycopg2://user:password@db.example.com:5432/mydatabase
```

### **🔹 MySQL (Popular Web Database)**
Use MySQL with authentication:
```sh
mysql+pymysql://user:password@localhost:3306/mydatabase
```
For a remote MySQL instance:
```sh
mysql+pymysql://user:password@db.example.com:3306/mydatabase
```

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

## Upstream Shortcut Checking & Integration

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

## Admin Config & UI Improvements

WIP

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
- By default, `python app.py` runs in debug mode (debug=True). Use `--prod` for production. Docker is run with Gunicorn and gevent (PRODUCTION READY WSGI Servers)

---

## Development & Testing

To run all tests for this app, use the following command from the project root:

```sh
python -m pytest tests --maxfail=2 --disable-warnings -v
```

If you see an error like `No module named pytest`, install pytest first:

```sh
pip install pytest
```

> **Note:**
> - Always run tests from the project root directory.
> - If you get import/module errors with `pytest`, use `python -m pytest` instead. This ensures Python uses the correct module path, especially on Windows or in virtual environments.

- To lint the code:

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

## Performance & Optimization

- **Efficient Session Management:**
  The app uses Flask-SQLAlchemy for automatic session handling. For custom scripts or background jobs, ensure sessions are closed after use to prevent leaks.

- **Bulk Operations:**
  For admin actions like cache resync or log purging, the backend uses SQLAlchemy's bulk methods for efficient database writes.

- **Query Optimization:**
  Frequently queried fields (like `pattern` and `upstream_name`) are indexed for fast lookups. Only necessary columns are fetched in large queries to reduce memory usage.

- **Connection Pooling:**
  When using PostgreSQL or MySQL, SQLAlchemy's connection pooling is enabled for high concurrency. You can tune pool size and timeout in your database URI if needed.

- **Redis Caching:**
  If enabled, Redis is used for ultra-fast shortcut and upstream cache lookups. The app uses specific cache keys and sets expiration to avoid stale data.

- **Robust Error Handling:**
  All database and cache operations are wrapped in try/except blocks with detailed logging for easy troubleshooting.

- **Template Rendering:**
  Only required fields are passed to templates, improving rendering speed and reducing memory footprint.

- **Testing:**
  The test suite uses isolated transactions to keep test data separate from production.

**Recommended for Production:**
- Use Docker or Gunicorn for serving the app.
- Enable Redis for best performance.
- Use PostgreSQL or MySQL for large-scale/team deployments.
- Regularly backup your `data/` directory (contains config and DB).

---

## Import/Export & Upstream Cache Management

- **Import/Export:** Importing redirects from JSON will NOT delete your existing redirects. Instead, it will upsert (insert or update) each redirect by pattern, and only update if the imported `updated_at` is newer than the existing one.
- **Upstream Cache:** You can now purge (delete) individual upstream cache entries directly from the UI, as well as purge all entries for an upstream. This helps keep your cache clean and up-to-date.

---

## Version & Credits

- See `/version` in the app for live version, commit info, and accessible URLs.
- Created by [@authoritydmc](https://github.com/authoritydmc) and contributors.

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

> **For local development, setup, and migration instructions, see [`DEVELOPMENT.md`](DEVELOPMENT.md).**

---
## Automated Release Tagging (Windows)

To automate the process of tagging a new release and triggering the GitHub Actions release workflow, use the provided PowerShell script:

### Usage

1. **Ensure your changes are committed and pushed.**
2. Open PowerShell in the project root directory.
3. Run:

```powershell
pwsh scripts/create-release-tag.ps1 -Version v1.2.3
```

- Replace `v1.2.3` with your desired version tag (must start with `v`).
- If you omit `-Version`, the script will prompt you to enter one interactively.
- The script will:
  - Check if the tag exists
  - Create the tag
  - Push it to `origin`
  - Trigger the GitHub Actions release workflow (if configured)

> **Note:** Tagging is required for the GitHub release workflow to succeed. See [VERSIONING.md](VERSIONING.md) for versioning details.

---

