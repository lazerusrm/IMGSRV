#!/bin/bash
# One-liner installer for Image Sequence Server
# Usage: curl -sSL https://raw.githubusercontent.com/lazerusrm/IMGSRV/main/install.sh | bash

set -e
echo "🚀 Installing Image Sequence Server..."
apt-get update -qq && apt-get install -y -qq git curl python3 python3-pip python3-venv python3-dev build-essential libssl-dev libffi-dev libjpeg-dev libpng-dev fonts-dejavu-core bc ufw nginx openssl systemd
git clone -q https://github.com/lazerusrm/IMGSRV.git /opt/imgserv
cd /opt/imgserv && chmod +x deploy/install.sh
./deploy/install.sh --production --camera-ip 192.168.1.110 --camera-user admin --camera-pass 123456
echo "✅ Installation complete! Visit https://localhost"
