#!/bin/bash

echo "Uninstalling steam-presence for Linux and macOS. Please confirm you want to continue."
read -p "Press the enter key to continue..."
echo ""

# Detect OS and perform OS-specific uninstall tasks
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
  echo "Stopping and disabling service for Linux"
  systemctl --user stop steam-presence.service
  systemctl --user disable steam-presence.service
  rm "$HOME/.config/systemd/user/steam-presence.service"
  systemctl --user daemon-reload
elif [[ "$OSTYPE" == "darwin"* ]]; then
  echo "Stopping and unloading service for macOS"
  launchctl unload "$HOME/Library/LaunchAgents/com.github.justtemmie.steam-presence.plist"
  rm "$HOME/Library/LaunchAgents/com.github.justtemmie.steam-presence.plist"
else
  echo "Unsupported OS. This uninstall script is designed for Linux and macOS only."
  exit 1
fi

# Remove virtual environment
echo "Removing virtual environment"
rm -rf venv

# Remove wrapper script if on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
  echo "Removing wrapper script"
  rm steam-presence
fi

echo "Uninstallation completed. If you want to remove any other files created by steam-presence, please do so manually."
