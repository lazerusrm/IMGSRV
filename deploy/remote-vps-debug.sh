#!/bin/bash
"""
Remote VPS Diagnostic Script for Image Sequence Server

This script runs diagnostics on your VPS from your camera server.
Use this to quickly check VPS status without SSH'ing into it.
"""

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
}

info() {
    echo -e "${BLUE}[REMOTE-DEBUG]${NC} $1"
}

# Check if VPS settings are configured
check_vps_config() {
    if [ ! -f /etc/imgserv/.env ]; then
        error "VPS configuration not found at /etc/imgserv/.env"
        exit 1
    fi
    
    source /etc/imgserv/.env
    
    if [ "$VPS_ENABLED" != "true" ]; then
        error "VPS is not enabled in configuration"
        exit 1
    fi
    
    if [ -z "$VPS_HOST" ] || [ "$VPS_HOST" = "your-vps-server.com" ]; then
        error "VPS host not configured properly"
        exit 1
    fi
    
    log "VPS Configuration:"
    log "  Host: $VPS_HOST"
    log "  User: $VPS_USER"
    log "  Port: $VPS_PORT"
    log "  Remote Path: $VPS_REMOTE_PATH"
    echo ""
}

# Test SSH connection
test_ssh_connection() {
    info "Testing SSH connection to VPS..."
    
    if [ ! -f "$VPS_SSH_KEY_PATH" ]; then
        error "SSH key not found at: $VPS_SSH_KEY_PATH"
        return 1
    fi
    
    ssh -i "$VPS_SSH_KEY_PATH" \
        -o StrictHostKeyChecking=no \
        -o ConnectTimeout=10 \
        -p "$VPS_PORT" \
        "$VPS_USER@$VPS_HOST" \
        "echo 'SSH connection successful'" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        log "✅ SSH connection successful"
        return 0
    else
        error "❌ SSH connection failed"
        return 1
    fi
}

# Test web server status
test_web_server_status() {
    info "Testing web server status on VPS..."
    
    ssh -i "$VPS_SSH_KEY_PATH" \
        -o StrictHostKeyChecking=no \
        -o ConnectTimeout=10 \
        -p "$VPS_PORT" \
        "$VPS_USER@$VPS_HOST" \
        "systemctl is-active nginx || systemctl is-active apache2 || systemctl is-active httpd" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        log "✅ Web server is running"
    else
        error "❌ Web server is not running"
    fi
}

# Test HTTP access
test_http_access() {
    info "Testing HTTP access to VPS..."
    
    # Test from camera server
    if curl -s -f "http://$VPS_HOST/" >/dev/null 2>&1; then
        log "✅ HTTP access from camera server works"
    else
        error "❌ HTTP access from camera server failed"
    fi
    
    # Test HTTPS access
    if curl -s -k -f "https://$VPS_HOST/" >/dev/null 2>&1; then
        log "✅ HTTPS access from camera server works"
    else
        warn "⚠️ HTTPS access from camera server failed"
    fi
    
    # Test monitoring path
    if curl -s -f "http://$VPS_HOST/monitoring/" >/dev/null 2>&1; then
        log "✅ Monitoring path access works"
    else
        error "❌ Monitoring path access failed"
    fi
}

# Check VPS file permissions
check_vps_permissions() {
    info "Checking VPS file permissions..."
    
    ssh -i "$VPS_SSH_KEY_PATH" \
        -o StrictHostKeyChecking=no \
        -o ConnectTimeout=10 \
        -p "$VPS_PORT" \
        "$VPS_USER@$VPS_HOST" \
        "ls -la $VPS_REMOTE_PATH" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        log "✅ Can access VPS remote path"
    else
        error "❌ Cannot access VPS remote path"
    fi
}

# Check VPS web server logs
check_vps_logs() {
    info "Checking VPS web server logs..."
    
    ssh -i "$VPS_SSH_KEY_PATH" \
        -o StrictHostKeyChecking=no \
        -o ConnectTimeout=10 \
        -p "$VPS_PORT" \
        "$VPS_USER@$VPS_HOST" \
        "tail -10 /var/log/nginx/error.log 2>/dev/null || tail -10 /var/log/apache2/error.log 2>/dev/null || tail -10 /var/log/httpd/error_log 2>/dev/null" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        log "✅ Retrieved web server error logs"
    else
        warn "⚠️ Could not retrieve web server error logs"
    fi
}

# Test RSYNC functionality
test_rsync() {
    info "Testing RSYNC functionality..."
    
    # Create a test file
    TEST_FILE="/tmp/rsync-test-$(date +%s).txt"
    echo "RSYNC test file - $(date)" > "$TEST_FILE"
    
    # Test RSYNC
    rsync -avz --delete \
        -e "ssh -i $VPS_SSH_KEY_PATH -o StrictHostKeyChecking=no -p $VPS_PORT" \
        "$TEST_FILE" \
        "$VPS_USER@$VPS_HOST:$VPS_REMOTE_PATH/" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        log "✅ RSYNC test successful"
        
        # Clean up test file
        rm -f "$TEST_FILE"
        ssh -i "$VPS_SSH_KEY_PATH" \
            -o StrictHostKeyChecking=no \
            -o ConnectTimeout=10 \
            -p "$VPS_PORT" \
            "$VPS_USER@$VPS_HOST" \
            "rm -f $VPS_REMOTE_PATH/rsync-test-*.txt" 2>/dev/null
    else
        error "❌ RSYNC test failed"
        rm -f "$TEST_FILE"
    fi
}

# Run comprehensive VPS diagnostics
run_vps_diagnostics() {
    info "Running comprehensive VPS diagnostics..."
    
    ssh -i "$VPS_SSH_KEY_PATH" \
        -o StrictHostKeyChecking=no \
        -o ConnectTimeout=10 \
        -p "$VPS_PORT" \
        "$VPS_USER@$VPS_HOST" \
        "curl -sSL https://raw.githubusercontent.com/lazerusrm/IMGSRV/main/deploy/vps-debug.sh | bash" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        log "✅ Comprehensive VPS diagnostics completed"
    else
        error "❌ Comprehensive VPS diagnostics failed"
    fi
}

# Main function
main() {
    info "Starting remote VPS diagnostics"
    
    check_vps_config
    
    if test_ssh_connection; then
        test_web_server_status
        test_http_access
        check_vps_permissions
        check_vps_logs
        test_rsync
        
        echo ""
        log "Would you like to run comprehensive VPS diagnostics?"
        echo -n "This will run the full debug script on your VPS [y/N]: "
        read -r RUN_FULL_DEBUG
        
        if [[ "$RUN_FULL_DEBUG" =~ ^[Yy]$ ]]; then
            run_vps_diagnostics
        fi
    else
        error "Cannot proceed without SSH connection to VPS"
        exit 1
    fi
    
    echo ""
    info "Remote VPS diagnostics completed"
}

# Run main function
main "$@"
