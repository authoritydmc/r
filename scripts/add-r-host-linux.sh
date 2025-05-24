#!/bin/bash
# Add 'r' to /etc/hosts if running as root, else print instructions

hostsPath="/etc/hosts"
entry="127.0.0.1   r"

if [ "$(id -u)" -eq 0 ]; then
    if ! grep -qw "127.0.0.1 r" "$hostsPath"; then
        echo "Adding $entry to $hostsPath..."
        echo "$entry" | sudo tee -a "$hostsPath" > /dev/null
        echo "Added 'r' to $hostsPath."
    else
        echo "'r' is already present in $hostsPath."
    fi
else
    echo "To enable http://r/ shortcuts, add this line manually to $hostsPath:"
    echo "$entry"
    echo "You need sudo/root privileges to edit $hostsPath."
fi
