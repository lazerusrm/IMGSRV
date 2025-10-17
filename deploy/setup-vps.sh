#!/bin/bash
"""
Complete VPS Setup Script for Image Sequence Server

This script automates the entire VPS setup process including:
1. VPS server deployment
2. SSH key setup
3. User creation
4. Service configuration
5. Testing

Usage: ./setup-vps.sh <vps-ip> <vps-user> <vps-password>
Example: ./setup-vps.sh 198.23.249.133 vmuser256133 MJuBUXOLQr
"""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VPS_IP="$1"
VPS_USER="$2"
VPS_PASSWORD="$3"
CAMERA_SERVER_IP=$(hostname -I | awk '{print $1}')

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
    echo -e "${BLUE}[VPS-SETUP]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
        echo "Please run: sudo bash $0 <vps-ip> <vps-user> <vps-password>"
        exit 1
    fi
}

# Validate parameters
validate_params() {
    if [[ -z "$VPS_IP" || -z "$VPS_USER" || -z "$VPS_PASSWORD" ]]; then
        error "Missing required parameters"
        echo "Usage: $0 <vps-ip> <vps-user> <vps-password>"
        echo "Example: $0 198.23.249.133 vmuser256133 MJuBUXOLQr"
        exit 1
    fi
    
    log "VPS Setup Parameters:"
    log "  VPS IP: $VPS_IP"
    log "  VPS User: $VPS_USER"
    log "  Camera Server: $CAMERA_SERVER_IP"
}

# Install required packages
install_packages() {
    log "Installing required packages..."
    
    apt-get update
    apt-get install -y sshpass jq curl
    
    log "Packages installed successfully"
}

# Generate SSH key pair
generate_ssh_key() {
    log "Generating SSH key pair..."
    
    # Create SSH directory
    mkdir -p /opt/imgserv/.ssh
    chown -R imgserv:imgserv /opt/imgserv/.ssh
    chmod 700 /opt/imgserv/.ssh
    
    # Generate SSH key if it doesn't exist
    if [[ ! -f /opt/imgserv/.ssh/vps_key ]]; then
        ssh-keygen -t rsa -b 4096 -f /opt/imgserv/.ssh/vps_key -N ""
        log "SSH key pair generated"
    else
        log "SSH key pair already exists"
    fi
    
    # Set proper permissions
    chown -R imgserv:imgserv /opt/imgserv/.ssh/
    chmod 700 /opt/imgserv/.ssh/
    chmod 600 /opt/imgserv/.ssh/vps_key
    chmod 644 /opt/imgserv/.ssh/vps_key.pub
}

# Deploy VPS server
deploy_vps_server() {
    log "Deploying VPS server..."
    
    # Use sshpass to run commands on VPS
    sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "
        # Switch to root
        sudo su - << 'EOF'
        # Run VPS deploy script
        curl -sSL https://raw.githubusercontent.com/lazerusrm/IMGSRV/main/deploy/vps-deploy.sh | bash
        
        # Create imgserv user
        useradd -r -s /bin/bash -d /opt/imgserv imgserv
        
        # Create SSH directory
        mkdir -p /home/imgserv/.ssh
        chown -R imgserv:imgserv /home/imgserv/.ssh
        chmod 700 /home/imgserv/.ssh
        
        # Create authorized_keys file
        touch /home/imgserv/.ssh/authorized_keys
        chown imgserv:imgserv /home/imgserv/.ssh/authorized_keys
        chmod 600 /home/imgserv/.ssh/authorized_keys
EOF
    "
    
    log "VPS server deployed successfully"
}

# Copy SSH key to VPS
copy_ssh_key() {
    log "Copying SSH key to VPS..."
    
    # Read public key
    PUBLIC_KEY=$(cat /opt/imgserv/.ssh/vps_key.pub)
    
    # Copy key to VPS using sshpass (to root user for easier management)
    sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "
        # Add key to root's authorized_keys for VPS sync
        echo '$PUBLIC_KEY' >> /root/.ssh/authorized_keys
        chmod 600 /root/.ssh/authorized_keys
        
        # Also add to imgserv user if it exists
        if id imgserv &>/dev/null; then
            echo '$PUBLIC_KEY' >> /home/imgserv/.ssh/authorized_keys
            chown imgserv:imgserv /home/imgserv/.ssh/authorized_keys
            chmod 600 /home/imgserv/.ssh/authorized_keys
        fi
    "
    
    log "SSH key copied to VPS (root and imgserv users)"
}

# Test SSH connection
test_ssh_connection() {
    log "Testing SSH connection..."
    
    if ssh -i /opt/imgserv/.ssh/vps_key -o StrictHostKeyChecking=no root@$VPS_IP "echo 'SSH connection successful'"; then
        log "SSH connection test passed (root user)"
        return 0
    else
        error "SSH connection test failed"
        return 1
    fi
}

# Configure camera server
configure_camera_server() {
    log "Configuring camera server..."
    
    # Update .env file (use root user for VPS sync - more reliable)
    cat >> /etc/imgserv/.env << EOF

# VPS synchronization settings
VPS_ENABLED=true
VPS_HOST=$VPS_IP
VPS_USER=root
VPS_PORT=22
VPS_REMOTE_PATH=/var/www/html/monitoring
VPS_SSH_KEY_PATH=/opt/imgserv/.ssh/vps_key
VPS_RSYNC_OPTIONS=-avz --delete
EOF
    
    log "Camera server configured with root user for VPS sync"
}

# Restart and test service
restart_and_test() {
    log "Restarting service..."
    
    systemctl restart imgserv
    
    # Wait for service to start
    sleep 5
    
    # Check service status
    if systemctl is-active --quiet imgserv; then
        log "Service restarted successfully"
    else
        error "Service failed to start"
        systemctl status imgserv
        return 1
    fi
    
    # Test VPS sync status
    log "Testing VPS sync status..."
    sleep 10  # Give service time to initialize
    
    if curl -s http://localhost:8080/status | jq -r '.vps_sync_status.enabled' | grep -q "true"; then
        log "VPS sync is enabled and working"
    else
        warn "VPS sync may not be working properly"
    fi
}

# Show completion info
show_completion_info() {
    info "VPS setup completed successfully!"
    
    echo ""
    echo "🎉 Setup Complete!"
    echo ""
    echo "Your VPS endpoints:"
    echo "  Main Page: http://$VPS_IP/"
    echo "  Iframe: http://$VPS_IP/iframe"
    echo "  Health Check: http://$VPS_IP/health"
    echo ""
    echo "Embedding code:"
    echo "<iframe src=\"http://$VPS_IP/iframe\" width=\"800\" height=\"600\" frameborder=\"0\"></iframe>"
    echo ""
    echo "Service status:"
    echo "  Camera Server: http://$CAMERA_SERVER_IP:8080/status"
    echo "  VPS Sync: Enabled and working"
    echo ""
    echo "Next steps:"
    echo "1. Wait 5-10 minutes for first GIF to be generated and synced"
    echo "2. Test the iframe URL: http://$VPS_IP/iframe"
    echo "3. Embed the iframe in your web host"
    echo ""
}

# Main function
main() {
    info "Starting complete VPS setup for Image Sequence Server"
    
    check_root
    validate_params
    install_packages
    generate_ssh_key
    deploy_vps_server
    copy_ssh_key
    
    if test_ssh_connection; then
        configure_camera_server
        restart_and_test
        show_completion_info
    else
        error "SSH connection failed. Please check VPS credentials and try again."
        exit 1
    fi
}

# Handle script interruption
trap 'error "Setup interrupted"; exit 1' INT TERM

# Run main function
main "$@"
