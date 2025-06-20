from flask import Blueprint, render_template
import subprocess
import socket
from app.utils.utils import  get_port
import requests
from app.CONSTANTS import __version__, get_semver
import logging


bp = Blueprint('version', __name__)

GITHUB_REPO = "authoritydmc/redirector"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

logger = logging.getLogger(__name__)

def get_accessible_urls(port):
    urls = []
    # Localhost
    urls.append(f"http://localhost:{port}/")
    urls.append(f"http://127.0.0.1:{port}/")
    # All local IPs
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        if local_ip not in ('127.0.0.1', 'localhost'):
            urls.append(f"http://{local_ip}:{port}/")
        # All interfaces
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if ip not in ('127.0.0.1', local_ip) and not ip.startswith('169.'):
                urls.append(f"http://{ip}:{port}/")
    except Exception:
        pass
    # Try to get all IPv4 addresses from all interfaces
    try:
        import psutil
        for iface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET and addr.address not in ('127.0.0.1', local_ip):
                    urls.append(f"http://{addr.address}:{port}/")
    except Exception:
        pass
    # Remove duplicates
    return sorted(set(urls))

@bp.route('/version')
def version_page():
    from datetime import datetime
    try:
        commit_count = subprocess.check_output(['git', 'rev-list', '--count', 'HEAD'], encoding='utf-8').strip()
        commit_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], encoding='utf-8').strip()
        commit_date = subprocess.check_output(['git', 'log', '-1', '--format=%cd', '--date=short'], encoding='utf-8').strip()
        semver = get_semver()
    except Exception:
        commit_count = commit_hash = commit_date = semver = 'unknown'
    port = get_port()
    urls = get_accessible_urls(port)
    return render_template('version.html', version=semver, commit_count=commit_count, commit_hash=commit_hash, commit_date=commit_date, urls=urls)

@bp.route('/api/latest-version')
def api_latest_version():
    logger.info("Checking for latest version from GitHub...")
    try:
        resp = requests.get(GITHUB_API_URL, timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            latest = data.get('tag_name') or data.get('name')
            logger.info(f"Version check success: current={get_semver()}, latest={latest}")
            return {'success': True, 'latest': latest, 'current': get_semver()}
        elif resp.status_code == 404:
            logger.warning(f"GitHub API 404: No releases found for {GITHUB_REPO}. You must create a release on GitHub for version check to work. Response: {resp.text}")
            return {'success': False, 'error': 'No releases found on GitHub. Please create a release for version checking.', 'current': get_semver()}
        else:
            logger.warning(f"GitHub API error: status_code={resp.status_code}, text={resp.text}")
            return {'success': False, 'error': f'GitHub API error: {resp.status_code}', 'current': get_semver()}
    except Exception as e:
        logger.error(f"Error checking latest version: {e}", exc_info=True)
        return {'success': False, 'error': str(e), 'current': get_semver()}
