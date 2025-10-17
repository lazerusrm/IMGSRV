"""
Environment configuration and systemd service files for production deployment.
"""

# Systemd service file
SYSTEMD_SERVICE = """[Unit]
Description=Image Sequence Server
After=network.target
Wants=network.target

[Service]
Type=simple
User=imgserv
Group=imgserv
WorkingDirectory=/opt/imgserv
ExecStart=/opt/imgserv/venv/bin/python /opt/imgserv/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=imgserv

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/imgserv /var/log/imgserv
CapabilityBoundingSet=
AmbientCapabilities=
SystemCallFilter=@system-service
SystemCallErrorNumber=EPERM

# Resource limits
MemoryLimit=512M
CPUQuota=50%

[Install]
WantedBy=multi-user.target
"""

# Environment file template
ENV_TEMPLATE = """# Image Sequence Server Configuration
# Copy this file to /etc/imgserv/.env and modify as needed

# Server settings
HOST=0.0.0.0
PORT=8080
LOG_LEVEL=INFO

# Security settings
SECRET_KEY=CHANGE_THIS_IN_PRODUCTION
ALLOWED_HOSTS=*
CORS_ORIGINS=*
RATE_LIMIT_PER_MINUTE=60

# Camera settings
CAMERA_IP=192.168.1.110
CAMERA_USERNAME=admin
CAMERA_PASSWORD=123456
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
DATA_DIR=/var/lib/imgserv
IMAGES_DIR=/var/lib/imgserv/images
SEQUENCES_DIR=/var/lib/imgserv/sequences
MAX_STORAGE_MB=1024

# Logging
LOG_FILE=/var/log/imgserv/app.log

# Performance
MAX_CONCURRENT_CAPTURES=3
IMAGE_CACHE_TTL_SECONDS=300
"""

# Nginx configuration template
NGINX_CONFIG = """server {
    listen 80;
    server_name _;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
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
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/m;
    limit_req zone=api burst=5 nodelay;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # Static files caching
    location ~* \\.(gif|jpg|jpeg|png)$ {
        proxy_pass http://127.0.0.1:8080;
        expires 1h;
        add_header Cache-Control "public, immutable";
    }
}
"""

# Firewall rules (UFW)
FIREWALL_RULES = """# Image Sequence Server Firewall Rules
# Allow SSH
ufw allow 22/tcp

# Allow HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Allow camera access (adjust IP range as needed)
ufw allow from 192.168.1.0/24 to any port 80
ufw allow from 192.168.1.0/24 to any port 443

# Deny all other traffic
ufw default deny incoming
ufw default allow outgoing

# Enable firewall
ufw --force enable
"""
