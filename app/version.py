from flask import Blueprint, render_template_string, request, session, redirect, url_for
import subprocess
import socket
from app.utils import get_config, get_port
from functools import wraps

bp_version = Blueprint('version', __name__)

VERSION_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>App Version</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" crossorigin="anonymous" referrerpolicy="no-referrer" />
</head>
<body class="bg-gray-100 min-h-screen flex items-center justify-center">
  <div class="bg-white rounded-lg shadow p-8 w-full max-w-lg">
    <h2 class="text-2xl font-bold mb-4 text-blue-700">App Version</h2>
    <div class="mb-2 text-lg">Version: <span class="font-mono">{{ version }}</span></div>
    <div class="mb-2">Total Commits: <span class="font-mono">{{ commit_count }}</span></div>
    <div class="mb-2">Latest Commit: <span class="font-mono">{{ commit_hash }}</span></div>
    <div class="mb-2">Commit Date: <span class="font-mono">{{ commit_date }}</span></div>
    <div class="mb-4">
      <h3 class="text-xl font-semibold text-blue-600">Accessible URLs:</h3>
      <ul class="list-disc list-inside">
        {% for url in urls %}
        <li class="flex items-center gap-2 mb-1">
          <a href="{{ url }}" target="_blank" rel="noopener noreferrer" class="text-blue-700 hover:underline font-mono flex-1">{{ url }}</a>
          <button onclick="navigator.clipboard.writeText('{{ url }}')" title="Copy URL" class="ml-2 text-gray-500 hover:text-blue-600 focus:outline-none">
            <i class="fa-regular fa-copy"></i>
          </button>
          <a href="{{ url }}" target="_blank" rel="noopener noreferrer" title="Open URL" class="ml-2 text-gray-500 hover:text-green-600">
            <i class="fa-solid fa-arrow-up-right-from-square"></i>
          </a>
        </li>
        {% endfor %}
      </ul>
    </div>
    <div class="mt-6 text-center">
      <a href="/" class="text-blue-600 hover:underline">Back to Dashboard</a>
    </div>
  </div>
</body>
</html>
'''

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

@bp_version.route('/version')
def version_page():
    try:
        commit_count = subprocess.check_output(['git', 'rev-list', '--count', 'HEAD'], encoding='utf-8').strip()
        commit_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], encoding='utf-8').strip()
        commit_date = subprocess.check_output(['git', 'log', '-1', '--format=%cd', '--date=short'], encoding='utf-8').strip()
        version = f"v1.{commit_count}.{commit_hash}"
    except Exception:
        commit_count = commit_hash = commit_date = version = 'unknown'
    port = get_port()
    urls = get_accessible_urls(port)
    return render_template_string(VERSION_TEMPLATE, version=version, commit_count=commit_count, commit_hash=commit_hash, commit_date=commit_date, urls=urls)
