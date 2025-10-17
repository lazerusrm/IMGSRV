# Image Sequence Server

A secure, efficient service for capturing IP camera snapshots and generating traffic camera-style image sequences for web display.

## Features

- ONVIF camera integration with secure authentication
- Traffic camera-style timestamp overlays and image sequences
- Comprehensive security hardening (rate limiting, HTTPS, input validation)
- Resource-optimized for Proxmox LXC containers
- Production-ready deployment with systemd service and nginx reverse proxy
- Auto-refresh web interface
- Automatic storage management and cleanup

## Quick Start

```bash
# Clone repository
git clone https://github.com/yourusername/image-sequence-server.git
cd image-sequence-server

# Install (development mode)
sudo ./deploy/install.sh

# Install (production mode)
sudo ./deploy/install.sh --production --camera-ip 192.168.1.110 --camera-user admin --camera-pass yourpassword
```

## Access

- Web Interface: `https://your-server-ip`
- API Status: `https://your-server-ip/status`
- Health Check: `https://your-server-ip/health`

## Configuration

Edit `/etc/imgserv/.env` to customize settings:

```bash
# Camera settings
CAMERA_IP=192.168.1.110
CAMERA_USERNAME=admin
CAMERA_PASSWORD=123456

# Image processing
IMAGE_WIDTH=1920
IMAGE_HEIGHT=1080
SEQUENCE_DURATION_MINUTES=5
SEQUENCE_UPDATE_INTERVAL_MINUTES=5
```

## Security Features

- HTTPS with security headers
- Rate limiting and input validation
- User isolation and resource limits
- Firewall configuration
- Systemd security restrictions

## Monitoring

```bash
# Service status
systemctl status imgserv

# View logs
journalctl -u imgserv -f

# Check storage
curl https://your-server/status
```

## Requirements

- Linux system (Ubuntu 20.04+ recommended)
- Python 3.8+
- IP camera with ONVIF support
- Minimum: 1GB RAM, 2GB storage, 1 CPU core

## License

MIT License - see [LICENSE](LICENSE) for details.
