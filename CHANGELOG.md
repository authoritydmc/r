# Changelog

All notable changes to this project will be documented in this file.

### Added
- Accessible URLs on /version page are now clickable, copyable (with button), and have open-in-new-tab icons (FontAwesome).
- Modernized all UI with Tailwind CSS and SVG/FontAwesome icons.
- Config is now stored in `data/redirect.config.json` (JSON), not the DB. File is auto-created with secure defaults (random admin password).
- Database path is now `data/redirects.db`, with directory auto-creation for cross-platform and Docker compatibility.
- Docker instructions updated: use `rajlabs/redirect` image, with clear volume/bind mount and data location notes.
- Startup prints info about Docker port mapping, data persistence, and best practices.
- Success page for shortcut creation uses Tailwind CSS for a modern, user-friendly look.
- `/version` page now shows clickable/copyable URLs with icons, and version info is generated in the route.
- Fixed test teardown issues and ensured tests work cross-platform.
- Updated GitHub Actions workflow for multiple image names and correct env usage.
- README and UI now provide clear, actionable deployment and troubleshooting info.

### Changed
- All configuration and admin password handling is now file-based and secure by default.
- Improved feedback and error handling throughout the app.
- Enhanced Docker and reverse proxy support and documentation.

### Fixed
- ImportError for `__version__` in version route (now generated dynamically).
- Test teardown and cross-platform issues in test suite.

## [v1.1.0] - 2025-05-23
- Add audit logging: store created/updated date/time and IP address for each shortcut in the database.
- Show access count, created time, and last updated time on the edit page for each shortcut.
- Do not show IP/logs on the UI; only in the database for audit purposes.
- Maintain access count for every shortcut and display it in the dashboard and edit page.
- Remove JSON-based config; all configuration is now managed via the web UI and stored in the database.
- Add company-wide usage instructions to the README.
- Modernize and improve the web UI and documentation.

## [v1.0.0] - Initial release
- Flask-based URL shortener/redirector with static and dynamic shortcuts, SQLite storage, and web UI.
