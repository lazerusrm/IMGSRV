#!/bin/bash
#
# VPS SSL Certificate Setup Script
# Automates Let's Encrypt SSL certificate generation for Woodland Hills webcam.
#
# Prerequisites:
# - Domain DNS A record pointing to this server
# - Ports 80 and 443 open in firewall
# - Nginx installed and configured
#
# Usage:
#   sudo bash vps-setup-ssl.sh [email@example.com]
#

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="woodlandhillswebcam.industrialcamera.com"
WEB_ROOT="/var/www/html/monitoring"
NGINX_CONFIG="/etc/nginx/sites-available/monitoring"

log() {
    echo -e "${GREEN}[SSL-SETUP]${NC} $1"
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

# Validate email address
validate_email() {
    EMAIL=$1
    if [[ ! "$EMAIL" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
        error "Invalid email address: $EMAIL"
        return 1
    fi
    return 0
}

# Check DNS resolution
check_dns() {
    log "Checking DNS resolution for $DOMAIN..."
    
    # Get current public IP
    PUBLIC_IP=$(curl -s https://api.ipify.org)
    
    if [ -z "$PUBLIC_IP" ]; then
        warn "Could not detect public IP address"
        return 1
    fi
    
    log "Public IP: $PUBLIC_IP"
    
    # Check DNS resolution
    RESOLVED_IP=$(dig +short "$DOMAIN" | tail -n1)
    
    if [ -z "$RESOLVED_IP" ]; then
        error "Domain $DOMAIN does not resolve to any IP"
        echo ""
        echo "Please add an A record in GoDaddy DNS management:"
        echo "  Type: A"
        echo "  Name: woodlandhillswebcam"
        echo "  Value: $PUBLIC_IP"
        echo "  TTL: 600"
        echo ""
        echo "Wait 5-30 minutes for DNS propagation, then run this script again."
        return 1
    fi
    
    log "Domain resolves to: $RESOLVED_IP"
    
    if [ "$RESOLVED_IP" != "$PUBLIC_IP" ]; then
        warn "Domain resolves to $RESOLVED_IP but server IP is $PUBLIC_IP"
        echo ""
        echo "Please update the A record in GoDaddy to point to: $PUBLIC_IP"
        echo "Wait for DNS propagation (5-30 minutes) before continuing."
        echo ""
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        log "DNS correctly configured!"
    fi
    
    return 0
}

# Install certbot
install_certbot() {
    log "Installing Certbot and Nginx plugin..."
    
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
    
    if [ $? -eq 0 ]; then
        log "Certbot installed successfully"
    else
        error "Failed to install Certbot"
        exit 1
    fi
}

# Obtain SSL certificate
obtain_certificate() {
    EMAIL=$1
    
    log "Obtaining SSL certificate from Let's Encrypt..."
    log "Domain: $DOMAIN"
    log "Email: $EMAIL"
    
    # Run certbot in nginx mode
    certbot --nginx \
        -d "$DOMAIN" \
        --non-interactive \
        --agree-tos \
        --email "$EMAIL" \
        --redirect \
        --hsts \
        --staple-ocsp
    
    if [ $? -eq 0 ]; then
        log "SSL certificate obtained successfully!"
    else
        error "Failed to obtain SSL certificate"
        echo ""
        echo "Common issues:"
        echo "  1. Port 80 not open in firewall"
        echo "  2. Nginx not running or misconfigured"
        echo "  3. Domain not pointing to this server"
        echo "  4. Rate limit reached (5 certificates per week per domain)"
        echo ""
        echo "Check logs: journalctl -u certbot -n 50"
        exit 1
    fi
}

# Setup auto-renewal
setup_renewal() {
    log "Setting up automatic certificate renewal..."
    
    # Test renewal
    certbot renew --dry-run
    
    if [ $? -eq 0 ]; then
        log "Certificate renewal test successful"
        log "Certificates will auto-renew via systemd timer"
    else
        warn "Certificate renewal test failed"
        echo "Check configuration: certbot renew --dry-run"
    fi
    
    # Ensure certbot timer is enabled
    systemctl enable certbot.timer
    systemctl start certbot.timer
    
    log "Certbot renewal timer enabled"
}

# Verify SSL configuration
verify_ssl() {
    log "Verifying SSL configuration..."
    
    # Test HTTP redirect
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -L "http://$DOMAIN" --max-time 10)
    
    if [ "$HTTP_CODE" = "200" ]; then
        log "HTTP to HTTPS redirect working"
    else
        warn "HTTP redirect returned code: $HTTP_CODE"
    fi
    
    # Test HTTPS
    HTTPS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN" --max-time 10)
    
    if [ "$HTTPS_CODE" = "200" ]; then
        log "HTTPS working correctly"
    else
        warn "HTTPS returned code: $HTTPS_CODE"
    fi
    
    # Display certificate info
    log "Certificate information:"
    certbot certificates
}

# Update firewall rules
update_firewall() {
    log "Updating firewall rules for HTTPS..."
    
    # Check if ufw is installed
    if command -v ufw &> /dev/null; then
        ufw allow 443/tcp comment 'HTTPS'
        ufw allow 80/tcp comment 'HTTP for Let'\''s Encrypt'
        ufw status
        log "Firewall rules updated"
    else
        info "UFW not installed, skipping firewall configuration"
    fi
}

# Main execution
main() {
    echo "=========================================="
    echo "  VPS SSL Certificate Setup"
    echo "  Domain: $DOMAIN"
    echo "=========================================="
    echo ""
    
    # Check root
    check_root
    
    # Get email address
    EMAIL=$1
    if [ -z "$EMAIL" ]; then
        read -p "Enter email address for Let's Encrypt notifications: " EMAIL
    fi
    
    # Validate email
    if ! validate_email "$EMAIL"; then
        exit 1
    fi
    
    # Check DNS
    if ! check_dns; then
        exit 1
    fi
    
    # Install certbot
    install_certbot
    
    # Update firewall
    update_firewall
    
    # Obtain certificate
    obtain_certificate "$EMAIL"
    
    # Setup auto-renewal
    setup_renewal
    
    # Verify configuration
    verify_ssl
    
    echo ""
    echo "=========================================="
    log "SSL setup completed successfully!"
    echo "=========================================="
    echo ""
    echo "Your site is now available at:"
    echo "  https://$DOMAIN"
    echo ""
    echo "Certificate will auto-renew via systemd timer"
    echo "Check renewal status: systemctl status certbot.timer"
    echo ""
    echo "Test your SSL configuration:"
    echo "  https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"
    echo ""
}

# Run main function
main "$@"

