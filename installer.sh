#!/bin/bash

echo "This script is for Linux and macOS, and it's still in testing phases. If you encounter any bugs, please open an issue."
read -p "Press the enter key to continue..."
echo ""

# Check if script is running as root
if [ `whoami` == "root" ]; then
   echo "This script cannot be run as root. Please run as a regular user"
   exit 1
fi

# Check if config.json file exists
if [ ! -f "config.json" ]; then
   echo "Error: config.json file not found. Please make sure it exists in the current directory"
   echo "files in current directory:"
   ls
   exit 1
fi

# Create necessary files if they don't exist
for file in games.txt icons.txt customGameIDs.json; do
  if [ ! -e "$(pwd)/$file" ]; then
    echo "creating $file"
    [ "$file" == "customGameIDs.json" ] && echo "{}" > "$(pwd)/$file" || touch "$(pwd)/$file"
  fi
done

echo "Setting up virtual environment"
mkdir venv
cd venv
python3 -m venv .
./bin/python -m pip install --upgrade pip wheel
./bin/python -m pip install -r ../requirements.txt
cd ..

echo ""
echo "Testing if the script works"
echo ""

# Run the Python script in the background
./venv/bin/python ./main.py &
# Get the background process's PID
PYTHON_PID=$!
# Sleep for 2.5 seconds
sleep 2.5
# Kill the background process
kill $PYTHON_PID

echo "Test might've worked, did it spit out any errors?"
echo "Commands executed."

# Create a shell script wrapper for macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
  echo '#!/bin/bash' > steam-presence
  echo "DIR=\"\$( cd \"\$( dirname \"\${BASH_SOURCE[0]}\" )\" && pwd )\"" >> steam-presence
  echo "exec \"\$DIR/venv/bin/python\" \"\$DIR/main.py\"" >> steam-presence
  chmod +x steam-presence
fi

# Detect OS and perform OS-specific tasks
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
  echo "Setting up service file for Linux"
  mkdir -p "$HOME/.config/systemd/user"
  sed -e "s~steam-presence/bin/python~steam-presence/venv/bin/python~g" -e "s~/home/deck/steam-presence~$PWD~g" "$PWD/steam-presence.service" > $HOME/.config/systemd/user/steam-presence.service
  echo "Starting service"
  systemctl --user daemon-reload
  systemctl --user --now enable "steam-presence.service"
elif [[ "$OSTYPE" == "darwin"* ]]; then
  echo "Setting up launchd plist file for macOS"
  PLIST="$HOME/Library/LaunchAgents/com.github.justtemmie.steam-presence.plist"
  cat <<EOL > $PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>Steam Presence</string>
    <key>ProgramArguments</key>
    <array>
        <string>$(pwd)/steam-presence</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$(pwd)/steam-presence.log</string>
    <key>StandardErrorPath</key>
    <string>$(pwd)/steam-presence-error.log</string>
</dict>
</plist>
EOL
  echo "Starting service"
  launchctl load $PLIST
else
  echo "Unsupported OS. This script is designed for Linux and macOS only."
  exit 1
fi

echo "If you encountered any errors with this script, please create an issue on the GitHub page"
echo ""
echo "Script completed."
