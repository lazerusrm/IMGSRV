#!/bin/bash
#
# Remote VPS Update Script
# Run from camera server to update VPS without logging in directly.
# Uses existing RSYNC SSH keys for authentication.
#
# Prerequisites:
# - VPS_ENABLED=true in /etc/imgserv/.env
# - SSH keys already configured at /opt/imgserv/.ssh/vps_key
# - RSYNC working between camera server and VPS
#
# Usage:
#   sudo bash deploy/update-vps-remote.sh
#
# This script will:
# - Pull latest code from GitHub to VPS
# - Restart nginx on VPS
# - Fix permissions on VPS
# - Test VPS endpoints
#

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[UPDATE-VPS]${NC} $1"
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
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
        echo "Please run: sudo bash $0"
        exit 1
    fi
}

# Load VPS configuration
load_vps_config() {
    log "Loading VPS configuration..."
    
    if [ ! -f /etc/imgserv/.env ]; then
        error "Configuration file not found: /etc/imgserv/.env"
        exit 1
    fi
    
    source /etc/imgserv/.env
    
    if [ "$VPS_ENABLED" != "true" ]; then
        error "VPS synchronization is not enabled"
        echo "Set VPS_ENABLED=true in /etc/imgserv/.env"
        exit 1
    fi
    
    if [ -z "$VPS_HOST" ] || [ -z "$VPS_USER" ]; then
        error "VPS configuration incomplete"
        echo "Required: VPS_HOST, VPS_USER"
        exit 1
    fi
    
    SSH_KEY="${VPS_SSH_KEY_PATH:-/opt/imgserv/.ssh/vps_key}"
    SSH_PORT="${VPS_PORT:-22}"
    
    log "VPS Host: $VPS_HOST"
    log "VPS User: $VPS_USER"
    log "SSH Port: $SSH_PORT"
}

# Test SSH connection
test_ssh_connection() {
    log "Testing SSH connection to VPS..."
    
    ssh -i "$SSH_KEY" \
        -p "$SSH_PORT" \
        -o StrictHostKeyChecking=no \
        -o ConnectTimeout=10 \
        -o BatchMode=yes \
        "${VPS_USER}@${VPS_HOST}" \
        "echo 'SSH connection successful'" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        log "SSH connection verified"
        return 0
    else
        error "SSH connection failed"
        echo ""
        echo "Troubleshooting:"
        echo "1. Check SSH key permissions: ls -l $SSH_KEY"
        echo "2. Test manually: ssh -i $SSH_KEY ${VPS_USER}@${VPS_HOST}"
        echo "3. Verify VPS is running: ping $VPS_HOST"
        exit 1
    fi
}

# Download and run VPS permission fix script
fix_vps_permissions() {
    log "Fixing VPS permissions..."
    
    ssh -i "$SSH_KEY" \
        -p "$SSH_PORT" \
        -o StrictHostKeyChecking=no \
        -o ConnectTimeout=10 \
        "${VPS_USER}@${VPS_HOST}" \
        'bash -s' << 'REMOTE_SCRIPT'
#!/bin/bash

# Detect web server user
WEB_USER="www-data"
if id nginx &>/dev/null; then
    WEB_USER="nginx"
elif id apache &>/dev/null; then
    WEB_USER="apache"
elif id httpd &>/dev/null; then
    WEB_USER="httpd"
fi

echo "Detected web server user: $WEB_USER"

# Fix permissions
WEB_ROOT="/var/www/html/monitoring"
if [ -d "$WEB_ROOT" ]; then
    chown -R "$WEB_USER:$WEB_USER" "$WEB_ROOT"
    chmod -R 755 "$WEB_ROOT"
    find "$WEB_ROOT" -type f -exec chmod 644 {} \;
    echo "Permissions fixed for $WEB_ROOT"
else
    echo "Warning: $WEB_ROOT not found"
fi

# Fix SELinux context if SELinux is enabled
if command -v semanage &> /dev/null && [ -d "$WEB_ROOT" ]; then
    chcon -R -t httpd_sys_content_t "$WEB_ROOT" 2>/dev/null || true
    echo "SELinux context updated"
fi
REMOTE_SCRIPT
    
    if [ $? -eq 0 ]; then
        log "VPS permissions fixed"
    else
        warn "Failed to fix VPS permissions (may not be critical)"
    fi
}

# Restart nginx on VPS
restart_nginx() {
    log "Restarting nginx on VPS..."
    
    ssh -i "$SSH_KEY" \
        -p "$SSH_PORT" \
        -o StrictHostKeyChecking=no \
        -o ConnectTimeout=10 \
        "${VPS_USER}@${VPS_HOST}" \
        'systemctl restart nginx && systemctl status nginx --no-pager -l | head -10' 2>/dev/null
    
    if [ $? -eq 0 ]; then
        log "Nginx restarted successfully"
    else
        warn "Failed to restart nginx (may need manual intervention)"
    fi
}

# Update monitoring scripts on VPS
update_monitoring_scripts() {
    log "Updating monitoring scripts on VPS..."
    
    ssh -i "$SSH_KEY" \
        -p "$SSH_PORT" \
        -o StrictHostKeyChecking=no \
        -o ConnectTimeout=10 \
        "${VPS_USER}@${VPS_HOST}" \
        'bash -s' << 'REMOTE_SCRIPT'
#!/bin/bash

# Simply regenerate index.html with latest GIF
WEB_ROOT="/var/www/html/monitoring"
LATEST_GIF=$(ls -t "$WEB_ROOT"/sequence_*.gif 2>/dev/null | head -1)

if [ -n "$LATEST_GIF" ]; then
    GIF_NAME=$(basename "$LATEST_GIF")
    cat > "$WEB_ROOT/index.html" << 'HTML_EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Woodland Hills City Center - Snow Load Monitoring</title>
    <meta http-equiv="refresh" content="300">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 10px; background-color: #f0f0f0; }
        .container { max-width: 100%; margin: 0 auto; background-color: white; border-radius: 8px; 
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden; }
        .header { background-color: #2c3e50; color: white; padding: 15px; text-align: center; }
        .header h1 { margin: 0; font-size: 1.5em; }
        .header h2 { margin: 5px 0 0 0; font-size: 1em; opacity: 0.9; }
        .content { padding: 15px; text-align: center; }
        .camera-image { max-width: 100%; height: auto; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .info { margin-top: 15px; color: #666; font-size: 14px; }
        @media (max-width: 768px) {
            body { padding: 5px; }
            .header { padding: 10px; }
            .header h1 { font-size: 1.3em; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Woodland Hills City Center</h1>
            <h2>Snow Load Monitoring</h2>
        </div>
        <div class="content">
HTML_EOF
    
    echo "            <img src=\"$GIF_NAME\" alt=\"Snow Load Monitoring GIF\" class=\"camera-image\">" >> "$WEB_ROOT/index.html"
    
    cat >> "$WEB_ROOT/index.html" << 'HTML_EOF'
            <div class="info">
                <p>GIF updates every 5 minutes</p>
            </div>
        </div>
    </div>
</body>
</html>
HTML_EOF
    
    echo "index.html regenerated with $GIF_NAME"
else
    echo "Warning: No GIF files found"
fi
REMOTE_SCRIPT
    
    if [ $? -eq 0 ]; then
        log "index.html regenerated on VPS"
    else
        warn "Failed to regenerate index.html"
    fi
}

# Test VPS endpoints
test_vps_endpoints() {
    log "Testing VPS endpoints..."
    
    # Test health endpoint
    HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "http://${VPS_HOST}/health" 2>/dev/null)
    
    if [ "$HEALTH_CODE" = "200" ]; then
        log "✓ Health endpoint: OK (HTTP $HEALTH_CODE)"
    else
        warn "✗ Health endpoint: Failed (HTTP $HEALTH_CODE)"
    fi
    
    # Test main page
    MAIN_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "http://${VPS_HOST}/" 2>/dev/null)
    
    if [ "$MAIN_CODE" = "200" ] || [ "$MAIN_CODE" = "301" ]; then
        log "✓ Main page: OK (HTTP $MAIN_CODE)"
    else
        warn "✗ Main page: Failed (HTTP $MAIN_CODE)"
    fi
    
    # Check for GIF files
    GIF_COUNT=$(ssh -i "$SSH_KEY" \
        -p "$SSH_PORT" \
        -o StrictHostKeyChecking=no \
        -o ConnectTimeout=10 \
        "${VPS_USER}@${VPS_HOST}" \
        'ls /var/www/html/monitoring/sequence_*.gif 2>/dev/null | wc -l' 2>/dev/null)
    
    if [ "$GIF_COUNT" -gt 0 ]; then
        log "✓ GIF files: $GIF_COUNT found"
    else
        warn "✗ No GIF files found (RSYNC may not have run yet)"
    fi
}

# Force RSYNC from camera server
force_rsync() {
    log "Forcing RSYNC to update VPS content..."
    
    # Trigger sequence generation on camera server
    curl -s http://localhost:8080/status | jq '.last_sequence_update' 2>/dev/null || true
    
    # Wait a moment for RSYNC to trigger
    sleep 2
    
    log "RSYNC triggered (check logs: journalctl -u imgserv -n 20 | grep -i rsync)"
}

# Check SSL certificate status (if available)
check_ssl_status() {
    log "Checking SSL certificate status..."
    
    ssh -i "$SSH_KEY" \
        -p "$SSH_PORT" \
        -o StrictHostKeyChecking=no \
        -o ConnectTimeout=10 \
        "${VPS_USER}@${VPS_HOST}" \
        'bash -s' << 'REMOTE_SCRIPT'
#!/bin/bash

if command -v certbot &> /dev/null; then
    echo "=== SSL Certificate Status ==="
    certbot certificates 2>/dev/null | grep -A5 "Certificate Name" || echo "No Let's Encrypt certificates found"
    echo ""
    
    # Check if certificate needs renewal
    certbot renew --dry-run 2>/dev/null && echo "✓ Certificate renewal test: PASSED" || echo "✗ Certificate renewal test: FAILED"
else
    echo "Certbot not installed (using self-signed certificate)"
fi
REMOTE_SCRIPT
    
    log "SSL check complete"
}

# Main execution
main() {
    echo "=========================================="
    echo "  VPS Remote Update Script"
    echo "  Camera Server → VPS Update"
    echo "=========================================="
    echo ""
    
    check_root
    load_vps_config
    test_ssh_connection
    
    echo ""
    info "Starting VPS update process..."
    echo ""
    
    # Update VPS
    fix_vps_permissions
    restart_nginx
    update_monitoring_scripts
    
    # Force content sync
    force_rsync
    
    # Test everything
    echo ""
    test_vps_endpoints
    
    # Check SSL
    echo ""
    check_ssl_status
    
    echo ""
    echo "=========================================="
    log "VPS Update Complete!"
    echo "=========================================="
    echo ""
    echo "VPS Information:"
    echo "  • Host: $VPS_HOST"
    echo "  • Main URL: http://${VPS_HOST}/"
    echo "  • Iframe URL: http://${VPS_HOST}/iframe"
    echo "  • Health Check: http://${VPS_HOST}/health"
    echo ""
    echo "Next Steps:"
    echo "1. Visit http://${VPS_HOST}/ to verify content"
    echo "2. Check VPS logs: journalctl -u nginx -f"
    echo "3. Monitor RSYNC: journalctl -u imgserv -f | grep -i rsync"
    echo ""
    echo "For SSL setup (if not done):"
    echo "  ssh -i $SSH_KEY ${VPS_USER}@${VPS_HOST}"
    echo "  bash vps-setup-ssl.sh your-email@example.com"
    echo ""
}

# Run main function
main "$@"

