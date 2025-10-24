#!/bin/bash
"""
Remote VPS Update Script
Run from camera server to update VPS without logging in directly.
Uses existing RSYNC SSH keys for authentication.

Prerequisites:
- VPS_ENABLED=true in /etc/imgserv/.env
- SSH keys already configured at /opt/imgserv/.ssh/vps_key
- RSYNC working between camera server and VPS

Usage:
  sudo bash deploy/update-vps-remote.sh
  
This script will:
- Pull latest code from GitHub to VPS
- Restart nginx on VPS
- Fix permissions on VPS
- Test VPS endpoints
"""

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

# Download latest update script for index.html
curl -sSL https://raw.githubusercontent.com/lazerusrm/IMGSRV/main/deploy/vps-deploy.sh | \
    sed -n '/update-monitoring-index.sh/,/^EOF$/p' | \
    sed '1d;$d' > /usr/local/bin/update-monitoring-index.sh.tmp

if [ -s /usr/local/bin/update-monitoring-index.sh.tmp ]; then
    mv /usr/local/bin/update-monitoring-index.sh.tmp /usr/local/bin/update-monitoring-index.sh
    chmod +x /usr/local/bin/update-monitoring-index.sh
    echo "Monitoring script updated"
    
    # Run the script to update index.html
    /usr/local/bin/update-monitoring-index.sh
    echo "index.html regenerated"
else
    echo "Warning: Failed to download monitoring script"
fi
REMOTE_SCRIPT
    
    if [ $? -eq 0 ]; then
        log "Monitoring scripts updated"
    else
        warn "Failed to update monitoring scripts"
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

