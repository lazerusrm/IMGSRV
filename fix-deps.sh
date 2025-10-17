#!/bin/bash
# Quick fix for missing Python dependencies
# Run this to fix the current installation

echo "🔧 Fixing Python dependencies..."

# Stop the service
systemctl stop imgserv

# Go to the installation directory
cd /opt/imgserv

# Activate virtual environment and install dependencies
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Set proper ownership
chown -R imgserv:imgserv /opt/imgserv

# Start the service
systemctl start imgserv

# Check status
sleep 3
if systemctl is-active --quiet imgserv; then
    echo "✅ Service is now running!"
    echo "🌐 Web interface: https://localhost:8080"
else
    echo "⚠️ Service may still have issues, check with: systemctl status imgserv"
fi
