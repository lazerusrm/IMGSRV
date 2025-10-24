#!/bin/bash
#
# Force fresh SSL setup on VPS
# Removes cached script and downloads latest version
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
echo "  SSL Certificate Setup (Fresh)"
echo "  Domain: $DOMAIN"
echo "  Email: $EMAIL"
echo "=========================================="
echo ""

log "Removing cached SSL script on VPS and downloading fresh version..."

# Remove old script and download fresh one, then run it
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "${VPS_USER}@${VPS_HOST}" << ENDSSH
cd /root

# Remove old cached script
rm -f vps-setup-ssl.sh

# Download latest version
echo "Downloading latest SSL setup script..."
curl -sSL https://raw.githubusercontent.com/lazerusrm/IMGSRV/main/deploy/vps-setup-ssl.sh -o vps-setup-ssl.sh
chmod +x vps-setup-ssl.sh

echo ""
echo "Running fresh SSL setup..."
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
    echo "To debug manually, SSH to VPS:"
    echo "  ssh -i $SSH_KEY ${VPS_USER}@${VPS_HOST}"
fi

