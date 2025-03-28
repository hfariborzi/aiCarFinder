#!/bin/bash

# Install system dependencies for Chrome
apt-get update
apt-get install -y wget gnupg
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list
apt-get update
apt-get install -y google-chrome-stable

# Install Xvfb for virtual display
apt-get install -y xvfb

# Set environment variable to indicate we're on Render
export RENDER=true
