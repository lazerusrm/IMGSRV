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

set -euo pipefail

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
            apt-get update
            apt-get upgrade -y
            ;;
        "redhat")
            yum update -y
            ;;
        "arch")
            pacman -Syu --noconfirm
            ;;
    esac
    
    log "System updated successfully"
}

# Install dependencies
install_dependencies() {
    log "Installing dependencies..."
    
    case $OS in
        "debian")
            apt-get install -y \
                git \
                curl \
                wget \
                python3 \
                python3-pip \
                python3-venv \
                python3-dev \
                build-essential \
                libssl-dev \
                libffi-dev \
                libjpeg-dev \
                libpng-dev \
                libfreetype6-dev \
                liblcms2-dev \
                libwebp-dev \
                libharfbuzz-dev \
                libfribidi-dev \
                libxcb1-dev \
                fonts-dejavu-core \
                bc \
                ufw \
                nginx \
                openssl \
                systemd
            ;;
        "redhat")
            yum install -y \
                git \
                curl \
                wget \
                python3 \
                python3-pip \
                python3-devel \
                gcc \
                gcc-c++ \
                make \
                openssl-devel \
                libffi-devel \
                libjpeg-devel \
                libpng-devel \
                freetype-devel \
                lcms2-devel \
                libwebp-devel \
                harfbuzz-devel \
                fribidi-devel \
                libxcb-devel \
                dejavu-fonts-common \
                dejavu-sans-fonts \
                bc \
                firewalld \
                nginx \
                openssl \
                systemd
            ;;
        "arch")
            pacman -S --noconfirm \
                git \
                curl \
                wget \
                python \
                python-pip \
                python-virtualenv \
                base-devel \
                openssl \
                libffi \
                libjpeg-turbo \
                libpng \
                freetype2 \
                lcms2 \
                libwebp \
                harfbuzz \
                fribidi \
                libxcb \
                ttf-dejavu \
                bc \
                ufw \
                nginx \
                openssl \
                systemd
            ;;
    esac
    
    log "Dependencies installed successfully"
}

# Clone repository
clone_repository() {
    log "Cloning Image Sequence Server repository..."
    
    # Remove existing directory if it exists
    if [[ -d "$INSTALL_DIR" ]]; then
        warn "Removing existing installation directory"
        rm -rf "$INSTALL_DIR"
    fi
    
    # Clone repository
    git clone "$REPO_URL" "$INSTALL_DIR"
    
    if [[ ! -d "$INSTALL_DIR" ]]; then
        error "Failed to clone repository"
        exit 1
    fi
    
    log "Repository cloned successfully to $INSTALL_DIR"
}

# Run main installer
run_installer() {
    log "Running main installer..."
    
    cd "$INSTALL_DIR"
    
    # Make installer executable
    chmod +x deploy/install.sh
    
    # Run installer with production settings
    ./deploy/install.sh --production \
        --camera-ip 192.168.1.110 \
        --camera-user admin \
        --camera-pass 123456
    
    if [[ $? -eq 0 ]]; then
        log "Main installer completed successfully"
    else
        error "Main installer failed"
        exit 1
    fi
}

# Verify installation
verify_installation() {
    log "Verifying installation..."
    
    # Check if service is running
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log "Service is running"
    else
        warn "Service is not running, attempting to start..."
        systemctl start "$SERVICE_NAME"
        sleep 5
        
        if systemctl is-active --quiet "$SERVICE_NAME"; then
            log "Service started successfully"
        else
            error "Failed to start service"
            systemctl status "$SERVICE_NAME"
            return 1
        fi
    fi
    
    # Check if web interface is accessible
    sleep 10  # Give service time to fully start
    
    if curl -s -k https://localhost/health > /dev/null 2>&1; then
        log "Web interface is accessible"
    else
        warn "Web interface not accessible yet (may need more time)"
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
