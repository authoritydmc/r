# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]
### Added
- Upstream shortcut caching: successful upstream lookups are now cached in both SQLite and Redis (if enabled) for fast, low-latency redirects.
- Configurable upstream cache: enable/disable via `redirect.config.json` (`"upstream_cache": { "enabled": true }`), defaulting to enabled.
- Admin UI for viewing, resyncing, and purging upstream cache entries, with modern, responsive design and dark mode support.
- "Resync All" and "Purge All" actions for upstream cache, with robust error handling and double confirmation for purging.
- Gunicorn support for production: faster, multi-worker serving out of the box.
- Improved error diagnostics and logging for all cache and upstream operations.
- All admin and cache management endpoints now return valid JSON and robust error feedback.

### Changed
- Redirect route now uses upstream cache hits with the same logic as local shortcut hits (including delay and redirect template).
- Upstream and cache admin pages redesigned for modern, visually-contained, and mobile-friendly experience.
- Improved backend and UI error handling for all cache and upstream management actions.

### Fixed
- Route import and endpoint registration issues for upstream cache management.
- All endpoints now robustly handle errors and return valid JSON.
- UI feedback for resync and purge actions is now clear and actionable.

### Performance
- Redis is now used for in-memory, low-latency cache of both local and upstream shortcuts (if enabled).
- Gunicorn is recommended for production for high concurrency and speed.

---

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

## [Unreleased] - 2025-06-21
### Added
- Modal summary before saving admin config changes, with confirm/cancel.
- WIP badge and flask icon on admin config page and nav bar.
- Animated chevron and click-only admin tools dropdown, fully keyboard accessible.
### Changed
- Config save logic: config is reloaded and all dependent attributes updated after save.
- Config change detection now uses deep equality for booleans/objects, so unchanged values do not trigger the confirm modal.
### Fixed
- Admin tools dropdown no longer blocks the "New Shortcut" button.
- Improved text color for config summary modal in dark mode.
