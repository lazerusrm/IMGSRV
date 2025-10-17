# Changelog

All notable changes to the Image Sequence Server project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-10-17

### Added
- **Automated VPS Setup Script**: Complete one-command VPS deployment
  - `deploy/setup-vps.sh` for automated VPS configuration
  - Automatic SSH key generation and distribution
  - VPS server deployment with nginx
  - imgserv user creation and SSH key setup
  - Camera server configuration automation
  - Service restart and testing
  - Complete status reporting and next steps
- **Enhanced Documentation**: Updated README with automated setup instructions
- **jq Dependency**: Added to autoinstall.sh for JSON parsing

### Improved
- **Setup Process**: Reduced from 30+ minutes to 5 minutes
- **Error Handling**: Eliminated common SSH key permission issues
- **User Experience**: Single command handles entire VPS setup
- **Reliability**: Automated testing and validation

### Technical Details
- Automated VPS deployment via `curl -sSL ... | bash -s -- <ip> <user> <pass>`
- Secure SSH key management with proper permissions
- Complete VPS server configuration with nginx
- Camera server `.env` configuration automation
- Service restart and status verification

## [1.0.0] - 2025-10-17

### Added
- Initial release of Image Sequence Server
- RTSP camera integration using ffmpeg
- Traffic camera-style image sequences with timestamp overlays
- Web interface with auto-refresh every 5 minutes
- Automatic service installation and configuration
- Security hardening with rate limiting and input validation
- Storage management with automatic cleanup
- Systemd service integration
- Nginx reverse proxy support
- Docker containerization support
- GitHub Actions CI/CD pipeline
- Comprehensive error handling and logging

### Features
- **RTSP Camera Support**: Connects to `rtsp://admin:123456@192.168.1.110:554/stream0`
- **Image Processing**: Captures frames every 45 seconds, creates 10-image GIFs
- **Animation**: 1 FPS playback for smooth viewing
- **Branding**: "Woodland Hills City Center - Snow Load Monitoring"
- **Security**: Timestamp sanitization (rounded to 5-minute intervals)
- **Storage**: Automatic cleanup with 1GB limit
- **Updates**: New GIF every 5 minutes
- **Web Interface**: Professional municipal monitoring display

### Technical Details
- **Language**: Python 3.11+
- **Framework**: FastAPI with uvicorn
- **Image Processing**: Pillow (PIL) with ffmpeg
- **Database**: File-based storage
- **Authentication**: Basic HTTP auth for camera
- **Logging**: Structured logging with structlog
- **Monitoring**: Prometheus metrics support

### Installation
- **One-Command Install**: `curl -sSL https://raw.githubusercontent.com/lazerusrm/IMGSRV/main/autoinstall.sh | bash`
- **Supported OS**: Debian/Ubuntu, RedHat/CentOS, Arch Linux
- **Dependencies**: ffmpeg, Python 3.8+, systemd, nginx

### Security Features
- Rate limiting (60 requests/minute)
- Input validation and sanitization
- CORS protection
- HTTPS support with self-signed certificates
- Non-root user execution
- Systemd security features (NoNewPrivileges, PrivateTmp, ProtectSystem)

### Known Issues
- networkoptix-mediaserver package may show configuration errors (handled gracefully)
- Service requires restart after code updates (automated in installer)

### License
Proprietary software - All rights reserved. See LICENSE file for details.
