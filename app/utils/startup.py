import logging

from ..config import config
logger = logging.getLogger(__name__)

def app_startup_banner(app=None):
    import platform
    ascii_art = r''' _______  _______  ______  _________ _______  _______  _______ _________ _______  _______
(  ____ )(  ____ \\  __  \\ \__   __/(  ____ )(  ____ \\  ____ \\__   __/(  ___  )(  ____ )
| (    )|| (    \/| (  \  )   ) (   | (    )|| (    \/| (    \/   ) (   | (   ) || (    )|
| (____)|| (__    | |   ) |   | |   | (____)|| (__    | |         | |   | |   | || (____)|
|     __)|  __)   | |   | |   | |   |     __)|  __)   | |         | |   | |   | ||     __)
| (\ (   | (      | |   ) |   | |   | (\ (   | (      | |         | |   | |   | || (\ (
| ) \ \__| (____/\\| (__/  )___) (___| ) \ \__| (____/\\| (____/\\   | |   | (___) || ) \ \__
|/   \__/(_______/(______/ \_______/|/   \__/(_______/(_______/   )_(   (_______)|/   \__/

'''
    print("\n" + ascii_art) # Log the banner
    logger.info(f"==============================\n   {config.start_mode} - READY\n==============================")
    logger.info("URL Shortener & Redirector app initialized.")
    if app is not None:
        logger.info(f"Configured to run on port: {app.config.get('port', 'unknown')}")
    else:
        logger.info("(Port unknown: app not provided)")
    # Detect OS and print instructions for host file entry
    os_name = platform.system().lower()
    logger.info("\n==============================")
    logger.info(f"Detected OS: {os_name.capitalize()}")
    logger.info("==============================\n")
    if os_name == "windows":
        logger.info(
            "Run the following command in PowerShell as Administrator:\n"
            "  .\\scripts\\add-r-host-windows.ps1\n"
            "Or manually add this line to C:\\Windows\\System32\\drivers\\etc\\hosts:\n"
            "  127.0.0.1   r\n"
        )
    elif os_name == "darwin":
        logger.info(
            "Run the following command in Terminal:\n"
            "  bash scripts/add-r-host-macos.sh\n"
            "Or manually edit /etc/hosts using:\n"
            "  sudo nano /etc/hosts\n"
            "Then add this line:\n"
            "  127.0.0.1   r\n"
            "Run `dscacheutil -flushcache && sudo killall -HUP mDNSResponder` to apply changes.\n"
        )
    elif os_name == "linux":
        logger.info(
            "Run the following command in Terminal:\n"
            "  bash scripts/add-r-host-linux.sh\n"
            "Or manually edit /etc/hosts using:\n"
            "  sudo nano /etc/hosts\n"
            "Then add this line:\n"
            "  127.0.0.1   r\n"
        )

    else:
        logger.info("Your OS is not explicitly supported. Please manually update your hosts file:\n")
        logger.info("  127.0.0.1   r")
    # Print Redis status
    if not config.redis_enabled:
        logger.info("Redis is disabled (see config)")

    # Check if 'r' hostname resolves to localhost
    import socket
    try:
        r_ip = socket.gethostbyname('r')
        if r_ip == '127.0.0.1':
            logger.info("Hostname 'r' resolves to 127.0.0.1 (OK)")
        else:
            logger.warning(f"Hostname 'r' resolves to {r_ip} (not 127.0.0.1). Check your hosts/DNS setup.")
    except socket.gaierror: # Specific exception for name resolution failures
        logger.warning("Hostname 'r' does not resolve. Add '127.0.0.1   r' to your hosts file or set up DNS.")
    except Exception as e:
        logger.exception(f"Unexpected error checking hostname 'r' resolution: {e}")


    # Docker environment and port/network info

    if config.RUNNING_IN_DOCKER:
        logger.info("[INFO] Running inside a Docker container.")
        logger.info("      The app listens on the internal container port (default 80).\n      To access externally, ensure you map the container port to a host port using '-p <host_port>:80' in Docker.")
        logger.info("      If using Docker Compose or custom networks, check your port mappings and network mode.")
    else:
        logger.info("Not running in Docker. If using Docker, make sure to map ports correctly.")
