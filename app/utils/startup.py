import logging
import platform

from .. import get_port
from ..config import config
logger = logging.getLogger(__name__)
ascii_art = r'''

██████╗ ███████╗██████╗ ██╗██████╗ ███████╗ ██████╗████████╗ ██████╗ ██████╗ 
██╔══██╗██╔════╝██╔══██╗██║██╔══██╗██╔════╝██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗
██████╔╝█████╗  ██║  ██║██║██████╔╝█████╗  ██║        ██║   ██║   ██║██████╔╝
██╔══██╗██╔══╝  ██║  ██║██║██╔══██╗██╔══╝  ██║        ██║   ██║   ██║██╔══██╗
██║  ██║███████╗██████╔╝██║██║  ██║███████╗╚██████╗   ██║   ╚██████╔╝██║  ██║
╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝
                                                                             
'''
os_name = platform.system().lower()
def app_startup_banner(app=None):
    print("\n" + ascii_art) # Log the banner
    logger.info(f"\n   {config.start_mode} - READY 🚀\n")
    logger.info("🌐 URL Shortener & Redirector app initialized.")

    if app is not None:
        logger.info(f"🖥️ Configured to run on port: {get_port()}")
    else:
        logger.info("⚠️ (Port unknown: app not provided)")
    
    # Docker environment and port/network info 🚢🖥️
    
    if config.RUNNING_IN_DOCKER:
        logger.info("🐳 Running inside a Docker container.")
        logger.info("💡 The app listens on the internal container port (default 80) 🎛️.\n"
                    "🌍 To access externally, ensure you map the container port to a host port using '-p <host_port>:80' in Docker 🔄.")
        logger.info("🔗 If using Docker Compose or custom networks, check your port mappings and network mode 🔍.")

    else:
        logger.info("ℹ️ Not running in Docker 🐳. If using Docker, make sure to map ports correctly 🔌.")

        
    # Define OS-specific emojis
    os_emojis = {
        "windows": "🖥️",
        "darwin": "🍏",  # macOS
        "linux": "🐧",
        "unknown": "❓"
    }
    # Get the emoji based on the OS, defaulting to "unknown"
    emoji = os_emojis.get(os_name, os_emojis["unknown"])
    logger.info(f"{emoji} Detected OS: {os_name.capitalize()}")

    # Print Redis status
    if not config.redis_enabled:
        logger.info("🚫 Redis is disabled (see config)")


        # Check if 'r' hostname resolves to localhost
    import socket

    try:
        r_ip = socket.gethostbyname('r')
        if r_ip == '127.0.0.1':
            logger.info("✅ Hostname 'r' resolves to 127.0.0.1 (OK) 🎯")

        else:
            logger.warning(f"⚠️ Hostname 'r' resolves to {r_ip} (not 127.0.0.1) ❌. Check your hosts/DNS setup 🌐.")
            print_os_instruction_on_r_setup()
    except socket.gaierror:  # Specific exception for name resolution failures
        logger.warning("🚨 Hostname 'r' does not resolve ❗. Add '127.0.0.1   r' to your hosts file or set up DNS 📜.")
        print_os_instruction_on_r_setup()
    except Exception as e:
        logger.exception(f"🔥 Unexpected error checking hostname 'r' resolution: {e} 🚑")
        print_os_instruction_on_r_setup()


def print_os_instruction_on_r_setup():
        
    if os_name == "windows":
        logger.info(
            "💻 Run the following command in PowerShell as Administrator:\n"
            "  .\\scripts\\add-r-host-windows.ps1 🚀\n"
            "🔗 Or manually add this line to C:\\Windows\\System32\\drivers\\etc\\hosts:\n"
            "  127.0.0.1   r\n"
        )
    elif os_name == "darwin":
        logger.info(
            "🍏 Run the following command in Terminal:\n"
            "  bash scripts/add-r-host-macos.sh 🏗️\n"
            "✏️ Or manually edit /etc/hosts using:\n"
            "  sudo nano /etc/hosts ✏️\n"
            "Then add this line:\n"
            "  127.0.0.1   r\n"
            "♻️ Run `dscacheutil -flushcache && sudo killall -HUP mDNSResponder` to apply changes.\n"
        )
    elif os_name == "linux":
        logger.info(
            "🐧 Run the following command in Terminal:\n"
            "  bash scripts/add-r-host-linux.sh 🏗️\n"
            "✏️ Or manually edit /etc/hosts using:\n"
            "  sudo nano /etc/hosts ✏️\n"
            "Then add this line:\n"
            "  127.0.0.1   r\n"
        )
    else:
        logger.info("❓ Your OS is not explicitly supported. Please manually update your hosts file:\n")
        logger.info("  🏠 127.0.0.1   r")