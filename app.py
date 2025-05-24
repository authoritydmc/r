import platform
import argparse
from app import create_app

try:
    app = create_app()
except Exception as e:
    import traceback
    print("\n[ERROR] Failed to initialize Flask app.\n")
    traceback.print_exc()
    raise

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Run Flask in debug mode")
    args = parser.parse_args()
    mode = "DEV" if args.debug else "PROD"

    ascii_art = r''' _______  _______  ______  _________ _______  _______  _______ _________ _______  _______ 
(  ____ )(  ____ \(  __  \ \__   __/(  ____ )(  ____ \(  ____ \\__   __/(  ___  )(  ____ )
| (    )|| (    \/| (  \  )   ) (   | (    )|| (    \/| (    \/   ) (   | (   ) || (    )|
| (____)|| (__    | |   ) |   | |   | (____)|| (__    | |         | |   | |   | || (____)|
|     __)|  __)   | |   | |   | |   |     __)|  __)   | |         | |   | |   | ||     __)
| (\ (   | (      | |   ) |   | |   | (\ (   | (      | |         | |   | |   | || (\ (   
| ) \ \__| (____/\| (__/  )___) (___| ) \ \__| (____/\| (____/\   | |   | (___) || ) \ \__
|/   \__/(_______/(______/ \_______/|/   \__/(_______/(_______/   )_(   (_______)|/   \__/
'''

    print(ascii_art)
    print(f"==============================\n   RUNNING IN {mode} MODE\n==============================")
    print("URL Shortener & Redirector starting up...")
    print(f"Running on port: {app.config['port']}")
    
    # Detect OS and print instructions
    os_name = get_os_name()
    print_os_instructions(os_name)

    print("\n==============================\n")
    app.init_db()
    app.run(debug=args.debug, host="0.0.0.0", port=app.config['port'])
