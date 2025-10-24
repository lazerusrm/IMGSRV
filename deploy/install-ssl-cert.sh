#!/bin/bash
#
# Fix nginx config and install SSL certificate
# Runs on VPS to configure server_name and install certificate
#

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[NGINX-FIX]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Load VPS config
if [ ! -f /etc/imgserv/.env ]; then
    error "Configuration file not found: /etc/imgserv/.env"
    exit 1
fi

source /etc/imgserv/.env

SSH_KEY="${VPS_SSH_KEY_PATH:-/opt/imgserv/.ssh/vps_key}"
DOMAIN="woodlandhillswebcam.industrialcamera.com"

echo "=========================================="
echo "  Fix Nginx Config & Install Certificate"
echo "  Domain: $DOMAIN"
echo "=========================================="
echo ""

log "Fixing nginx configuration on VPS..."

# Fix nginx config and install certificate
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "${VPS_USER}@${VPS_HOST}" << 'ENDSSH'
DOMAIN="woodlandhillswebcam.industrialcamera.com"
NGINX_CONFIG="/etc/nginx/sites-available/monitoring"

echo "Backing up nginx config..."
cp "$NGINX_CONFIG" "$NGINX_CONFIG.backup"

echo "Updating server_name in nginx config..."

# Update the server block to include server_name
sed -i 's/server_name _;/server_name '"$DOMAIN"' www.'"$DOMAIN"' _;/' "$NGINX_CONFIG"

echo "Testing nginx configuration..."
nginx -t

if [ $? -eq 0 ]; then
    echo "Nginx config is valid"
    
    echo ""
    echo "Installing SSL certificate..."
    certbot install --cert-name "$DOMAIN" --nginx
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "Reloading nginx..."
        systemctl reload nginx
        
        echo ""
        echo "✓ SSL certificate installed successfully!"
        echo ""
        echo "Your site is now available at:"
        echo "  https://$DOMAIN"
    else
        echo "✗ Failed to install certificate"
        exit 1
    fi
else
    echo "✗ Nginx config test failed"
    exit 1
fi
ENDSSH

if [ $? -eq 0 ]; then
    echo ""
    log "SSL setup completed successfully!"
    echo ""
    echo "============================================"
    echo "🎉 HTTPS is now active!"
    echo "============================================"
    echo ""
    echo "Your site: https://$DOMAIN"
    echo ""
    echo "Test it:"
    echo "  curl -I https://$DOMAIN"
    echo "  curl -I http://$DOMAIN  # Should redirect to HTTPS"
    echo ""
else
    error "Failed to configure SSL"
fi

