# Changelog

All notable changes to this project will be documented in this file.

## [v1.1.*] - 2025-05-23
- Add audit logging: store created/updated date/time and IP address for each shortcut in the database.
- Show access count, created time, and last updated time on the edit page for each shortcut.
- Do not show IP/logs on the UI; only in the database for audit purposes.
- Maintain access count for every shortcut and display it in the dashboard and edit page.
- Remove JSON-based config; all configuration is now managed via the web UI and stored in the database.
- Add company-wide usage instructions to the README.
- Modernize and improve the web UI and documentation.

## [v1.0.0] - Initial release
- Flask-based URL shortener/redirector with static and dynamic shortcuts, SQLite storage, and web UI.
