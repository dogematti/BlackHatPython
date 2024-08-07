##OH Dogematti's done it again :D
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
  echo 'export PATH="/opt/homebrew/Cellar/proxychains-ng/4.16/bin:$PATH"' >> ~/.zshrc
  export PATH="/opt/homebrew/Cellar/proxychains-ng/4.16/bin:$PATH"

  # Add the alias for macOS
  echo 'alias proxy_flood="proxychains4 python3 flood.py"' >> ~/.zshrc

  # Make "flood.py" executable
  chmod +x flood.py

  # Reload the shell configuration
  source ~/.zshrc
elif [ "$(uname)" == "Linux" ]; then
  # Linux (Debian/Ubuntu)
  if command_exists apt; then
    # Update package lists
    $SUDO apt update

    # Install ProxyChains
    $SUDO apt install -y proxychains
  elif command_exists yum; then
    # Update package lists
    $SUDO yum update

    # Install ProxyChains
    $SUDO yum install -y proxychains
  else
    echo "Unsupported package manager. Please install ProxyChains manually."
    exit 1
  fi

  # Set the PATH for ProxyChains on Linux
  echo 'export PATH="/usr/bin:$PATH"' >> ~/.bashrc
  export PATH="/usr/bin:$PATH"

  # Add the alias for Linux
  echo 'alias proxy_flood="proxychains python3 flood.py"' >> ~/.bashrc

  # Make "flood.py" executable
  chmod +x flood.py

  # Reload the shell configuration
  source ~/.bashrc
else
  echo "Unsupported operating system. Please install ProxyChains manually."
  exit 1
fi

# Confirm completion
echo "Installation completed successfully. ProxyChains added to PATH and alias set."
