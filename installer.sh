#!/bin/bash

echo "This script is LINUX ONLY, and it's still in testing phases, if you encounter any bugs please open an issue"
read -p "Press the enter key to continue..."
echo ""


# Check if script is running as root
if [ "$(id -u)" == "0" ]; then
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

# Create steam-presence folder if it does not exist
if [ ! -d "$HOME/steam-presence" ]; then
  mkdir -p "$HOME/steam-presence"
fi

echo "Creating symlinks of necessary files..."

# Create games.txt if it doesn't exist
if [! -e "$(pwd)/games.txt" ]; then
  echo "creating games.txt"
  touch "$(pwd)/games.txt"
fi

# Create icons.txt if it doesn't exist
if [! -e "$(pwd)/icons.txt" ]; then
  echo "creating icons.txt"
  touch "$(pwd)/icons.txt"
fi

# Create gameIDs.json if it doesn't exist
if [! -e "$(pwd)/customGameIDs.json" ]; then
  echo "creating customGameIDs.json"
  echo "{}" > "$(pwd)/customGameIDs.json"
fi


# Create symlinks of necessary files
ln -s "$(pwd)/main.py" "$HOME/steam-presence/main.py"
ln -s "$(pwd)/requirements.txt" "$HOME/steam-presence/requirements.txt"
ln -s "$(pwd)/steam-presence.service" "$HOME/steam-presence/steam-presence.service"
ln -s "$(pwd)/config.json" "$HOME/steam-presence/config.json"
ln -s "$(pwd)/games.txt" "$HOME/steam-presence/games.txt"
ln -s "$(pwd)/icons.txt" "$HOME/steam-presence/icons.txt"
ln -s "$(pwd)/customGameIDs.json" "$HOME/steam-presence/customGameIDs.json"

echo "Symlinks created."

# Change to steam-presence directory
cd "$HOME/steam-presence"

echo "Executing commands in steam-presence directory..."

# Execute commands in steam-presence directory
python3 -m venv .
./bin/python -m pip install --upgrade pip wheel
./bin/python -m pip install -r requirements.txt

echo ""
echo "Testing if the script works"
echo ""

timeout 2.5s ./bin/python ./main.py

echo "Test might've worked, did it spit out any errors?"
echo "Commands executed."

# Replace "deck" user with local username in steam-presence.service file
echo "Editing service file"
local_username=$(whoami)
sed -i "s/deck/$local_username/g" "$HOME/steam-presence/steam-presence.service"

echo "Starting service"
systemctl --user --now enable "$HOME/steam-presence/steam-presence.service"

echo "If you encountered any errors with this script, please create an issue on the GitHub page"
echo ""
echo "Script completed."
echo "If you ever want to check the status of the script, simply run \"systemctl --user status steam-presence\""
