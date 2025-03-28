#!/bin/bash

# Install system dependencies for Chrome
apt-get update
apt-get install -y wget gnupg unzip xvfb

# Install Chrome
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list
apt-get update
apt-get install -y google-chrome-stable

# Make sure Chrome is in PATH
export PATH=$PATH:/usr/bin/google-chrome-stable
echo "export PATH=$PATH:/usr/bin/google-chrome-stable" >> ~/.bashrc

# Install ChromeDriver directly
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d. -f1)
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION")
wget -q "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"
unzip chromedriver_linux64.zip
mv chromedriver /usr/local/bin/
chmod +x /usr/local/bin/chromedriver

# Set environment variable to indicate we're on Render
export RENDER=true
echo "export RENDER=true" >> ~/.bashrc

# Print versions for debugging
echo "Chrome version:"
google-chrome --version
echo "ChromeDriver version:"
chromedriver --version
