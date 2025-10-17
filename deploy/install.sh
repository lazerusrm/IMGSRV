#!/bin/bash
"""
Idempotent installer script for Image Sequence Server.

This script can be run multiple times safely and will:
1. Create system user and directories
2. Install Python dependencies
3. Configure systemd service
4. Setup SSL certificates
5. Configure firewall
6. Start the service

Usage: ./install.sh [--production] [--camera-ip IP] [--camera-user USER] [--camera-pass PASS]
"""

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="/opt/imgserv"
SERVICE_USER="imgserv"
SERVICE_GROUP="imgserv"
VENV_DIR="$PROJECT_DIR/venv"
CONFIG_DIR="/etc/imgserv"
LOG_DIR="/var/log/imgserv"
DATA_DIR="/var/lib/imgserv"

# Default values
PRODUCTION=false
CAMERA_IP="192.168.1.110"
CAMERA_USER="admin"
CAMERA_PASS="123456"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --production)
            PRODUCTION=true
            shift
            ;;
        --camera-ip)
            CAMERA_IP="$2"
            shift 2
            ;;
        --camera-user)
            CAMERA_USER="$2"
            shift 2
            ;;
        --camera-pass)
            CAMERA_PASS="$2"
            shift 2
            ;;
        *)
            echo "Unknown option $1"
            exit 1
            ;;
    esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
        exit 1
    fi
}

# Check system requirements
check_requirements() {
    log "Checking system requirements..."
    
    # Check if running on Linux
    if [[ "$(uname)" != "Linux" ]]; then
        error "This script is designed for Linux systems"
        exit 1
    fi
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is required but not installed"
        exit 1
    fi
    
    local python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if [[ $(echo "$python_version < 3.8" | bc -l) -eq 1 ]]; then
        error "Python 3.8 or higher is required (found $python_version)"
        exit 1
    fi
    
    log "System requirements check passed"
}

# Create system user and directories
setup_user_and_directories() {
    log "Setting up user and directories..."
    
    # Create user if it doesn't exist
    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd --system --shell /bin/false --home-dir "$PROJECT_DIR" --create-home "$SERVICE_USER"
        log "Created user: $SERVICE_USER"
    else
        log "User $SERVICE_USER already exists"
    fi
    
    # Create directories
    mkdir -p "$PROJECT_DIR" "$CONFIG_DIR" "$LOG_DIR" "$DATA_DIR"
    mkdir -p "$DATA_DIR/images" "$DATA_DIR/sequences"
    
    # Set ownership
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$PROJECT_DIR" "$DATA_DIR" "$LOG_DIR"
    chmod 755 "$PROJECT_DIR" "$DATA_DIR" "$LOG_DIR"
    chmod 700 "$CONFIG_DIR"
    
    log "User and directories setup complete"
}

# Install system dependencies
install_system_dependencies() {
    log "Installing system dependencies..."
    
    # Update package list
    apt-get update
    
    # Install required packages
    apt-get install -y \
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
        openssl
    
    log "System dependencies installed"
}

# Setup Python virtual environment
setup_python_environment() {
    log "Setting up Python virtual environment..."
    
    # Create virtual environment if it doesn't exist
    if [[ ! -d "$VENV_DIR" ]]; then
        python3 -m venv "$VENV_DIR"
        log "Created virtual environment"
    else
        log "Virtual environment already exists"
    fi
    
    # Activate virtual environment and install dependencies
    source "$VENV_DIR/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    if [[ -f "$SCRIPT_DIR/../requirements.txt" ]]; then
        pip install -r "$SCRIPT_DIR/../requirements.txt"
        log "Python dependencies installed"
    else
        error "requirements.txt not found"
        exit 1
    fi
}

# Copy application files
copy_application_files() {
    log "Copying application files..."
    
    # Copy source code
    cp -r "$SCRIPT_DIR/../src" "$PROJECT_DIR/"
    cp "$SCRIPT_DIR/../main.py" "$PROJECT_DIR/"
    
    # Set ownership
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$PROJECT_DIR"
    
    log "Application files copied"
}

# Generate configuration files
generate_configuration() {
    log "Generating configuration files..."
    
    # Generate environment file
    cat > "$CONFIG_DIR/.env" << EOF
# Image Sequence Server Configuration
# Generated by installer on $(date)

# Server settings
HOST=0.0.0.0
PORT=8080
LOG_LEVEL=INFO

# Security settings
SECRET_KEY=$(openssl rand -hex 32)
ALLOWED_HOSTS=*
CORS_ORIGINS=*
RATE_LIMIT_PER_MINUTE=60

# Camera settings
CAMERA_IP=$CAMERA_IP
CAMERA_USERNAME=$CAMERA_USER
CAMERA_PASSWORD=$CAMERA_PASS
CAMERA_PORT=80
CAMERA_SNAPSHOT_PATH=/snapshot.cgi

# Image processing
IMAGE_WIDTH=1920
IMAGE_HEIGHT=1080
IMAGE_QUALITY=85
SEQUENCE_DURATION_MINUTES=5
SEQUENCE_UPDATE_INTERVAL_MINUTES=5
MAX_IMAGES_PER_SEQUENCE=60

# Storage settings
DATA_DIR=$DATA_DIR
IMAGES_DIR=$DATA_DIR/images
SEQUENCES_DIR=$DATA_DIR/sequences
MAX_STORAGE_MB=1024

# Logging
LOG_FILE=$LOG_DIR/app.log

# Performance
MAX_CONCURRENT_CAPTURES=3
IMAGE_CACHE_TTL_SECONDS=300
EOF
    
    # Set ownership
    chown "$SERVICE_USER:$SERVICE_GROUP" "$CONFIG_DIR/.env"
    chmod 600 "$CONFIG_DIR/.env"
    
    log "Configuration files generated"
}

# Setup SSL certificates
setup_ssl_certificates() {
    log "Setting up SSL certificates..."
    
    local ssl_dir="/etc/ssl/imgserv"
    mkdir -p "$ssl_dir"
    
    # Generate self-signed certificate for development
    if [[ "$PRODUCTION" == "false" ]]; then
        openssl req -x509 -newkey rsa:4096 -keyout "$ssl_dir/imgserv.key" \
            -out "$ssl_dir/imgserv.crt" -days 365 -nodes \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        
        # Copy to standard locations
        cp "$ssl_dir/imgserv.crt" /etc/ssl/certs/
        cp "$ssl_dir/imgserv.key" /etc/ssl/private/
        chmod 644 /etc/ssl/certs/imgserv.crt
        chmod 600 /etc/ssl/private/imgserv.key
        
        log "Self-signed SSL certificate generated"
    else
        warn "Production mode: Please install proper SSL certificates"
    fi
}

# Setup systemd service
setup_systemd_service() {
    log "Setting up systemd service..."
    
    cat > /etc/systemd/system/imgserv.service << EOF
[Unit]
Description=Image Sequence Server
After=network.target
Wants=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$PROJECT_DIR
ExecStart=$VENV_DIR/bin/python $PROJECT_DIR/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=imgserv
EnvironmentFile=$CONFIG_DIR/.env

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$DATA_DIR $LOG_DIR
CapabilityBoundingSet=
AmbientCapabilities=
SystemCallFilter=@system-service
SystemCallErrorNumber=EPERM

# Resource limits
MemoryLimit=512M
CPUQuota=50%

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable imgserv.service
    
    log "Systemd service configured"
}

# Configure firewall
configure_firewall() {
    log "Configuring firewall..."
    
    # Enable UFW if not already enabled
    if ! ufw status | grep -q "Status: active"; then
        ufw --force enable
    fi
    
    # Allow SSH
    ufw allow 22/tcp
    
    # Allow HTTP/HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Allow camera access
    ufw allow from 192.168.1.0/24 to any port 80
    ufw allow from 192.168.1.0/24 to any port 443
    
    log "Firewall configured"
}

# Setup nginx reverse proxy
setup_nginx() {
    log "Setting up nginx reverse proxy..."
    
    cat > /etc/nginx/sites-available/imgserv << EOF
server {
    listen 80;
    server_name _;
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name _;
    
    # SSL configuration
    ssl_certificate /etc/ssl/certs/imgserv.crt;
    ssl_certificate_key /etc/ssl/private/imgserv.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/m;
    limit_req zone=api burst=5 nodelay;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # Static files caching
    location ~* \\.(gif|jpg|jpeg|png)\$ {
        proxy_pass http://127.0.0.1:8080;
        expires 1h;
        add_header Cache-Control "public, immutable";
    }
}
EOF
    
    # Enable site
    ln -sf /etc/nginx/sites-available/imgserv /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    # Test nginx configuration
    nginx -t
    
    # Restart nginx
    systemctl restart nginx
    systemctl enable nginx
    
    log "Nginx reverse proxy configured"
}

# Start services
start_services() {
    log "Starting services..."
    
    # Start the main service
    systemctl start imgserv.service
    
    # Check service status
    if systemctl is-active --quiet imgserv.service; then
        log "Image Sequence Server started successfully"
    else
        error "Failed to start Image Sequence Server"
        systemctl status imgserv.service
        exit 1
    fi
    
    log "Services started successfully"
}

# Main installation function
main() {
    log "Starting Image Sequence Server installation..."
    log "Production mode: $PRODUCTION"
    log "Camera IP: $CAMERA_IP"
    log "Camera User: $CAMERA_USER"
    
    check_root
    check_requirements
    setup_user_and_directories
    install_system_dependencies
    setup_python_environment
    copy_application_files
    generate_configuration
    setup_ssl_certificates
    setup_systemd_service
    configure_firewall
    setup_nginx
    start_services
    
    log "Installation completed successfully!"
    log "Service is running at: https://localhost"
    log "Logs available at: $LOG_DIR/app.log"
    log "Configuration at: $CONFIG_DIR/.env"
    
    if [[ "$PRODUCTION" == "false" ]]; then
        warn "Running in development mode with self-signed certificates"
        warn "Replace SSL certificates for production use"
    fi
}

# Run main function
main "$@"
