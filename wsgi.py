# wsgi.py

import platform
from app import create_app
from app.utils import init_redis_from_config, app_startup_banner

def get_os_name():
    """Detect the operating system and return its name."""
    os_name = platform.system().lower()
    if os_name == "windows":
        return "Windows"
    elif os_name == "darwin":  # macOS is detected as 'Darwin'
        return "macOS"
    elif os_name == "linux":
        return "Linux"
    else:
        return "Unknown OS"

def print_os_instructions(os_name):
    """Print instructions to enable r/ based on detected OS."""
    print("\n==============================")
    print(f"Detected OS: {os_name}")
    print("==============================\n")

    if os_name == "Windows":
        print("Run the following command in PowerShell as Administrator:")
        print("  .\\scripts\\add-r-host-windows.ps1")
        print("Or manually add this line to C:\\Windows\\System32\\drivers\\etc\\hosts:")
        print("  127.0.0.1   r\n")

    elif os_name == "macOS":
        print("Run the following command in Terminal:")
        print("  bash scripts/add-r-host-macos.sh")
        print("Or manually edit /etc/hosts using:")
        print("  sudo nano /etc/hosts")
        print("Then add this line:")
        print("  127.0.0.1   r\n")
        print("Run `dscacheutil -flushcache && sudo killall -HUP mDNSResponder` to apply changes.\n")

    elif os_name == "Linux":
        print("Run the following command in Terminal:")
        print("  bash scripts/add-r-host-linux.sh")
        print("Or manually edit /etc/hosts using:")
        print("  sudo nano /etc/hosts")
        print("Then add this line:")
        print("  127.0.0.1   r\n")

    else:
        print("Your OS is not explicitly supported. Please manually update your hosts file:\n")
        print("  127.0.0.1   r")

# Initialize Redis before app
init_redis_from_config()

# Initialize Flask app
try:
    app = create_app()
except Exception as e:
    import traceback
    print("\n[ERROR] Failed to initialize Flask app.\n")
    traceback.print_exc()
    raise

# Print environment details and host setup tips
app_startup_banner(app)

# Optional: Init DB before Gunicorn takes over
app.init_db()

# Expose app variable for Gunicorn
# Gunicorn will look for: `wsgi:app`
