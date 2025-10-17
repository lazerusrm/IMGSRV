#!/bin/bash
"""
VPS Deployment Script for Image Sequence Server

This script sets up the public-facing VPS server to serve the synchronized content.
Run this on your VPS server after setting up RSYNC synchronization.
"""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
WEB_ROOT="/var/www/html/monitoring"
NGINX_CONFIG="/etc/nginx/sites-available/monitoring"
SERVICE_USER="imgserv"

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
    echo -e "${BLUE}[VPS-DEPLOY]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
        echo "Please run: sudo bash $0"
        exit 1
    fi
}

# Install required packages
install_packages() {
    log "Installing required packages..."
    
    apt-get update
    apt-get install -y nginx rsync
    
    log "Packages installed successfully"
}

# Create web directory structure
setup_web_directory() {
    log "Setting up web directory structure..."
    
    # Create web root directory
    mkdir -p "$WEB_ROOT"
    
    # Create placeholder files
    cat > "$WEB_ROOT/index.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Woodland Hills City Center - Snow Load Monitoring</title>
    <meta http-equiv="refresh" content="300">
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            margin: 0;
            padding: 20px;
            background-color: #f0f0f0;
        }
        .container {
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            max-width: 800px;
            margin: 0 auto;
        }
        .error {
            color: red;
            font-size: 18px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Woodland Hills City Center</h1>
        <h2>Snow Load Monitoring</h2>
        <div class="error">Waiting for content synchronization...</div>
        <p>Content will appear here once RSYNC synchronization begins.</p>
    </div>
</body>
</html>
EOF

    # Create iframe page
    cat > "$WEB_ROOT/iframe.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Snow Load Monitoring - Iframe</title>
    <meta http-equiv="refresh" content="300">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 10px;
            background-color: #f0f0f0;
        }
        .container {
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background-color: #2c3e50;
            color: white;
            padding: 15px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 1.8em;
            font-weight: bold;
        }
        .header h2 {
            margin: 5px 0 0 0;
            font-size: 1.2em;
            font-weight: normal;
            opacity: 0.9;
        }
        .content {
            padding: 15px;
            text-align: center;
        }
        .camera-image {
            max-width: 100%;
            height: auto;
            border: 2px solid #ddd;
            border-radius: 4px;
        }
        .info {
            margin-top: 15px;
            color: #666;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Woodland Hills City Center</h1>
            <h2>Snow Load Monitoring</h2>
        </div>
        <div class="content">
            <div class="error">Waiting for content synchronization...</div>
            <div class="info">
                <p>Content will appear here once RSYNC synchronization begins.</p>
            </div>
        </div>
    </div>
</body>
</html>
EOF

    # Set proper permissions
    chown -R www-data:www-data "$WEB_ROOT"
    chmod -R 755 "$WEB_ROOT"
    
    # Create auto-update script for index.html
    cat > "/usr/local/bin/update-monitoring-index.sh" << 'EOF'
#!/bin/bash
# Auto-update index.html with latest GIF

WEB_ROOT="/var/www/html/monitoring"
LATEST_GIF=$(ls -t "$WEB_ROOT"/sequence_*.gif 2>/dev/null | head -1)

if [ -n "$LATEST_GIF" ]; then
    GIF_NAME=$(basename "$LATEST_GIF")
    cat > "$WEB_ROOT/index.html" << HTML_EOF
<!DOCTYPE html>
<html>
<head>
    <title>Woodland Hills City Center - Snow Load Monitoring</title>
    <meta http-equiv="refresh" content="300">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f0f0f0;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2em;
        }
        .header h2 {
            margin: 5px 0 0 0;
            font-size: 1.2em;
            opacity: 0.9;
        }
        .content {
            padding: 20px;
            text-align: center;
        }
        .camera-image {
            max-width: 100%;
            height: auto;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .info {
            margin-top: 20px;
            color: #666;
        }
        .refresh-info {
            font-size: 0.9em;
            color: #888;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Woodland Hills City Center</h1>
            <h2>Snow Load Monitoring</h2>
        </div>
        <div class="content">
            <img src="$GIF_NAME" alt="Snow Load Monitoring GIF" class="camera-image">
            <div class="info">
                <p>GIF updates every 5 minutes</p>
                <div class="refresh-info">
                    Page refreshes automatically every 5 minutes
                </div>
            </div>
        </div>
    </div>
</body>
</html>
HTML_EOF
    chown www-data:www-data "$WEB_ROOT/index.html"
    chmod 644 "$WEB_ROOT/index.html"
fi
EOF
    
    chmod +x "/usr/local/bin/update-monitoring-index.sh"
    
    log "Web directory structure created with auto-update script"
}

# Configure nginx
setup_nginx() {
    log "Configuring nginx with HTTPS..."
    
    # Create SSL directory and self-signed certificate
    mkdir -p /etc/nginx/ssl
    if [ ! -f /etc/nginx/ssl/monitoring.crt ]; then
        log "Generating self-signed SSL certificate..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout /etc/nginx/ssl/monitoring.key \
            -out /etc/nginx/ssl/monitoring.crt \
            -subj "/C=US/ST=California/L=Woodland Hills/O=City Center/CN=monitoring" \
            2>/dev/null || warn "SSL certificate generation failed"
    fi
    
    # Create nginx configuration with HTTPS
    cat > "$NGINX_CONFIG" << EOF
# HTTP to HTTPS redirect
server {
    listen 80;
    server_name _;
    return 301 https://\$host\$request_uri;
}

# HTTPS server
server {
    listen 443 ssl;
    server_name _;
    root $WEB_ROOT;
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
        try_files \$uri \$uri/ /index.html;
    }
    
    # Iframe endpoint
    location /iframe {
        try_files \$uri /iframe.html;
    }
    
    # API endpoints (if needed)
    location /api/ {
        return 404;
    }
    
    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

    # Enable the site
    ln -sf "$NGINX_CONFIG" /etc/nginx/sites-enabled/
    
    # Remove default nginx site
    rm -f /etc/nginx/sites-enabled/default
    
    # Test nginx configuration
    nginx -t
    
    if [ $? -eq 0 ]; then
        log "Nginx configuration is valid"
        systemctl reload nginx
        log "Nginx reloaded successfully"
    else
        error "Nginx configuration test failed"
        exit 1
    fi
}

# Setup SSH access for RSYNC
setup_ssh_access() {
    log "Setting up SSH access for RSYNC..."
    
    # Create imgserv user if it doesn't exist
    if ! id "$SERVICE_USER" &>/dev/null; then
        # Create user with proper home directory (not system user)
        useradd -m -s /bin/bash "$SERVICE_USER" || error "Failed to create user '$SERVICE_USER'."
        log "Created user: $SERVICE_USER with home directory /home/$SERVICE_USER"
    else
        log "User '$SERVICE_USER' already exists."
    fi
    
    # Create SSH directory
    mkdir -p "/home/$SERVICE_USER/.ssh"
    chown -R "$SERVICE_USER:$SERVICE_USER" "/home/$SERVICE_USER/.ssh"
    chmod 700 "/home/$SERVICE_USER/.ssh"
    
    # Create authorized_keys placeholder
    touch "/home/$SERVICE_USER/.ssh/authorized_keys"
    chown "$SERVICE_USER:$SERVICE_USER" "/home/$SERVICE_USER/.ssh/authorized_keys"
    chmod 600 "/home/$SERVICE_USER/.ssh/authorized_keys"
    
    log "SSH access configured for user: $SERVICE_USER"
    warn "Please add the public key from your camera server to: /home/$SERVICE_USER/.ssh/authorized_keys"
}

# Create monitoring script
create_monitoring_script() {
    log "Creating monitoring script..."
    
    cat > "/usr/local/bin/monitor-sync.sh" << 'EOF'
#!/bin/bash
# Monitor RSYNC synchronization status

WEB_ROOT="/var/www/html/monitoring"
LOG_FILE="/var/log/monitor-sync.log"

# Check if content exists
if [ -f "$WEB_ROOT/latest_sequence.gif" ] || [ -f "$WEB_ROOT/sequence_*.gif" ]; then
    echo "$(date): Content synchronized successfully" >> "$LOG_FILE"
    exit 0
else
    echo "$(date): WARNING - No synchronized content found" >> "$LOG_FILE"
    exit 1
fi
EOF

    chmod +x "/usr/local/bin/monitor-sync.sh"
    
    # Create logrotate configuration
    cat > "/etc/logrotate.d/monitor-sync" << EOF
/var/log/monitor-sync.log {
    daily
    missingok
    rotate 7
    compress
    notifempty
    create 644 root root
}
EOF

    log "Monitoring script created"
}

# Main installation function
main() {
    info "Starting VPS deployment for Image Sequence Server"
    
    check_root
    install_packages
    setup_web_directory
    setup_nginx
    setup_ssh_access
    create_monitoring_script
    
    info "VPS deployment completed successfully!"
    
    echo ""
    echo "Next steps:"
    echo "1. Add SSH public key to: /home/$SERVICE_USER/.ssh/authorized_keys"
    echo "2. Configure VPS settings on your camera server:"
    echo "   VPS_ENABLED=true"
    echo "   VPS_HOST=$(hostname -I | awk '{print $1}')"
    echo "   VPS_USER=$SERVICE_USER"
    echo "3. Test the setup: curl http://$(hostname -I | awk '{print $1}')/health"
    echo ""
    echo "Your VPS is ready to serve synchronized content!"
}

# Run main function
main "$@"
