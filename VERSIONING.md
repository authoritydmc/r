# Versioning for URL Shortener/Redirector

The current version is tracked by git commit count and hash. For frontend version checks, the backend exposes `/api/latest-version` (fetches latest GitHub release tag) and `/version` (shows current commit info).

To display the current version in the footer and check for updates:
- The frontend should fetch `/api/latest-version` and compare with the current version (commit count/hash or a static version string if available).
- If a newer version is available, show an upgrade notice in the footer.

If you want to set a static version string, add a `__version__` variable in `app/__init__.py` or `app/CONSTANTS.py` and update it on each release. Otherwise, the app uses git commit info for versioning.
