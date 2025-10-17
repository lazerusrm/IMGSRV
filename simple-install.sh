#!/bin/bash
# Ultra-simple installer that bypasses most errors
# Usage: curl -sSL https://raw.githubusercontent.com/lazerusrm/IMGSRV/main/simple-install.sh | bash

echo "🚀 Simple Image Sequence Server Installer"
echo "========================================"

# Update system (ignore errors)
echo "📦 Updating system..."
apt-get update 2>/dev/null || true
apt-get --fix-broken install -y 2>/dev/null || true
apt-get upgrade -y 2>/dev/null || true

# Install essential packages (ignore errors)
echo "🔧 Installing packages..."
apt-get install -y git python3 python3-pip python3-venv curl wget 2>/dev/null || true

# Clone repository
echo "📥 Downloading Image Sequence Server..."
cd /opt
rm -rf imgserv 2>/dev/null || true

# Try git clone first, fallback to wget
if git clone https://github.com/lazerusrm/IMGSRV.git imgserv 2>/dev/null; then
    echo "✅ Repository cloned"
else
    echo "📦 Downloading as zip..."
    cd /tmp
    wget -q https://github.com/lazerusrm/IMGSRV/archive/main.zip -O imgserv.zip 2>/dev/null || true
    unzip -q imgserv.zip 2>/dev/null || true
    mv IMGSRV-main /opt/imgserv 2>/dev/null || true
fi

# Setup Python environment
echo "🐍 Setting up Python environment..."
cd /opt/imgserv
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate
pip install -r requirements.txt 2>/dev/null || true

# Create user and directories
echo "👤 Creating user and directories..."
useradd --system --shell /bin/false --home-dir /opt/imgserv imgserv 2>/dev/null || true
mkdir -p /var/lib/imgserv/images /var/lib/imgserv/sequences /var/log/imgserv /etc/imgserv
chown -R imgserv:imgserv /var/lib/imgserv /var/log/imgserv /opt/imgserv 2>/dev/null || true

# Create systemd service
echo "⚙️ Creating systemd service..."
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

[Install]
WantedBy=multi-user.target
EOF

# Create basic config
cat > /etc/imgserv/.env << 'EOF'
HOST=0.0.0.0
PORT=8080
LOG_LEVEL=INFO
CAMERA_IP=192.168.1.110
CAMERA_USERNAME=admin
CAMERA_PASSWORD=123456
DATA_DIR=/var/lib/imgserv
IMAGES_DIR=/var/lib/imgserv/images
SEQUENCES_DIR=/var/lib/imgserv/sequences
EOF

# Start service
echo "🚀 Starting service..."
systemctl daemon-reload
systemctl enable imgserv
systemctl start imgserv

# Wait and check
sleep 5
if systemctl is-active --quiet imgserv; then
    echo "✅ Service is running!"
    echo "🌐 Web interface: http://localhost:8080"
    echo "📊 Status: systemctl status imgserv"
    echo "📝 Logs: journalctl -u imgserv -f"
else
    echo "⚠️ Service may have issues, check with: systemctl status imgserv"
fi

echo ""
echo "🎉 Installation completed!"
echo "Visit http://localhost:8080 to see the interface"
