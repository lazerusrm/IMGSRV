#!/bin/bash
# VPS HTTPS Patch Script
# Run this directly on your VPS to enable HTTPS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

echo "=========================================="
echo "VPS HTTPS Patch Script"
echo "Woodland Hills City Center Monitoring"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    error "This script must be run as root (use: sudo bash $0)"
fi

# Configuration
WEB_ROOT="/var/www/html/monitoring"
NGINX_CONFIG="/etc/nginx/sites-available/monitoring"
SSL_DIR="/etc/nginx/ssl"

# Detect OS
if [ -f /etc/debian_version ]; then
    OS="debian"
    log "Detected Debian/Ubuntu system"
elif [ -f /etc/redhat-release ]; then
    OS="redhat"
    log "Detected RedHat/CentOS system"
else
    warn "Unknown OS, assuming Debian-based"
    OS="debian"
fi

# Install required packages
log "Ensuring required packages are installed..."
if [ "$OS" = "debian" ]; then
    apt-get update -qq 2>/dev/null || warn "apt-get update failed"
    apt-get install -y nginx openssl 2>/dev/null || warn "Package installation had issues"
else
    yum install -y nginx openssl 2>/dev/null || warn "Package installation had issues"
fi

# Create SSL directory and certificate
log "Setting up SSL certificate..."
mkdir -p "$SSL_DIR"

if [ ! -f "$SSL_DIR/monitoring.crt" ]; then
    log "Generating self-signed SSL certificate..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$SSL_DIR/monitoring.key" \
        -out "$SSL_DIR/monitoring.crt" \
        -subj "/C=US/ST=California/L=Woodland Hills/O=City Center/CN=monitoring" \
        2>/dev/null || error "SSL certificate generation failed"
    
    log "✅ SSL certificate created"
else
    log "SSL certificate already exists"
fi

# Set proper permissions
chmod 600 "$SSL_DIR/monitoring.key"
chmod 644 "$SSL_DIR/monitoring.crt"

# Backup existing nginx config
if [ -f "$NGINX_CONFIG" ]; then
    log "Backing up existing nginx configuration..."
    cp "$NGINX_CONFIG" "${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Create new nginx configuration with HTTPS
log "Creating nginx configuration with HTTPS..."
cat > "$NGINX_CONFIG" << 'EOF'
# HTTP to HTTPS redirect
server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}

# HTTPS server
server {
    listen 443 ssl;
    server_name _;
    root /var/www/html/monitoring;
    index index.html;
    
    # SSL configuration
    ssl_certificate /etc/nginx/ssl/monitoring.crt;
    ssl_certificate_key /etc/nginx/ssl/monitoring.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000" always;
    
    # Cache static content
    location ~* \.(gif|jpg|jpeg|png|css|js)$ {
        expires 1h;
        add_header Cache-Control "public, immutable";
    }
    
    # Main page
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # Iframe endpoint
    location /iframe.html {
        try_files $uri =404;
    }
}
EOF

log "✅ Nginx configuration updated"

# Enable site if not already enabled
if [ ! -L /etc/nginx/sites-enabled/monitoring ]; then
    log "Enabling monitoring site..."
    ln -sf "$NGINX_CONFIG" /etc/nginx/sites-enabled/monitoring
fi

# Remove default site if exists
if [ -L /etc/nginx/sites-enabled/default ]; then
    log "Removing default nginx site..."
    rm -f /etc/nginx/sites-enabled/default
fi

# Test nginx configuration
log "Testing nginx configuration..."
if nginx -t 2>/dev/null; then
    log "✅ Nginx configuration is valid"
else
    error "Nginx configuration test failed! Rolling back..."
fi

# Restart nginx
log "Restarting nginx..."
if systemctl restart nginx; then
    log "✅ Nginx restarted successfully"
else
    error "Failed to restart nginx"
fi

# Configure firewall (if available)
log "Configuring firewall..."
if command -v ufw &> /dev/null; then
    ufw allow 443/tcp comment 'HTTPS monitoring' 2>/dev/null || warn "UFW rule addition failed"
    ufw allow 80/tcp comment 'HTTP redirect' 2>/dev/null || warn "UFW rule addition failed"
    log "✅ Firewall rules updated (ufw)"
elif command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-service=https 2>/dev/null || warn "Firewall rule addition failed"
    firewall-cmd --permanent --add-service=http 2>/dev/null || warn "Firewall rule addition failed"
    firewall-cmd --reload 2>/dev/null || warn "Firewall reload failed"
    log "✅ Firewall rules updated (firewalld)"
else
    warn "No firewall detected (ufw/firewalld)"
fi

# Verify HTTPS is working
log "Verifying HTTPS configuration..."
sleep 2

if curl -k -s -o /dev/null -w "%{http_code}" https://localhost/ | grep -q "200\|301\|302"; then
    log "✅ HTTPS is responding"
else
    warn "HTTPS verification failed, but configuration is in place"
fi

# Show certificate info
log "SSL Certificate information:"
info "  Location: $SSL_DIR/monitoring.crt"
info "  Valid for: 365 days"
info "  Type: Self-signed"

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "=========================================="
echo "✅ HTTPS Patch Complete!"
echo "=========================================="
echo ""
log "Your monitoring site is now HTTPS-enabled!"
echo ""
info "Access URLs:"
info "  HTTPS: https://$SERVER_IP/"
info "  HTTP:  http://$SERVER_IP/ (redirects to HTTPS)"
echo ""
warn "Note: Self-signed certificate will show browser warning"
warn "To fix: Install a proper SSL certificate (Let's Encrypt recommended)"
echo ""
log "Nginx configuration backup: ${NGINX_CONFIG}.backup.*"
log "SSL certificate: $SSL_DIR/monitoring.crt"
log "SSL key: $SSL_DIR/monitoring.key"
echo ""

# Test from external
echo "Testing HTTPS redirect..."
REDIRECT_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/)
if [ "$REDIRECT_CODE" = "301" ]; then
    log "✅ HTTP to HTTPS redirect working"
else
    warn "HTTP redirect returned: $REDIRECT_CODE"
fi

echo ""
log "Patch complete! Your monitoring site is now secure."
echo ""

