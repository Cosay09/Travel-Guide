#!/bin/bash

echo "Installing project requirements..."
echo

python3 -m pip install --upgrade pip
python3 -m pip install customtkinter Pillow reportlab geopy

echo
echo "All requirements installed successfully."

#This script can be run using the following commands:
#chmod +x install_requirements.sh
#./install_requirements.sh
