# Image Sequence Server

**Version: 1.0.0** | **Release Date: 2025-10-17**

**⚠️ PROPRIETARY SOFTWARE - ALL RIGHTS RESERVED**

This software is proprietary and confidential. Unauthorized use, copying, modification, distribution, or reverse engineering is strictly prohibited.

## License

This software is licensed under a proprietary license. See [LICENSE](LICENSE) for details.

**You may NOT:**
- Use this software without explicit written permission
- Copy, modify, or distribute this software
- Reverse engineer or create derivative works
- Remove copyright notices

For licensing inquiries, contact: lazerusrm

---

## Overview

A secure, efficient service for capturing IP camera snapshots and generating traffic camera-style image sequences for web display. Designed for deployment in Proxmox LXC containers with comprehensive security hardening.

## Features

- **RTSP Camera Integration**: Secure RTSP stream capture using ffmpeg
- **Traffic Camera Style**: Professional timestamp overlays and image sequences
- **Security Hardened**: Rate limiting, input validation, HTTPS, and isolation
- **Resource Optimized**: Minimal memory and CPU usage for LXC containers
- **Production Ready**: Systemd service, nginx reverse proxy, SSL certificates
- **Auto-refresh**: Web interface updates every 5 minutes
- **Storage Management**: Automatic cleanup and storage monitoring

## Quick Start

### 🚀 One-Command Installation (Linux)

**Single Universal Installer (Handles all cases including package conflicts):**

```bash
curl -sSL https://raw.githubusercontent.com/lazerusrm/IMGSRV/main/autoinstall.sh | bash
```

**Ultra-Simple Installation (Bypasses most errors):**

```bash
curl -sSL https://raw.githubusercontent.com/lazerusrm/IMGSRV/main/simple-install.sh | bash
```

**Minimal Installation:**

```bash
curl -sSL https://raw.githubusercontent.com/lazerusrm/IMGSRV/main/install.sh | bash
```

**Manual Download:**

```bash
wget https://raw.githubusercontent.com/lazerusrm/IMGSRV/main/autoinstall.sh
chmod +x autoinstall.sh
sudo ./autoinstall.sh
```

### 🪟 Windows Development Setup

For Windows development/testing:

```powershell
# Run as Administrator
Set-ExecutionPolicy Bypass -Scope Process -Force
iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/lazerusrm/IMGSRV/main/install-windows.ps1'))
```

### 📋 Manual Installation (Advanced)

If you prefer manual installation:

**Prerequisites:**
- Linux system (Ubuntu 20.04+ recommended)
- Python 3.8+
- Root access for installation
- IP camera with ONVIF support

**Steps:**
1. **Clone the repository**:
   ```bash
   git clone https://github.com/lazerusrm/IMGSRV.git
   cd IMGSRV
   ```

2. **Run the installer**:
   ```bash
   # Development installation
   sudo ./deploy/install.sh
   
   # Production installation with custom camera settings
   sudo ./deploy/install.sh --production --camera-ip 192.168.1.110 --camera-user admin --camera-pass yourpassword
   ```

3. **Access the service**:
   - Web interface: `https://your-server-ip`
   - API status: `https://your-server-ip/status`
   - Health check: `https://your-server-ip/health`

## Configuration

The service is configured via environment variables in `/etc/imgserv/.env`:

### Camera Settings
```bash
CAMERA_IP=192.168.1.110
CAMERA_USERNAME=admin
CAMERA_PASSWORD=123456
CAMERA_PORT=554
CAMERA_RTSP_PATH=/stream0
CAMERA_RESOLUTION=1920x1080
```

### Image Processing
```bash
IMAGE_WIDTH=1920
IMAGE_HEIGHT=1080
IMAGE_QUALITY=85
SEQUENCE_DURATION_MINUTES=5
SEQUENCE_UPDATE_INTERVAL_MINUTES=5
MAX_IMAGES_PER_SEQUENCE=10
```

### Security Settings
```bash
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=*
CORS_ORIGINS=*
RATE_LIMIT_PER_MINUTE=60
```

## Architecture

### Components

1. **Camera Service** (`src/services/camera.py`)
   - ONVIF camera integration
   - Secure authentication
   - Snapshot capture with error handling

2. **Image Processor** (`src/services/image_processor.py`)
   - Traffic camera-style timestamp overlays
   - Image sequence generation (animated GIF)
   - Storage cleanup

3. **Storage Manager** (`src/services/storage.py`)
   - File storage and organization
   - Storage monitoring and cleanup
   - Recent image retrieval

4. **Web Server** (`src/app.py`)
   - FastAPI application
   - Security middleware
   - Auto-refresh interface

5. **Sequence Service** (`src/services/sequence_service.py`)
   - Main orchestration service
   - Background image capture
   - Sequence generation coordination

### Security Features

- **Input Validation**: All user inputs are validated and sanitized
- **Rate Limiting**: Configurable rate limits per endpoint
- **HTTPS Only**: SSL/TLS encryption with security headers
- **User Isolation**: Runs as dedicated `imgserv` user
- **Resource Limits**: Memory and CPU constraints
- **Firewall Rules**: UFW configuration for network security
- **Systemd Security**: NoNewPrivileges, PrivateTmp, ProtectSystem

## API Endpoints

### Web Interface
- `GET /` - Main traffic camera interface with auto-refresh
- `GET /sequence/latest` - Latest image sequence (GIF)

### API Endpoints
- `GET /status` - Service status and statistics
- `GET /health` - Health check endpoint

## Deployment

### Proxmox LXC Container

1. **Create LXC container**:
   ```bash
   # Ubuntu 22.04 template recommended
   # Minimum: 1GB RAM, 2GB storage, 1 CPU core
   ```

2. **Install dependencies**:
   ```bash
   apt update && apt upgrade -y
   apt install -y git curl
   ```

3. **Clone and install**:
   ```bash
   git clone https://github.com/yourusername/image-sequence-server.git
   cd image-sequence-server
   sudo ./deploy/install.sh --production
   ```

### Docker Deployment (Alternative)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY main.py .

EXPOSE 8080
CMD ["python", "main.py"]
```

## Monitoring

### Service Status
```bash
# Check service status
systemctl status imgserv

# View logs
journalctl -u imgserv -f

# Check storage usage
curl https://your-server/status
```

### Log Files
- Application logs: `/var/log/imgserv/app.log`
- System logs: `journalctl -u imgserv`
- Nginx logs: `/var/log/nginx/`

## Troubleshooting

### Common Issues

1. **Camera Connection Failed**
   ```bash
   # Test camera connectivity
   # Test RTSP stream access
   ffmpeg -i rtsp://admin:123456@192.168.1.110:554/stream0 -vframes 1 -f image2 test.jpg
   
   # Check camera settings in /etc/imgserv/.env
   ```

2. **Service Won't Start**
   ```bash
   # Check logs
   journalctl -u imgserv -n 50
   
   # Verify configuration
   sudo -u imgserv python /opt/imgserv/main.py
   ```

3. **Storage Issues**
   ```bash
   # Check storage usage
   df -h /var/lib/imgserv
   
   # Manual cleanup
   sudo -u imgserv find /var/lib/imgserv -name "*.jpg" -mtime +1 -delete
   ```

### Performance Tuning

1. **Memory Optimization**:
   ```bash
   # Reduce image quality
   IMAGE_QUALITY=70
   
   # Reduce sequence duration
   SEQUENCE_DURATION_MINUTES=3
   ```

2. **CPU Optimization**:
   ```bash
   # Reduce capture frequency
   # Edit src/services/sequence_service.py line 95
   await asyncio.sleep(60)  # Change from 30 to 60 seconds
   ```

## Security Considerations

### Production Deployment

1. **Change Default Credentials**:
   ```bash
   # Update camera password
   CAMERA_PASSWORD=your-secure-password
   
   # Generate new secret key
   SECRET_KEY=$(openssl rand -hex 32)
   ```

2. **SSL Certificates**:
   ```bash
   # Install Let's Encrypt certificates
   certbot --nginx -d your-domain.com
   ```

3. **Network Security**:
   ```bash
   # Restrict camera access
   ufw allow from 192.168.1.0/24 to any port 80
   ufw deny 80
   ```

### CVE Protection

- **Dependencies**: All packages are pinned to specific versions
- **Updates**: Regular security updates via `apt update && apt upgrade`
- **Monitoring**: Security headers and rate limiting enabled
- **Isolation**: Service runs in restricted environment

## Development

### Local Development

1. **Setup environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run locally**:
   ```bash
   python main.py
   ```

3. **Run tests**:
   ```bash
   pytest tests/
   ```

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/image-sequence-server/issues)
- **Documentation**: [Wiki](https://github.com/yourusername/image-sequence-server/wiki)
- **Security**: Report security issues privately to lazerusrm

## Changelog

### v1.0.0
- Initial release
- ONVIF camera integration
- Traffic camera-style interface
- Security hardening
- Production deployment scripts

---

**⚠️ REMINDER: This is proprietary software. Unauthorized use is prohibited.**