#!/bin/bash
#
# VPS dpkg Fix Script
# Fixes interrupted dpkg process on VPS
#
# Usage from camera server:
#   sudo bash deploy/fix-vps-dpkg.sh
#

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[DPKG-FIX]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Load VPS config
if [ ! -f /etc/imgserv/.env ]; then
    error "Configuration file not found: /etc/imgserv/.env"
    exit 1
fi

source /etc/imgserv/.env

SSH_KEY="${VPS_SSH_KEY_PATH:-/opt/imgserv/.ssh/vps_key}"

echo "=========================================="
echo "  VPS dpkg Fix"
echo "  Host: $VPS_HOST"
echo "=========================================="
echo ""

log "Fixing interrupted dpkg process on VPS..."

# Fix dpkg on VPS
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "${VPS_USER}@${VPS_HOST}" << 'ENDSSH'
echo "Running dpkg --configure -a..."
dpkg --configure -a

echo ""
echo "Cleaning up..."
apt-get clean
apt-get autoclean

echo ""
echo "Updating package lists..."
apt-get update

echo ""
echo "dpkg fix completed!"
ENDSSH

if [ $? -eq 0 ]; then
    log "dpkg fixed successfully!"
    echo ""
    echo "Now run SSL setup:"
    echo "  sudo bash deploy/setup-ssl-remote.sh"
else
    error "Failed to fix dpkg"
fi

