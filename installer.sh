#!/usr/bin/env bash

echo "This script is LINUX ONLY, and it's still in testing phases, if you encounter any bugs please open an issue"
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

# Create games.txt if it doesn't exist
if [ ! -e "$(pwd)/games.txt" ]; then
  echo "creating games.txt"
  touch "$(pwd)/games.txt"
fi

# Create icons.txt if it doesn't exist
if [ ! -e "$(pwd)/icons.txt" ]; then
  echo "creating icons.txt"
  touch "$(pwd)/icons.txt"
fi

# Create gameIDs.json if it doesn't exist
if [ ! -e "$(pwd)/customGameIDs.json" ]; then
  echo "creating customGameIDs.json"
  echo "{}" > "$(pwd)/customGameIDs.json"
fi

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

timeout 2.5s ./venv/bin/python ./main.py

echo "Test might've worked, did it spit out any errors?"
echo "Commands executed."

# Replace "/home/deck" with current directory in steam-presence.service file
echo "Setting up service file"
# turn steam-presence/bin/python into steam-presence/venv/bin/python
sed -i "s/steam-presence\/bin\/python/steam-presence\/venv\/bin\/python/g" "$PWD/steam-presence.service"
mkdir -p "$HOME/.config/systemd/user"
sed -e "s~/home/deck/steam-presence~$PWD~g" "$PWD/steam-presence.service" > $HOME/.config/systemd/user/steam-presence.service


echo "Starting service"
systemctl --user daemon-reload
systemctl --user --now enable "steam-presence.service"

echo "If you encountered any errors with this script, please create an issue on the GitHub page"
echo ""
echo "Script completed."
echo "If you ever want to check the status of the script, simply run \"systemctl --user status steam-presence\""
