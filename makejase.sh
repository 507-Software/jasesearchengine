#!/bin/bash
clear
echo "J.A.S.E. v2.0.0 Installer."
echo "This installer will clone all data from the J.A.S.E. Github and setup the Virtual Enviornment for you."
echo "Have fun while using J.A.S.E."
sleep 5
# Check if git is installed
if ! command -v git &> /dev/null
then
    echo "git could not be found. Please install git."
    exit 1
fi

# Check if python3 is installed
if ! command -v python3 &> /dev/null
then
    echo "python3 could not be found. Please install python3."
    exit 1
fi

# Check if python3-venv is installed
if ! dpkg -l | grep -q python3-venv; then
    echo "python3-venv is not installed. Installing..."
    sudo apt-get update
    sudo apt-get install -y python3-venv
fi

# Remove existing jasesearchengine directory if it exists
if [ -d "jasesearchengine" ]; then
    echo "Removing existing jasesearchengine directory..."
    rm -rf jasesearchengine
fi

# Clone the repository
git clone https://github.com/507-Software/jasesearchengine.git

# Wait for the clone to complete
sleep 10

# Navigate to the project directory
cd jasesearchengine || { echo "Failed to enter directory"; exit 1; }

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install required packages
pip install Flask requests beautifulsoup4 gunicorn

# Deactivate the virtual environment
deactivate

clear

echo "Setup complete. To activate the virtual environment, run 'source venv/bin/activate' in the jasesearchengine directory."
