#!/bin/bash
# Comprehensive fix for Python dependencies and service setup

echo "🔧 Comprehensive Image Sequence Server Fix"
echo "=========================================="

# Stop the service
echo "🛑 Stopping service..."
systemctl stop imgserv

# Go to installation directory
cd /opt/imgserv

# Remove existing virtual environment
echo "🗑️ Removing existing virtual environment..."
rm -rf venv

# Create new virtual environment
echo "🐍 Creating new virtual environment..."
python3 -m venv venv

# Activate and upgrade pip
echo "📦 Upgrading pip..."
source venv/bin/activate
pip install --upgrade pip

# Install dependencies
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Verify installation
echo "✅ Verifying installation..."
python -c "import aiohttp; print('aiohttp installed successfully')"
python -c "import fastapi; print('fastapi installed successfully')"
python -c "import PIL; print('Pillow installed successfully')"

# Set proper ownership
echo "👤 Setting ownership..."
chown -R imgserv:imgserv /opt/imgserv

# Create/update systemd service
echo "⚙️ Updating systemd service..."
cat > /etc/systemd/system/imgserv.service << 'EOF'
[Unit]
Description=Image Sequence Server
After=network.target

[Service]
Type=simple
User=imgserv
Group=imgserv
WorkingDirectory=/opt/imgserv
ExecStart=/opt/imgserv/venv/bin/python /opt/imgserv/main.py
Restart=always
RestartSec=10
EnvironmentFile=/etc/imgserv/.env

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start service
echo "🚀 Starting service..."
systemctl daemon-reload
systemctl enable imgserv
systemctl start imgserv

# Wait and check status
sleep 5
echo "📊 Checking service status..."
if systemctl is-active --quiet imgserv; then
    echo "✅ Service is running successfully!"
    echo "🌐 Web interface: https://localhost:8080"
    echo "📊 Status: systemctl status imgserv"
    echo "📝 Logs: journalctl -u imgserv -f"
else
    echo "⚠️ Service failed to start. Checking logs..."
    journalctl -u imgserv --no-pager -n 20
fi
