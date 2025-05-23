#!/bin/bash
# Add 'r' to /etc/hosts if running as root, else print instructions
if [ "$(id -u)" -eq 0 ]; then
  if ! grep -qE '^127\.0\.0\.1\s+r(\s|$)' /etc/hosts; then
    echo 'Adding 127.0.0.1   r to /etc/hosts...'
    echo '127.0.0.1   r' >> /etc/hosts
    echo 'Added r to /etc/hosts.'
  else
    echo 'r already present in /etc/hosts.'
  fi
else
  echo 'To enable http://r/ shortcuts, add this line to /etc/hosts:'
  echo '127.0.0.1   r'
  echo 'You need sudo/root privileges to edit /etc/hosts.'
fi
