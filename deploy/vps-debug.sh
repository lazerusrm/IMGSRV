#!/bin/bash
# Comprehensive VPS Debugging Script for Image Sequence Server
#
# This script performs thorough debugging of VPS web server issues.
# Run this on your VPS to identify the root cause of 403 Forbidden errors.

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
WEB_ROOT="/var/www/html/monitoring"
LOG_FILE="/tmp/vps-debug-$(date +%Y%m%d-%H%M%S).log"

log() {
    echo -e "${GREEN}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[DEBUG]${NC} $1" | tee -a "$LOG_FILE"
}

section() {
    echo -e "${CYAN}==========================================${NC}" | tee -a "$LOG_FILE"
    echo -e "${CYAN}$1${NC}" | tee -a "$LOG_FILE"
    echo -e "${CYAN}==========================================${NC}" | tee -a "$LOG_FILE"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
        echo "Please run: sudo bash $0"
        exit 1
    fi
}

# System information
system_info() {
    section "SYSTEM INFORMATION"
    
    log "Hostname: $(hostname)"
    log "OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
    log "Kernel: $(uname -r)"
    log "Architecture: $(uname -m)"
    log "Uptime: $(uptime)"
    log "Memory: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
    log "Disk: $(df -h / | tail -1 | awk '{print $3 "/" $2 " (" $5 " used)"}')"
    
    echo "" | tee -a "$LOG_FILE"
}

# Web server detection and status
web_server_status() {
    section "WEB SERVER STATUS"
    
    # Check for nginx
    if systemctl is-active --quiet nginx; then
        WEB_SERVER="nginx"
        log "✅ Nginx is running"
        systemctl status nginx --no-pager -l | tee -a "$LOG_FILE"
    elif systemctl is-active --quiet apache2; then
        WEB_SERVER="apache2"
        log "✅ Apache2 is running"
        systemctl status apache2 --no-pager -l | tee -a "$LOG_FILE"
    elif systemctl is-active --quiet httpd; then
        WEB_SERVER="httpd"
        log "✅ Httpd is running"
        systemctl status httpd --no-pager -l | tee -a "$LOG_FILE"
    else
        WEB_SERVER="none"
        error "❌ No web server is running!"
        log "Checking for installed web servers..."
        
        if command -v nginx &>/dev/null; then
            log "Nginx is installed but not running"
            systemctl status nginx --no-pager -l | tee -a "$LOG_FILE"
        fi
        
        if command -v apache2 &>/dev/null; then
            log "Apache2 is installed but not running"
            systemctl status apache2 --no-pager -l | tee -a "$LOG_FILE"
        fi
        
        if command -v httpd &>/dev/null; then
            log "Httpd is installed but not running"
            systemctl status httpd --no-pager -l | tee -a "$LOG_FILE"
        fi
    fi
    
    echo "" | tee -a "$LOG_FILE"
}

# Web server configuration
web_server_config() {
    section "WEB SERVER CONFIGURATION"
    
    if [ "$WEB_SERVER" = "nginx" ]; then
        log "Nginx configuration files:"
        find /etc/nginx -name "*.conf" -o -name "monitoring*" | tee -a "$LOG_FILE"
        
        log "Nginx sites enabled:"
        ls -la /etc/nginx/sites-enabled/ | tee -a "$LOG_FILE"
        
        log "Nginx configuration test:"
        nginx -t 2>&1 | tee -a "$LOG_FILE"
        
        log "Nginx main configuration:"
        cat /etc/nginx/nginx.conf | grep -E "(user|worker_processes|error_log)" | tee -a "$LOG_FILE"
        
    elif [ "$WEB_SERVER" = "apache2" ]; then
        log "Apache2 configuration files:"
        find /etc/apache2 -name "*.conf" | head -10 | tee -a "$LOG_FILE"
        
        log "Apache2 sites enabled:"
        ls -la /etc/apache2/sites-enabled/ | tee -a "$LOG_FILE"
        
        log "Apache2 configuration test:"
        apache2ctl configtest 2>&1 | tee -a "$LOG_FILE"
        
    elif [ "$WEB_SERVER" = "httpd" ]; then
        log "Httpd configuration files:"
        find /etc/httpd -name "*.conf" | head -10 | tee -a "$LOG_FILE"
        
        log "Httpd configuration test:"
        httpd -t 2>&1 | tee -a "$LOG_FILE"
    fi
    
    echo "" | tee -a "$LOG_FILE"
}

# File system analysis
file_system_analysis() {
    section "FILE SYSTEM ANALYSIS"
    
    log "Web root directory: $WEB_ROOT"
    
    if [ -d "$WEB_ROOT" ]; then
        log "✅ Web root directory exists"
        
        log "Directory permissions:"
        ls -la "$WEB_ROOT" | tee -a "$LOG_FILE"
        
        log "Directory ownership:"
        stat "$WEB_ROOT" | grep -E "(Uid|Gid)" | tee -a "$LOG_FILE"
        
        log "Directory contents:"
        find "$WEB_ROOT" -type f -exec ls -la {} \; | tee -a "$LOG_FILE"
        
        log "Directory size:"
        du -sh "$WEB_ROOT" | tee -a "$LOG_FILE"
        
    else
        error "❌ Web root directory does not exist: $WEB_ROOT"
        log "Creating web root directory..."
        mkdir -p "$WEB_ROOT"
        chmod 755 "$WEB_ROOT"
    fi
    
    echo "" | tee -a "$LOG_FILE"
}

# Web server user analysis
web_user_analysis() {
    section "WEB SERVER USER ANALYSIS"
    
    # Detect web server user
    WEB_USER="unknown"
    
    if [ "$WEB_SERVER" = "nginx" ]; then
        if id nginx &>/dev/null; then
            WEB_USER="nginx"
        elif id www-data &>/dev/null; then
            WEB_USER="www-data"
        fi
    elif [ "$WEB_SERVER" = "apache2" ] || [ "$WEB_SERVER" = "httpd" ]; then
        if id apache &>/dev/null; then
            WEB_USER="apache"
        elif id www-data &>/dev/null; then
            WEB_USER="www-data"
        elif id httpd &>/dev/null; then
            WEB_USER="httpd"
        fi
    fi
    
    log "Detected web server: $WEB_SERVER"
    log "Detected web user: $WEB_USER"
    
    if [ "$WEB_USER" != "unknown" ]; then
        log "Web user details:"
        id "$WEB_USER" | tee -a "$LOG_FILE"
        
        log "Web user groups:"
        groups "$WEB_USER" | tee -a "$LOG_FILE"
        
        log "Web user home directory:"
        getent passwd "$WEB_USER" | cut -d: -f6 | tee -a "$LOG_FILE"
    else
        error "❌ Could not determine web server user"
    fi
    
    echo "" | tee -a "$LOG_FILE"
}

# Permission analysis
permission_analysis() {
    section "PERMISSION ANALYSIS"
    
    if [ -d "$WEB_ROOT" ]; then
        log "Current permissions for $WEB_ROOT:"
        ls -la "$WEB_ROOT" | tee -a "$LOG_FILE"
        
        log "Permission test - can web user read files?"
        if [ "$WEB_USER" != "unknown" ]; then
            sudo -u "$WEB_USER" ls -la "$WEB_ROOT" 2>&1 | tee -a "$LOG_FILE"
            
            log "Permission test - can web user access directory?"
            sudo -u "$WEB_USER" test -r "$WEB_ROOT" && log "✅ Web user can read directory" || error "❌ Web user cannot read directory"
            sudo -u "$WEB_USER" test -x "$WEB_ROOT" && log "✅ Web user can execute directory" || error "❌ Web user cannot execute directory"
        fi
        
        log "Parent directory permissions:"
        ls -la "$(dirname "$WEB_ROOT")" | tee -a "$LOG_FILE"
        
        log "Path traversal permissions:"
        ls -la /var/www/html/ | tee -a "$LOG_FILE"
        ls -la /var/www/ | tee -a "$LOG_FILE"
        ls -la /var/ | tee -a "$LOG_FILE"
        
    else
        error "❌ Web root directory does not exist for permission analysis"
    fi
    
    echo "" | tee -a "$LOG_FILE"
}

# Network and firewall analysis
network_analysis() {
    section "NETWORK AND FIREWALL ANALYSIS"
    
    log "Listening ports:"
    netstat -tlnp | grep -E ":(80|443|8080)" | tee -a "$LOG_FILE"
    
    log "Firewall status:"
    if command -v ufw &>/dev/null; then
        ufw status | tee -a "$LOG_FILE"
    elif command -v firewall-cmd &>/dev/null; then
        firewall-cmd --list-all | tee -a "$LOG_FILE"
    elif command -v iptables &>/dev/null; then
        iptables -L -n | tee -a "$LOG_FILE"
    else
        log "No firewall management tool found"
    fi
    
    log "Network interfaces:"
    ip addr show | grep -E "(inet |UP)" | tee -a "$LOG_FILE"
    
    echo "" | tee -a "$LOG_FILE"
}

# Web server logs analysis
log_analysis() {
    section "WEB SERVER LOGS ANALYSIS"
    
    if [ "$WEB_SERVER" = "nginx" ]; then
        log "Nginx error log (last 20 lines):"
        tail -20 /var/log/nginx/error.log 2>/dev/null | tee -a "$LOG_FILE" || warn "Nginx error log not found"
        
        log "Nginx access log (last 20 lines):"
        tail -20 /var/log/nginx/access.log 2>/dev/null | tee -a "$LOG_FILE" || warn "Nginx access log not found"
        
    elif [ "$WEB_SERVER" = "apache2" ]; then
        log "Apache2 error log (last 20 lines):"
        tail -20 /var/log/apache2/error.log 2>/dev/null | tee -a "$LOG_FILE" || warn "Apache2 error log not found"
        
        log "Apache2 access log (last 20 lines):"
        tail -20 /var/log/apache2/access.log 2>/dev/null | tee -a "$LOG_FILE" || warn "Apache2 access log not found"
        
    elif [ "$WEB_SERVER" = "httpd" ]; then
        log "Httpd error log (last 20 lines):"
        tail -20 /var/log/httpd/error_log 2>/dev/null | tee -a "$LOG_FILE" || warn "Httpd error log not found"
        
        log "Httpd access log (last 20 lines):"
        tail -20 /var/log/httpd/access_log 2>/dev/null | tee -a "$LOG_FILE" || warn "Httpd access log not found"
    fi
    
    log "System journal (last 20 lines):"
    journalctl -n 20 --no-pager | tee -a "$LOG_FILE"
    
    echo "" | tee -a "$LOG_FILE"
}

# Test web server functionality
test_web_server() {
    section "WEB SERVER FUNCTIONALITY TEST"
    
    # Test local access
    log "Testing local HTTP access..."
    if curl -s -f "http://localhost/" >/dev/null 2>&1; then
        log "✅ Local HTTP access works"
    else
        error "❌ Local HTTP access failed"
    fi
    
    # Test HTTPS if available
    log "Testing local HTTPS access..."
    if curl -s -k -f "https://localhost/" >/dev/null 2>&1; then
        log "✅ Local HTTPS access works"
    else
        warn "⚠️ Local HTTPS access failed (may be normal if not configured)"
    fi
    
    # Test specific monitoring path
    log "Testing monitoring path access..."
    if curl -s -f "http://localhost/monitoring/" >/dev/null 2>&1; then
        log "✅ Monitoring path access works"
    else
        error "❌ Monitoring path access failed"
    fi
    
    # Test health endpoint
    log "Testing health endpoint..."
    if curl -s -f "http://localhost/health" >/dev/null 2>&1; then
        log "✅ Health endpoint works"
    else
        warn "⚠️ Health endpoint failed"
    fi
    
    # Test external access
    EXTERNAL_IP=$(hostname -I | awk '{print $1}')
    log "Testing external access from $EXTERNAL_IP..."
    if curl -s -f "http://$EXTERNAL_IP/" >/dev/null 2>&1; then
        log "✅ External HTTP access works"
    else
        error "❌ External HTTP access failed"
    fi
    
    echo "" | tee -a "$LOG_FILE"
}

# SELinux analysis (if applicable)
selinux_analysis() {
    section "SELINUX ANALYSIS"
    
    if command -v getenforce &>/dev/null; then
        SELINUX_STATUS=$(getenforce)
        log "SELinux status: $SELINUX_STATUS"
        
        if [ "$SELINUX_STATUS" != "Disabled" ]; then
            log "SELinux contexts for web root:"
            ls -Z "$WEB_ROOT" 2>/dev/null | tee -a "$LOG_FILE" || warn "Could not get SELinux contexts"
            
            log "SELinux booleans related to web server:"
            getsebool -a | grep -E "(httpd|nginx)" | tee -a "$LOG_FILE" || warn "No web server SELinux booleans found"
        else
            log "SELinux is disabled"
        fi
    else
        log "SELinux not installed"
    fi
    
    echo "" | tee -a "$LOG_FILE"
}

# Generate recommendations
generate_recommendations() {
    section "RECOMMENDATIONS"
    
    log "Based on the analysis above, here are the recommended fixes:"
    echo "" | tee -a "$LOG_FILE"
    
    # Check if web server is running
    if [ "$WEB_SERVER" = "none" ]; then
        error "CRITICAL: No web server is running!"
        log "Fix: Start your web server"
        if command -v nginx &>/dev/null; then
            log "  systemctl start nginx"
            log "  systemctl enable nginx"
        elif command -v apache2 &>/dev/null; then
            log "  systemctl start apache2"
            log "  systemctl enable apache2"
        fi
        echo "" | tee -a "$LOG_FILE"
    fi
    
    # Check web root existence
    if [ ! -d "$WEB_ROOT" ]; then
        error "CRITICAL: Web root directory does not exist!"
        log "Fix: Create web root directory"
        log "  mkdir -p $WEB_ROOT"
        log "  chmod 755 $WEB_ROOT"
        echo "" | tee -a "$LOG_FILE"
    fi
    
    # Check permissions
    if [ "$WEB_USER" != "unknown" ]; then
        log "Fix permissions:"
        log "  chown -R $WEB_USER:$WEB_USER $WEB_ROOT"
        log "  chmod -R 755 $WEB_ROOT"
        log "  find $WEB_ROOT -type f -exec chmod 644 {} \\;"
        echo "" | tee -a "$LOG_FILE"
    fi
    
    # Check SELinux
    if command -v getenforce &>/dev/null && [ "$(getenforce)" != "Disabled" ]; then
        log "Fix SELinux contexts:"
        log "  setsebool -P httpd_read_user_content 1"
        log "  chcon -R -t httpd_exec_t $WEB_ROOT"
        echo "" | tee -a "$LOG_FILE"
    fi
    
    log "After applying fixes, test with:"
    log "  curl http://localhost/"
    log "  curl http://$(hostname -I | awk '{print $1}')/"
    echo "" | tee -a "$LOG_FILE"
}

# Main debugging function
main() {
    info "Starting comprehensive VPS debugging for Image Sequence Server"
    info "Debug log will be saved to: $LOG_FILE"
    
    check_root
    system_info
    web_server_status
    web_server_config
    file_system_analysis
    web_user_analysis
    permission_analysis
    network_analysis
    log_analysis
    test_web_server
    selinux_analysis
    generate_recommendations
    
    info "Comprehensive debugging completed!"
    info "Debug log saved to: $LOG_FILE"
    
    echo ""
    echo -e "${CYAN}==========================================${NC}"
    echo -e "${CYAN}DEBUGGING COMPLETE${NC}"
    echo -e "${CYAN}==========================================${NC}"
    echo ""
    echo "Debug log location: $LOG_FILE"
    echo "You can view the full log with: cat $LOG_FILE"
    echo ""
    echo "If you need to share this information, you can:"
    echo "1. Copy the log file: scp $LOG_FILE user@your-machine:/path/"
    echo "2. Or share the key findings from the recommendations section"
}

# Run main function
main "$@"
