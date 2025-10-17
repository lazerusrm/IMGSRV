#!/bin/bash
"""
VPS Permissions Fix Script for Image Sequence Server

This script fixes file permissions issues on the VPS server.
Run this directly on your VPS when files show 403 Forbidden errors.
"""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
WEB_ROOT="/var/www/html/monitoring"

log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

info() {
    echo -e "${BLUE}[VPS-FIX]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
        echo "Please run: sudo bash $0"
        exit 1
    fi
}

# Detect web server and user
detect_web_server() {
    log "Detecting web server configuration..."
    
    # Check for nginx
    if systemctl is-active --quiet nginx; then
        WEB_SERVER="nginx"
        if id nginx &>/dev/null; then
            WEB_USER="nginx"
        else
            WEB_USER="www-data"
        fi
        log "Detected nginx web server, using user: $WEB_USER"
        
    # Check for apache
    elif systemctl is-active --quiet apache2 || systemctl is-active --quiet httpd; then
        WEB_SERVER="apache"
        if id apache &>/dev/null; then
            WEB_USER="apache"
        elif id www-data &>/dev/null; then
            WEB_USER="www-data"
        else
            WEB_USER="httpd"
        fi
        log "Detected apache web server, using user: $WEB_USER"
        
    # Default fallback
    else
        WEB_SERVER="unknown"
        WEB_USER="www-data"
        warn "Could not detect web server, using default user: $WEB_USER"
    fi
    
    log "Web server: $WEB_SERVER, User: $WEB_USER"
}

# Fix directory permissions
fix_directory_permissions() {
    log "Fixing directory permissions..."
    
    # Ensure web root exists
    if [ ! -d "$WEB_ROOT" ]; then
        log "Creating web root directory: $WEB_ROOT"
        mkdir -p "$WEB_ROOT"
    fi
    
    # Set ownership
    log "Setting ownership to $WEB_USER:$WEB_USER"
    chown -R "$WEB_USER:$WEB_USER" "$WEB_ROOT"
    
    # Set permissions
    log "Setting directory permissions to 755"
    find "$WEB_ROOT" -type d -exec chmod 755 {} \;
    
    # Set file permissions
    log "Setting file permissions to 644"
    find "$WEB_ROOT" -type f -exec chmod 644 {} \;
    
    # Make scripts executable
    log "Making scripts executable"
    find "$WEB_ROOT" -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true
    
    log "Directory permissions fixed"
}

# Fix SELinux context (if applicable)
fix_selinux_context() {
    if command -v setsebool &>/dev/null && command -v chcon &>/dev/null; then
        log "Fixing SELinux context..."
        
        # Enable httpd to read user content
        setsebool -P httpd_read_user_content 1 2>/dev/null || true
        
        # Set proper SELinux context
        chcon -R -t httpd_exec_t "$WEB_ROOT" 2>/dev/null || true
        
        log "SELinux context fixed"
    else
        log "SELinux not detected, skipping context fix"
    fi
}

# Test web server access
test_web_access() {
    log "Testing web server access..."
    
    # Create test file
    echo "Test file - $(date)" > "$WEB_ROOT/test.txt"
    chown "$WEB_USER:$WEB_USER" "$WEB_ROOT/test.txt"
    chmod 644 "$WEB_ROOT/test.txt"
    
    # Test local access
    if curl -s -f "http://localhost/test.txt" >/dev/null 2>&1; then
        log "✅ Local web access test passed"
    else
        warn "⚠️ Local web access test failed"
    fi
    
    # Test HTTPS if available
    if curl -s -k -f "https://localhost/test.txt" >/dev/null 2>&1; then
        log "✅ Local HTTPS access test passed"
    else
        log "ℹ️ HTTPS not available or test failed"
    fi
    
    # Clean up test file
    rm -f "$WEB_ROOT/test.txt"
}

# Show current permissions
show_permissions() {
    log "Current permissions for $WEB_ROOT:"
    ls -la "$WEB_ROOT" 2>/dev/null || warn "Directory not accessible"
    
    log "Web server process info:"
    if [ "$WEB_SERVER" = "nginx" ]; then
        ps aux | grep nginx | grep -v grep || warn "Nginx process not found"
    elif [ "$WEB_SERVER" = "apache" ]; then
        ps aux | grep apache | grep -v grep || warn "Apache process not found"
    fi
}

# Main fix function
main() {
    info "Starting VPS permissions fix for Image Sequence Server"
    
    check_root
    detect_web_server
    fix_directory_permissions
    fix_selinux_context
    test_web_access
    show_permissions
    
    info "VPS permissions fix completed!"
    
    echo ""
    echo "Summary:"
    echo "• Web server: $WEB_SERVER"
    echo "• Web user: $WEB_USER"
    echo "• Web root: $WEB_ROOT"
    echo ""
    echo "Test URLs:"
    echo "• HTTP: http://$(hostname -I | awk '{print $1}')/"
    echo "• HTTPS: https://$(hostname -I | awk '{print $1}')/"
    echo ""
    echo "If you still see 403 errors, check:"
    echo "• Web server configuration: systemctl status $WEB_SERVER"
    echo "• Web server logs: journalctl -u $WEB_SERVER -f"
    echo "• Directory permissions: ls -la $WEB_ROOT"
}

# Run main function
main "$@"
