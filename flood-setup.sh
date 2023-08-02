#!/bin/bash

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Check if the script is being run as root (for Linux)
if [ "$(id -u)" -eq 0 ]; then
  SUDO=""
else
  SUDO="sudo"
fi

# Check the operating system
if [ "$(uname)" == "Darwin" ]; then
  # macOS
  if command_exists brew; then
    echo "Homebrew is already installed."
  else
    # Install Homebrew (if not already installed)
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
  fi

  # Install ProxyChains with Homebrew
  $SUDO brew install proxychains-ng

  # Set the PATH for ProxyChains on macOS
  export PATH="/opt/homebrew/Cellar/proxychains-ng/4.16/bin/:$PATH"
elif [ "$(uname)" == "Linux" ]; then
  # Linux (Debian/Ubuntu)
  if command_exists apt; then
    # Update package lists
    $SUDO apt update

    # Install ProxyChains
    $SUDO apt install proxychains
  elif command_exists yum; then
    # Update package lists
    $SUDO yum update

    # Install ProxyChains
    $SUDO yum install proxychains
  else
    echo "Unsupported package manager. Please install ProxyChains manually."
    exit 1
  fi

  # Set the PATH for ProxyChains on Linux
  export PATH="/usr/bin/:$PATH"
else
  echo "Unsupported operating system. Please install ProxyChains manually."
  exit 1
fi

# Make "flood.py" executable
chmod +x flood.py

# Execute Python script "flood.py" (assuming "flood.py" is in the same directory as this script)
# Replace "python" with "python3" if required.
python3 flood.py --help
