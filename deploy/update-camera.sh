#!/bin/bash
"""
Camera Server Update Script
Quick update script to pull latest code and restart service.

Usage:
  sudo bash deploy/update-camera.sh
  
Or one-liner:
  curl -sSL https://raw.githubusercontent.com/lazerusrm/IMGSRV/main/deploy/update-camera.sh | sudo bash
"""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[UPDATE]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    error "This script must be run as root"
    echo "Please run: sudo bash $0"
    exit 1
fi

echo "=========================================="
echo "  Camera Server Update"
echo "  Version: 1.2.0+"
echo "=========================================="
echo ""

# Check if imgserv is installed
if [ ! -d /opt/imgserv ]; then
    error "IMGSRV not found at /opt/imgserv"
    echo "Please run the installer first:"
    echo "  curl -sSL https://raw.githubusercontent.com/lazerusrm/IMGSRV/main/autoinstall.sh | bash"
    exit 1
fi

log "Pulling latest code from GitHub..."
cd /opt/imgserv

# Stash any local changes
git stash 2>/dev/null

# Pull latest
git pull origin main

if [ $? -eq 0 ]; then
    log "Code updated successfully"
else
    error "Failed to pull latest code"
    exit 1
fi

log "Restarting imgserv service..."
systemctl restart imgserv

# Wait a moment for service to start
sleep 3

# Check service status
if systemctl is-active --quiet imgserv; then
    log "Service restarted successfully"
else
    error "Service failed to start"
    echo "Check logs: journalctl -u imgserv -n 50"
    exit 1
fi

# Also restart networkoptix if it exists
if systemctl list-units --full -all | grep -q networkoptix-mediaserver.service; then
    log "Restarting networkoptix-mediaserver..."
    systemctl restart networkoptix-mediaserver 2>/dev/null || warn "Failed to restart networkoptix (may be normal)"
fi

# Show service status
echo ""
log "Service Status:"
systemctl status imgserv --no-pager -l | head -15

# Show recent logs
echo ""
log "Recent Logs:"
journalctl -u imgserv -n 10 --no-pager

# Check version
echo ""
if [ -f /opt/imgserv/VERSION ]; then
    VERSION=$(cat /opt/imgserv/VERSION)
    log "Current Version: $VERSION"
fi

echo ""
echo "=========================================="
log "Camera Server Update Complete!"
echo "=========================================="
echo ""
echo "Useful Commands:"
echo "  • View logs: journalctl -u imgserv -f"
echo "  • Check status: systemctl status imgserv"
echo "  • Configuration: http://localhost:8080/config"
echo "  • Service status: curl http://localhost:8080/status | jq"
echo ""

# Check if VPS is enabled and offer to update it
if [ -f /etc/imgserv/.env ] && grep -q "^VPS_ENABLED=true" /etc/imgserv/.env 2>/dev/null; then
    source /etc/imgserv/.env
    echo "VPS synchronization is enabled for: $VPS_HOST"
    echo ""
    echo "To update VPS remotely (no login required):"
    echo "  sudo bash /opt/imgserv/deploy/update-vps-remote.sh"
    echo ""
fi

log "Update complete!"

