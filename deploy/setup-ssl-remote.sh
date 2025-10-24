#!/bin/bash
#
# SSL Setup via Camera Server
# Configures Let's Encrypt SSL on VPS remotely using brad@industrialcamera.com
#
# Prerequisites:
# - VPS must be accessible via SSH keys (already configured)
# - DNS A record must be configured and propagated
#
# Usage from camera server:
#   sudo bash deploy/setup-ssl-remote.sh
#

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[SSL-SETUP]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Load VPS config
if [ ! -f /etc/imgserv/.env ]; then
    error "Configuration file not found: /etc/imgserv/.env"
    exit 1
fi

source /etc/imgserv/.env

SSH_KEY="${VPS_SSH_KEY_PATH:-/opt/imgserv/.ssh/vps_key}"
EMAIL="brad@industrialcamera.com"
DOMAIN="woodlandhillswebcam.industrialcamera.com"

echo "=========================================="
echo "  SSL Certificate Setup (Remote)"
echo "  Domain: $DOMAIN"
echo "  Email: $EMAIL"
echo "=========================================="
echo ""

log "Downloading SSL setup script to VPS..."

# Download and run SSL setup script on VPS
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "${VPS_USER}@${VPS_HOST}" << ENDSSH
cd /root
curl -sSL https://raw.githubusercontent.com/lazerusrm/IMGSRV/main/deploy/vps-setup-ssl.sh -o vps-setup-ssl.sh
chmod +x vps-setup-ssl.sh

echo ""
echo "Running SSL setup on VPS..."
echo ""

bash vps-setup-ssl.sh $EMAIL
ENDSSH

if [ $? -eq 0 ]; then
    echo ""
    log "SSL setup completed!"
    echo ""
    echo "Your site is now available at:"
    echo "  https://$DOMAIN"
    echo ""
    echo "Test it:"
    echo "  curl -I https://$DOMAIN"
else
    error "SSL setup failed"
    echo ""
    echo "Common issues:"
    echo "1. DNS not propagated yet - wait 5-30 minutes"
    echo "2. Ports 80/443 not open on VPS"
    echo "3. Previous certificate rate limit hit"
    echo ""
    echo "To debug, SSH to VPS:"
    echo "  ssh -i $SSH_KEY ${VPS_USER}@${VPS_HOST}"
fi

