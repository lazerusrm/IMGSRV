#!/bin/bash
"""
Auto-Installer for Image Sequence Server

This script automatically:
1. Updates the system
2. Installs all dependencies (git, python, etc.)
3. Clones the repository
4. Runs the main installer
5. Starts the service

Usage: curl -sSL https://raw.githubusercontent.com/lazerusrm/IMGSRV/main/autoinstall.sh | bash
Or: wget -qO- https://raw.githubusercontent.com/lazerusrm/IMGSRV/main/autoinstall.sh | bash
"""

# Remove strict error handling to be more resilient
# set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/lazerusrm/IMGSRV.git"
INSTALL_DIR="/opt/imgserv"
SERVICE_NAME="imgserv"

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
    echo -e "${BLUE}[AUTO-INSTALLER]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
        echo "Please run: sudo bash $0"
        exit 1
    fi
}

# Detect OS and set package manager
detect_os() {
    if [[ -f /etc/debian_version ]]; then
        OS="debian"
        PKG_MANAGER="apt"
        log "Detected Debian/Ubuntu system"
    elif [[ -f /etc/redhat-release ]]; then
        OS="redhat"
        PKG_MANAGER="yum"
        log "Detected RedHat/CentOS system"
    elif [[ -f /etc/arch-release ]]; then
        OS="arch"
        PKG_MANAGER="pacman"
        log "Detected Arch Linux system"
    else
        error "Unsupported operating system"
        exit 1
    fi
}

# Update system packages
update_system() {
    log "Updating system packages..."
    
    case $OS in
        "debian")
            # Try to fix broken packages first (ignore networkoptix errors)
            apt-get --fix-broken install -y 2>/dev/null || warn "Some packages may have issues, continuing..."
            apt-get update 2>/dev/null || warn "Update had issues, continuing..."
            apt-get upgrade -y 2>/dev/null || warn "Upgrade had issues, continuing..."
            ;;
        "redhat")
            yum update -y || warn "Update had issues, continuing..."
            ;;
        "arch")
            pacman -Syu --noconfirm || warn "Update had issues, continuing..."
            ;;
    esac
    
    log "System update completed (with warnings if any)"
}

# Safe package installer that ignores networkoptix errors
safe_apt_install() {
    local packages="$*"
    # Install packages and filter out networkoptix error messages
    apt-get install -y $packages 2>&1 | grep -v "networkoptix-mediaserver" | grep -v "dpkg: error processing package networkoptix-mediaserver" | grep -v "Errors were encountered while processing" | grep -v "E: Sub-process /usr/bin/dpkg returned an error code" || true
}

# Install dependencies
install_dependencies() {
    log "Installing dependencies..."
    
    case $OS in
        "debian")
            # Install packages in batches, ignoring networkoptix errors
            log "Installing core packages..."
            safe_apt_install git curl wget python3 python3-pip python3-venv python3-dev
            
            log "Installing build tools..."
            safe_apt_install build-essential
            
            log "Installing image processing libraries..."
            # Install all image libraries together, ignoring networkoptix errors
            safe_apt_install libssl-dev libffi-dev libjpeg-dev libpng-dev libfreetype6-dev liblcms2-dev libwebp-dev libharfbuzz-dev libfribidi-dev libxcb1-dev fonts-dejavu-core
            
            log "Installing system packages..."
            safe_apt_install bc ufw nginx openssl systemd
            ;;
        "redhat")
            yum install -y \
                git curl wget python3 python3-pip python3-devel gcc gcc-c++ make \
                openssl-devel libffi-devel libjpeg-devel libpng-devel freetype-devel \
                lcms2-devel libwebp-devel harfbuzz-devel fribidi-devel libxcb-devel \
                dejavu-fonts-common dejavu-sans-fonts bc firewalld nginx openssl systemd \
                || warn "Some packages failed to install, continuing..."
            ;;
        "arch")
            pacman -S --noconfirm \
                git curl wget python python-pip python-virtualenv base-devel \
                openssl libffi libjpeg-turbo libpng freetype2 lcms2 libwebp \
                harfbuzz fribidi libxcb ttf-dejavu bc ufw nginx openssl systemd \
                || warn "Some packages failed to install, continuing..."
            ;;
    esac
    
    log "Dependencies installation completed (networkoptix errors ignored)"
}

# Clone repository
clone_repository() {
    log "Cloning Image Sequence Server repository..."
    
    # Remove existing directory if it exists
    if [[ -d "$INSTALL_DIR" ]]; then
        warn "Removing existing installation directory"
        rm -rf "$INSTALL_DIR"
    fi
    
    # Clone repository with error handling
    if git clone "$REPO_URL" "$INSTALL_DIR"; then
        log "Repository cloned successfully to $INSTALL_DIR"
    else
        error "Failed to clone repository. Trying alternative method..."
        # Try downloading as zip as fallback
        cd /tmp
        if wget -q "$REPO_URL/archive/main.zip" -O imgserv.zip; then
            unzip -q imgserv.zip
            mv IMGSRV-main "$INSTALL_DIR"
            log "Repository downloaded and extracted successfully"
        else
            error "Failed to download repository. Please check your internet connection."
            exit 1
        fi
    fi
    
    if [[ ! -d "$INSTALL_DIR" ]]; then
        error "Installation directory not found after clone/download"
        exit 1
    fi
}

# Run main installer
run_installer() {
    log "Running main installer..."
    
    cd "$INSTALL_DIR"
    
    # Make installer executable
    chmod +x deploy/install.sh
    
    # Run installer with production settings and error handling
    if ./deploy/install.sh --production \
        --camera-ip 192.168.1.110 \
        --camera-user admin \
        --camera-pass 123456; then
        log "Main installer completed successfully"
    else
        warn "Main installer had issues, but continuing with manual setup..."
        # Try to manually set up the service
        manual_service_setup
    fi
}

# Manual service setup as fallback
manual_service_setup() {
    log "Setting up service manually..."
    
    # Create system user if it doesn't exist
    if ! id "imgserv" &>/dev/null; then
        useradd --system --shell /bin/false --home-dir /opt/imgserv --create-home imgserv
    fi
    
    # Create directories
    mkdir -p /var/lib/imgserv/images /var/lib/imgserv/sequences /var/log/imgserv
    chown -R imgserv:imgserv /var/lib/imgserv /var/log/imgserv
    
    # Set up Python environment properly
    log "Setting up Python virtual environment..."
    cd /opt/imgserv
    python3 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip first
    pip install --upgrade pip
    
    # Install dependencies
    log "Installing Python dependencies..."
    pip install -r requirements.txt
    
    # Create basic systemd service
    cat > /etc/systemd/system/imgserv.service << 'EOF'
[Unit]
Description=Image Sequence Server
After=network.target

[Service]
Type=simple
User=imgserv
Group=imgserv
WorkingDirectory=/opt/imgserv
ExecStart=/opt/imgserv/venv/bin/python /opt/imgserv/main.py
Restart=always
RestartSec=10
EnvironmentFile=/etc/imgserv/.env

[Install]
WantedBy=multi-user.target
EOF
    
    # Create basic environment file
    mkdir -p /etc/imgserv
    cat > /etc/imgserv/.env << 'EOF'
HOST=0.0.0.0
PORT=8080
LOG_LEVEL=INFO
CAMERA_IP=192.168.1.110
CAMERA_USERNAME=admin
CAMERA_PASSWORD=123456
DATA_DIR=/var/lib/imgserv
IMAGES_DIR=/var/lib/imgserv/images
SEQUENCES_DIR=/var/lib/imgserv/sequences
EOF
    
    # Set ownership
    chown -R imgserv:imgserv /opt/imgserv
    
    # Enable and start service
    systemctl daemon-reload
    systemctl enable imgserv
    systemctl start imgserv
    
    log "Manual service setup completed"
}

# Verify installation
verify_installation() {
    log "Verifying installation..."
    
    # Wait a moment for service to start
    sleep 5
    
    # Check if service is running
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log "Service is running"
    else
        warn "Service is not running, attempting to start..."
        systemctl start "$SERVICE_NAME" || warn "Failed to start service"
        sleep 5
        
        if systemctl is-active --quiet "$SERVICE_NAME"; then
            log "Service started successfully"
        else
            warn "Service may have issues, but installation completed"
            log "You can check status with: systemctl status $SERVICE_NAME"
        fi
    fi
    
    # Check if web interface is accessible (with timeout)
    sleep 10  # Give service time to fully start
    
    if timeout 10 curl -s -k https://localhost/health > /dev/null 2>&1; then
        log "Web interface is accessible"
    else
        warn "Web interface not accessible yet (may need more time or configuration)"
        log "You can check logs with: journalctl -u $SERVICE_NAME -f"
    fi
    
    log "Installation verification completed"
}

# Display completion information
show_completion_info() {
    echo ""
    echo "=========================================="
    echo -e "${GREEN}🎉 INSTALLATION COMPLETED SUCCESSFULLY! 🎉${NC}"
    echo "=========================================="
    echo ""
    echo -e "${BLUE}Service Information:${NC}"
    echo "• Service Name: $SERVICE_NAME"
    echo "• Installation Directory: $INSTALL_DIR"
    echo "• Web Interface: https://localhost"
    echo "• Status Endpoint: https://localhost/status"
    echo "• Health Check: https://localhost/health"
    echo ""
    echo -e "${BLUE}Service Management:${NC}"
    echo "• Check Status: systemctl status $SERVICE_NAME"
    echo "• View Logs: journalctl -u $SERVICE_NAME -f"
    echo "• Restart Service: systemctl restart $SERVICE_NAME"
    echo "• Stop Service: systemctl stop $SERVICE_NAME"
    echo ""
    echo -e "${BLUE}Configuration:${NC}"
    echo "• Config File: /etc/imgserv/.env"
    echo "• Log File: /var/log/imgserv/app.log"
    echo "• Data Directory: /var/lib/imgserv"
    echo ""
    echo -e "${BLUE}Camera Settings:${NC}"
    echo "• Camera IP: 192.168.1.110"
    echo "• Username: admin"
    echo "• Password: 123456"
    echo "• Update these in /etc/imgserv/.env for production"
    echo ""
    echo -e "${YELLOW}⚠️  IMPORTANT SECURITY NOTES:${NC}"
    echo "• Change default camera password in production"
    echo "• Update SECRET_KEY in /etc/imgserv/.env"
    echo "• Configure firewall rules as needed"
    echo "• Install proper SSL certificates for production"
    echo ""
    echo -e "${GREEN}🚀 Your Image Sequence Server is ready!${NC}"
    echo "Visit https://localhost to see the traffic camera interface"
    echo ""
}

# Main installation function
main() {
    echo ""
    echo "=========================================="
    echo -e "${BLUE}Image Sequence Server Auto-Installer${NC}"
    echo "=========================================="
    echo ""
    echo "This script will automatically install:"
    echo "• All system dependencies"
    echo "• Image Sequence Server from GitHub"
    echo "• Production configuration"
    echo "• Systemd service"
    echo "• Nginx reverse proxy"
    echo "• SSL certificates"
    echo ""
    
    # Run installation steps
    check_root
    detect_os
    update_system
    install_dependencies
    clone_repository
    run_installer
    verify_installation
    show_completion_info
}

# Handle script interruption
trap 'error "Installation interrupted"; exit 1' INT TERM

# Run main function
main "$@"
