# Development Guide

This guide will help you set up and run the project for local development on Windows, macOS, or Linux.

---

## 1. Clone the Repository

```sh
git clone <your-repo-url>
cd redirector
```

---

## 2. Python Virtual Environment Setup

### Windows (PowerShell)
```sh
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### macOS/Linux (bash/zsh)
```sh
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3. Install Dependencies

```sh
pip install -r requirements.txt
```

---

## 4. Database Setup & Migration (SQLAlchemy/Alembic)

- By default, the app uses SQLite. The database file is at `data/redirect.db`.
- The database URI is set in `data/redirect.config.json` (edit if needed).

### Initialize/Migrate the Database

```sh
# Make sure you are in the project root and venv is activated
flask db upgrade
```

- If you make changes to models, generate a migration:
```sh
flask db migrate -m "Describe your change"
flask db upgrade
```

---

## 5. Running the App Locally

```sh
python app.py
```
- The app will start on the port specified in `redirect.config.json` (default: 80).
- Visit `http://localhost` in your browser.

---

## 6. Useful Tips
- If you change the database location, ensure the `data/` directory exists and is writable.
- For Redis caching, ensure Redis is running locally (see `redirect.config.json`).
- To reset the database, you can delete `data/redirect.db` and re-run migrations.
- For admin access, the password is in `data/redirect.config.json` under `admin_password`.

---

## 7. Running Tests

```sh
pytest
```

---

## 8. Troubleshooting
- **Database errors:** Ensure the path in `redirect.config.json` is correct and the file is writable.
- **Redis errors:** Make sure Redis is running and the host/port are correct.
- **Module not found:** Ensure your venv is activated and dependencies are installed.

---

Happy coding!
