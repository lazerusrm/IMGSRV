# Changelog

All notable changes to the Image Sequence Server project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2025-10-24

### Added - Major Features
- **Interactive Installer**: Streamlined installation with user prompts
  - Optional VPS setup with yes/no prompt
  - Domain name, SSL email, VPS credentials collection
  - Camera IP, username, password configuration
  - Input validation for domain, email, IP formats
  - DNS propagation check with 30 retries (5 minutes)
  - SSL certificate setup with 3 retry attempts
  - Non-interactive mode support via environment variables
  - Graceful error handling with manual override options
  - Automatic dig installation if needed
- **Inline Road Visualization**: Embedded debugging in config page
  - Live road detection visualization without opening new tabs
  - Refresh button with spinning animation
  - Metadata display: road pixels, coverage %, contours, timestamp
  - Auto-refresh on page load after 1 second
  - Loading and error states
  - Fetches headers for metadata extraction
  - Green overlay showing detected road boundaries
  - Improves UX by keeping all tools on one page

### Enhanced
- **VPS Automation**: Fully automated VPS deployment
  - `setup_vps_with_automation()` orchestrates deployment
  - `check_dns_propagation()` validates DNS before SSL
  - `setup_ssl_with_retry()` handles SSL certificate installation
  - Automatic SSH key deployment to VPS
  - Password-based initial authentication
  - Transition to key-based authentication
  - Error recovery and retry logic
- **Deployment Experience**: Improved installation flow
  - Detect interactive vs non-interactive terminals
  - Use environment variables in CI/CD scenarios
  - Clear progress indicators
  - Helpful error messages
  - Manual override options for edge cases
  - Summary of configured services
- **Configuration Page**: Embedded debugging tools
  - Road visualization inline instead of external link
  - Real-time refresh capability
  - Metadata display below visualization
  - CSS animations for loading states
  - JavaScript fetch API for header extraction

### Fixed
- Non-interactive installer now properly detects TTY
- DNS propagation timeout extended to 5 minutes
- SSL retry logic includes proper wait intervals
- Input validation catches all invalid formats
- IP octet validation (each must be ≤ 255)

### Changed
- Installer now prompts for VPS setup (opt-in instead of mandatory)
- Camera server can run standalone without VPS
- Road boundaries accessible inline, not new tab
- Better separation of camera-only vs full deployment

### Documentation
- Updated README.md with interactive installer examples
- Added non-interactive mode documentation
- Updated CONTEXT.md deployment process
- Documented DNS propagation checking
- Added inline visualization details

## [1.2.0] - 2025-10-24

### Added - Major Features
- **Configurable Update Intervals**: Dynamic GIF generation from 1-30 minutes
  - Preset options: 1, 2, 5, 10, 15, 30 minutes
  - Automatic capture interval calculation
  - Formula: `capture_interval = (update_interval * 60) / max_images`
  - Real-time configuration updates without service restart
- **GIF Optimization**: 60-80% file size reduction
  - Three optimization levels: Low (256 colors), Balanced (192 colors), Aggressive (128 colors)
  - Automatic resize to 1280x720 for web serving
  - Color quantization with dithering for quality preservation
  - Maintains original 1920x1080 source images
- **Road Boundary Visualization**: Debug endpoint for analytics verification
  - `/analytics/road-boundaries` endpoint
  - Real-time visualization with green overlay
  - Metadata in response headers (road pixels, percentage, contours)
  - PNG image output for easy inspection
- **Let's Encrypt SSL Automation**: Fully automated SSL certificate management
  - `deploy/vps-setup-ssl.sh` script for one-command setup
  - DNS validation and health checks
  - Automatic certificate renewal via systemd timer
  - HTTP to HTTPS redirect configuration
  - Domain: woodlandhillswebcam.industrialcamera.com
  - GoDaddy DNS integration instructions
- **Auto-Reload Configuration**: Service automatically applies config changes
  - No manual restart needed for interval changes
  - Graceful reload mechanism
  - Configuration validation before applying
  - Logging of all configuration changes

### Enhanced
- **Configuration UI**: Comprehensive updates to config page
  - Update Interval Settings section
  - GIF Optimization section with explanations
  - Debug Tools section with road boundary link
  - Calculated capture interval display
  - Images per sequence control (5-30)
  - Frame duration control (0.5-5.0 seconds)
- **Dynamic Photo Spacing**: Intelligent capture timing
  - Example: 2-minute updates with 10 images = 12-second captures
  - Example: 5-minute updates with 10 images = 30-second captures
  - Automatic adjustment when configuration changes
- **VPS Deployment**: Enhanced SSL setup instructions
  - Step-by-step GoDaddy DNS configuration
  - DNS propagation checking
  - Certificate verification and testing
  - SSL Labs integration for validation

### Technical Improvements
- **Config Manager**: Added validation for new settings
  - `sequence_update_interval_minutes` (1-60 minutes)
  - `max_images_per_sequence` (1-30 images)
  - `gif_frame_duration_seconds` (0.1-5.0 seconds)
  - `gif_optimization_level` (low, balanced, aggressive)
  - `get_capture_interval()` method for dynamic calculation
- **Image Processor**: Enhanced GIF creation
  - Pillow LANCZOS resampling for quality
  - Adaptive palette color quantization
  - Optimize flag enabled
  - Quality parameter based on optimization level
  - File size logging for monitoring
- **Sequence Service**: Reload mechanism
  - `reload_config()` method for graceful restart
  - Cancel and restart capture loop
  - Apply new timing immediately
  - Preserve service state during reload
- **Snow Analytics**: Road visualization
  - `visualize_road_boundaries()` method in RoadDetector
  - Semi-transparent green overlay (30% opacity)
  - Contour drawing for boundary clarity
  - Metadata calculation and reporting

### Documentation
- **README.md**: Comprehensive updates
  - SSL setup section with Let's Encrypt instructions
  - GoDaddy DNS configuration steps
  - Update interval configuration guide
  - Road boundary debugging instructions
  - GIF optimization explanations
  - Enhanced troubleshooting (7 new sections)
  - SSL certificate troubleshooting
  - Configuration reload troubleshooting
- **CHANGELOG.md**: Detailed feature documentation
- **DEPLOYMENT.md**: SSL deployment procedures (if exists)

### Performance
- **GIF File Sizes**: 60-80% reduction
  - Before: ~2-4 MB per GIF (1920x1080, 256 colors)
  - After: ~400-800 KB per GIF (1280x720, 192 colors balanced)
  - Maintains visual quality with balanced optimization
  - Faster page loads and reduced bandwidth
- **Capture Efficiency**: Optimized timing
  - 2-minute updates: 12-second intervals (10 images)
  - 5-minute updates: 30-second intervals (10 images)
  - 10-minute updates: 60-second intervals (10 images)
  - Configurable images per sequence for flexibility

### Security
- **SSL/TLS**: Production-grade certificates
  - Let's Encrypt automated setup
  - TLS 1.2 and 1.3 support
  - Strong cipher suites
  - HSTS enabled
  - OCSP stapling
- **Configuration Access**: Enhanced logging
  - All configuration changes logged with client IP
  - Reload events tracked
  - Failed reload attempts logged
  - Security monitoring integration

### API Changes
- **New Endpoints**:
  - `GET /analytics/road-boundaries`: Road detection visualization
- **Enhanced Endpoints**:
  - `POST /config/analytics`: Now includes auto-reload trigger
  - Returns reload status in response

### Breaking Changes
None - Fully backward compatible with V1.1.0

### Migration Notes
- Existing configurations will continue to work
- New settings have sensible defaults
- Update interval defaults to 5 minutes (unchanged)
- GIF optimization defaults to "balanced"
- Recommended: Review and adjust update intervals in config UI
- Optional: Run SSL setup script for HTTPS

### Known Issues
- networkoptix-mediaserver package configuration errors (handled gracefully)
- First SSL certificate request requires 5-30 min DNS propagation
- Let's Encrypt rate limit: 5 certificates per week per domain

### Upgrade Instructions
1. Pull latest code: `git pull origin main`
2. Restart service: `systemctl restart imgserv`
3. Access config UI: `http://camera-server:8080/config`
4. Review and adjust update intervals
5. (Optional) Setup SSL: `bash vps-setup-ssl.sh your-email@example.com`

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
