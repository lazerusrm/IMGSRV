# IMGSRV - Project Context & Architecture

**Version:** 2.0.0  
**Last Updated:** 2025-10-24    
**Project Type:** Python + Bash deployment scripts  
**Primary Use:** Snow load monitoring webcam system for Woodland Hills City Center

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Two-Server Architecture](#two-server-architecture)
3. [Development Environment](#development-environment)
4. [System Architecture](#system-architecture)
5. [Technology Stack](#technology-stack)
6. [Directory Structure](#directory-structure)
7. [Key Components](#key-components)
8. [Configuration](#configuration)
9. [Deployment Process](#deployment-process)
10. [Common Tasks](#common-tasks)
11. [Troubleshooting](#troubleshooting)
12. [Future Development](#future-development)

---

## Project Overview

IMGSRV is a production-grade IP camera snapshot system that:
- Captures frames from an RTSP camera stream using ffmpeg
- Generates traffic camera-style animated GIF sequences
- Performs snow load analytics using computer vision
- Integrates real-time weather data from NOAA API
- Serves content via a public HTTPS website
- Runs in a secure two-server architecture

**End Goal:** Provide a reliable, automated snow load monitoring system with public web access, optimized GIF delivery, configurable update intervals, and comprehensive analytics.

---

## Two-Server Architecture

### Critical Design Decision
The system uses TWO separate servers for security and network isolation:

```
┌─────────────────────────────────────┐
│  CAMERA SERVER (Internal/Private)  │
│  ─────────────────────────────────  │
│  • LXC Container on Proxmox        │
│  • IP: 192.168.1.110 (Camera)      │
│  • Captures images via RTSP        │
│  • Generates GIF sequences         │
│  • Runs analytics                  │
│  • Stores configuration            │
│  • NO public internet access       │
│                                     │
│  SSH Keys: /opt/imgserv/.ssh/      │
│  Config: /etc/imgserv/.env         │
└──────────┬──────────────────────────┘
           │ RSYNC over SSH
           │ (One-way sync)
           ▼
┌─────────────────────────────────────┐
│    VPS SERVER (Public-Facing)      │
│  ─────────────────────────────────  │
│  • RackNerd VPS                    │
│  • IP: 198.23.249.133              │
│  • Domain: woodlandhillswebcam     │
│           .industrialcamera.com    │
│  • Serves GIFs via nginx           │
│  • HTTPS with Let's Encrypt       │
│  • NO processing or analytics      │
│  • NO configuration access         │
└─────────────────────────────────────┘
```

**Why This Architecture?**
1. **Security:** Camera server behind firewall/NAT, no open ports
2. **Isolation:** Configuration and analytics stay private
3. **Simplicity:** VPS only serves static content
4. **Cost:** Minimal VPS resources needed (512MB RAM)

---

## Development Environment

### Camera Server (Primary Development)
- **Host:** Proxmox VE
- **Container:** LXC (Debian/Ubuntu based)
- **OS:** Debian 11+ or Ubuntu 20.04+
- **Python:** 3.11+
- **Shell:** Bash
- **User:** root (for system service management)
- **Service User:** imgserv (non-root, runs the service)

### VPS Server (Public Content)
- **Provider:** RackNerd (https://www.racknerd.com)
- **IP:** 198.23.249.133
- **OS:** Ubuntu 24.04 LTS
- **Domain:** woodlandhillswebcam.industrialcamera.com
- **DNS:** GoDaddy (A record for industrialcamera.com)
- **Web Server:** nginx
- **SSL:** Let's Encrypt (certbot)
- **User:** root (for SSH access from camera server)

### Camera Details
- **Model:** PG2056IRC-ZS (Chinese ONVIF camera)
- **IP:** 192.168.1.110
- **Protocol:** RTSP (rtsp://admin:123456@192.168.1.110:554/stream0)
- **Resolution:** 1920x1080
- **Username:** admin
- **Password:** 123456

### Key Contact
- **Email:** brad@industrialcamera.com (for Let's Encrypt, support)
- **GitHub:** lazerusrm

---

## System Architecture

### Core Services Flow

```
Camera (RTSP) → ffmpeg → Python Service → GIF Generation
                              ↓
                      Analytics Engine
                      (Computer Vision)
                              ↓
                      Weather API (NOAA)
                              ↓
                      Overlay Generation
                              ↓
                    Save to /var/lib/imgserv
                              ↓
                      RSYNC to VPS
                              ↓
                    VPS nginx serves HTTPS
```

### Data Flow
1. **Capture:** ffmpeg pulls frames from RTSP every 12-60 seconds (configurable)
2. **Store:** Images saved to `/var/lib/imgserv/images/`
3. **Analyze:** Computer vision detects road boundaries and surface conditions
4. **Weather:** NOAA API provides temperature, snow depth, precipitation
5. **Generate:** Create GIF sequence with overlays every 2-30 minutes (configurable)
6. **Sync:** RSYNC pushes GIF to VPS over SSH
7. **Serve:** VPS nginx serves via HTTPS with auto-refresh HTML

---

## Technology Stack

### Backend (Camera Server)
- **Language:** Python 3.11+
- **Framework:** FastAPI + uvicorn
- **Image Processing:** Pillow (PIL), ffmpeg
- **Computer Vision:** OpenCV (cv2), NumPy
- **HTTP Client:** aiohttp
- **Config:** pydantic-settings
- **Logging:** structlog
- **Monitoring:** prometheus-client
- **Rate Limiting:** slowapi

### Frontend (VPS)
- **Web Server:** nginx
- **SSL:** certbot (Let's Encrypt)
- **Content:** Static HTML + GIF files
- **Auto-refresh:** HTML meta refresh (300 seconds)
- **Mobile:** Responsive CSS design

### System Integration
- **Service:** systemd (imgserv.service)
- **Sync:** rsync over SSH with key authentication
- **Firewall:** ufw (VPS), iptables (camera server)
- **Deployment:** Bash scripts

### APIs
- **Weather:** NOAA API (api.weather.gov)
  - Forecast endpoint for predictions
  - Observation stations for current conditions
  - No API key required

---

## Directory Structure

```
/opt/imgserv/                    # Main installation directory
├── main.py                      # Entry point
├── requirements.txt             # Python dependencies
├── VERSION                      # Version number (1.2.0)
├── CHANGELOG.md                 # Release history
├── README.md                    # User documentation
├── CONTEXT.md                   # This file (AI reference)
├── src/
│   ├── app.py                  # FastAPI application
│   ├── config.py               # Settings & environment variables
│   ├── services/
│   │   ├── camera.py           # RTSP capture via ffmpeg
│   │   ├── image_processor.py # GIF generation & optimization
│   │   ├── sequence_service.py# Orchestration & timing
│   │   ├── storage.py          # File management
│   │   ├── vps_sync.py         # RSYNC to VPS
│   │   ├── snow_analytics.py   # Computer vision analytics
│   │   ├── analytics_overlay.py# Overlay generation
│   │   └── config_manager.py   # Dynamic configuration
│   ├── templates/
│   │   └── config_page.py      # Configuration UI HTML
│   └── utils/
│       └── logging.py          # Structured logging setup
├── deploy/
│   ├── autoinstall.sh          # One-command installer
│   ├── install.sh              # Manual installer
│   ├── update-camera.sh        # Update camera server
│   ├── update-vps-remote.sh    # Update VPS remotely
│   ├── setup-ssl-remote.sh     # SSL setup (remote)
│   ├── setup-ssl-fresh.sh      # SSL setup (force fresh)
│   ├── install-ssl-cert.sh     # Install obtained certificate
│   ├── vps-deploy.sh           # VPS initial setup
│   ├── setup-vps.sh            # Automated VPS setup
│   ├── fix-vps-dpkg.sh         # Fix dpkg issues
│   ├── fix-env.sh              # Fix .env syntax
│   └── vps-setup-ssl.sh        # SSL setup script (runs on VPS)
└── tests/
    └── test_imgserv.py         # Test suite

/etc/imgserv/                    # Configuration directory
├── .env                         # Environment variables
└── analytics_config.json        # Dynamic analytics config

/var/lib/imgserv/                # Data directory
├── images/                      # Captured frames
├── sequences/                   # Generated GIFs
└── analytics/                   # Analytics history

/var/log/imgserv/                # Logs
└── app.log                      # Application logs

/opt/imgserv/.ssh/               # SSH keys for VPS sync
├── vps_key                      # Private key
└── vps_key.pub                  # Public key

/etc/systemd/system/
└── imgserv.service              # Systemd service

VPS: /var/www/html/monitoring/   # Public web root
├── index.html                   # Main page (auto-generated)
├── iframe.html                  # Iframe endpoint
└── sequence_*.gif               # Synced GIF files
```

---

## Key Components

### 1. Camera Service (`src/services/camera.py`)
- Uses `ffmpeg` subprocess to capture frames from RTSP
- Handles connection errors with exponential backoff
- Returns JPEG image data and timestamp
- No HTTP snapshots (switched from aiohttp to ffmpeg in V1.0)

### 2. Image Processor (`src/services/image_processor.py`)
- Creates animated GIFs from image sequences
- **Removed Timestamp Overlays:** No longer adds redundant timestamps (handled by analytics overlay)
- Applies analytics overlays (minimal driver-focused design)
- **Deprecated Legacy Methods:** `add_timestamp_overlay()` marked as deprecated
- **GIF Optimization:**
  - Resizes to 1280x720 (from 1920x1080)
  - Color quantization (128-256 colors)
  - LANCZOS resampling for quality
  - 60-80% file size reduction
  - Typical output: 400-800 KB per GIF

### 3. Sequence Service (`src/services/sequence_service.py`)
- Orchestrates the entire capture → process → sync workflow
- **Dynamic Timing:**
  - Capture interval = (update_interval_minutes × 60) / max_images
  - Example: 2-min updates, 10 images = 12-second captures
  - Example: 5-min updates, 10 images = 30-second captures
- Handles service reload without full restart
- Manages error recovery with exponential backoff

### 4. VPS Synchronizer (`src/services/vps_sync.py`)
- RSYNC over SSH with key authentication
- One-way sync (camera → VPS)
- Automatically fixes VPS permissions after sync
- Updates `index.html` with latest GIF reference
- Verifies sync success via file count

### 5. Snow Analytics (`src/services/snow_analytics.py`)
- **RoadDetector:** Detects road boundaries using edge detection
- **RoadSurfaceAnalyzer:** Analyzes snow/wet/ice coverage via computer vision
- **WeatherDataClient:** Fetches real-time data from NOAA API
- **SnowAnalytics:** Combines vision + weather for accurate reporting
- **Simplified Driver Alerts:** Clear, Light, Moderate, Heavy, Ice Possible
- **Raw Image Processing:** Analytics performed on uncompressed camera data for maximum accuracy
- **24-Hour Forecast Integration:** Provides specific snow/ice alerts with times

### 6. Analytics Overlay (`src/services/analytics_overlay.py`)
- **Continuous Black Bar Design:** Professional black bar across bottom 1/8th of image
- **Strategic Positioning:** 
  - Top-left: Location name only ("Woodland Hills City Center") with individual background box
  - Bottom: Continuous black bar with all analytics data overlaid horizontally
- **Font Sizes:** Uniform 36px font size for all analytics text elements
- **Horizontal Layout:** Road Condition → Alerts → Timestamp → Temperature (far right)
- **Color-Coded Status:** Green (Clear), Yellow (Light), Orange (Moderate), Red (Heavy), Purple (Ice Possible)
- **Enhanced Readability:** White/yellow text on continuous black background for maximum visibility
- **Deprecated Legacy Methods:** Old overlay system marked as deprecated with warnings

### 7. Configuration Manager (`src/services/config_manager.py`)
- Manages `/etc/imgserv/analytics_config.json`
- Validates all configuration changes
- Provides `get_capture_interval()` for dynamic timing
- Supports real-time updates without service restart

---

## Configuration

### Environment Variables (`/etc/imgserv/.env`)

```bash
# Camera Settings
CAMERA_IP=192.168.1.110
CAMERA_USERNAME=admin
CAMERA_PASSWORD=123456
CAMERA_PORT=554
CAMERA_RTSP_PATH=/stream0
CAMERA_RESOLUTION=1920x1080

# Image Processing (Base Defaults)
IMAGE_WIDTH=1920
IMAGE_HEIGHT=1080
IMAGE_QUALITY=85
SEQUENCE_DURATION_MINUTES=5      # Time span of image sequence
SEQUENCE_UPDATE_INTERVAL_MINUTES=5  # How often to generate new GIF
MAX_IMAGES_PER_SEQUENCE=10       # Frames per GIF

# Storage
DATA_DIR=/var/lib/imgserv
MAX_STORAGE_MB=1024

# Server
HOST=0.0.0.0
PORT=8080
WORKERS=1
RATE_LIMIT_PER_MINUTE=60

# Security
SECRET_KEY=<generate-with-openssl-rand-hex-32>

# VPS Synchronization
VPS_ENABLED=true
VPS_HOST=198.23.249.133
VPS_USER=root
VPS_PORT=22
VPS_REMOTE_PATH=/var/www/html/monitoring
VPS_SSH_KEY_PATH=/opt/imgserv/.ssh/vps_key
VPS_RSYNC_OPTIONS="-avz --delete"

# Analytics (Base Defaults - overridden by analytics_config.json)
ANALYTICS_ENABLED=true
ANALYTICS_UPDATE_INTERVAL_MINUTES=5
WEATHER_API_ENABLED=true
WEATHER_LATITUDE=40.011771        # Woodland Hills, Utah
WEATHER_LONGITUDE=-111.648000
ANALYTICS_OVERLAY_ENABLED=true
ANALYTICS_OVERLAY_STYLE=minimal
```

### Dynamic Configuration (`/etc/imgserv/analytics_config.json`)

Managed via web UI at `http://camera-server:8080/config`

```json
{
  "analytics_enabled": true,
  "analytics_update_interval_minutes": 5,
  "weather_api_enabled": true,
  "weather_latitude": 40.011757,
  "weather_longitude": -111.648119,
  "weather_location_name": "Woodland Hills City, Utah",
  "analytics_overlay_enabled": true,
  "analytics_overlay_style": "minimal",
  "snow_detection_threshold": 0.7,
  "ice_warning_temperature": 32,
  "hazardous_snow_depth": 2.0,
  "sequence_update_interval_minutes": 5,
  "max_images_per_sequence": 10,
  "gif_frame_duration_seconds": 1.0,
  "gif_optimization_level": "balanced",
  "road_roi_points": [],
  "road_roi_enabled": false,
  "last_updated": "2025-10-24T..."
}
```

**Interactive ROI Configuration:**
- **Canvas-based polygon editor** for defining road monitoring regions
- **Click-to-add points** (4-12 points) on live camera feed
- **Normalized coordinates** (0-1 scale) for resolution independence
- **Visual feedback** with blue overlay and red first point marker
- **Test functionality** to preview ROI on road detection visualization
- **Enable/disable toggle** to switch between custom and default detection

**Configuration Changes Apply Immediately** - Service auto-reloads capture loop.

---

## Deployment Process

### Interactive Installation (Recommended)

The installer now supports interactive configuration for streamlined setup:

```bash
# Interactive installation with prompts
curl -sSL https://raw.githubusercontent.com/lazerusrm/IMGSRV/main/autoinstall.sh | bash

# You will be prompted for:
# 1. VPS setup (y/N) - optional
# 2. Domain name (e.g., webcam.example.com)
# 3. SSL email (for Let's Encrypt)
# 4. VPS IP address
# 5. VPS username (default: root)
# 6. VPS password (for SSH key setup)
# 7. Camera IP (default: 192.168.1.110)
# 8. Camera username (default: admin)
# 9. Camera password (default: 123456)

# Features:
# - Input validation (domain format, email format, IP validation)
# - DNS propagation check with 30 retries (5 minutes)
# - Automatic VPS deployment
# - SSL certificate setup with 3 retries
# - Graceful error handling
# - Non-interactive mode support (env vars)
```

### Non-Interactive Installation

For automated deployments or CI/CD, set environment variables:

```bash
# Camera-only setup (no VPS)
CAMERA_IP=192.168.1.110 \
CAMERA_USER=admin \
CAMERA_PASS=123456 \
curl -sSL https://raw.githubusercontent.com/lazerusrm/IMGSRV/main/autoinstall.sh | bash

# Full setup with VPS
DOMAIN_NAME=webcam.example.com \
SSL_EMAIL=admin@example.com \
VPS_IP=198.23.249.133 \
VPS_USER=root \
VPS_PASSWORD=secretpassword \
CAMERA_IP=192.168.1.110 \
CAMERA_USER=admin \
CAMERA_PASS=123456 \
curl -sSL https://raw.githubusercontent.com/lazerusrm/IMGSRV/main/autoinstall.sh | bash
```

### What the Installer Does

**Camera Server:**
1. Installs system dependencies (ffmpeg, python3, nginx, jq, rsync, sshpass, etc.)
2. Creates imgserv user and directories
3. Clones repository to /opt/imgserv
4. Sets up Python venv and installs packages
5. Creates systemd service
6. Configures nginx reverse proxy
7. **ENHANCED VPS CONFIGURATION DETECTION:**
   - Automatically detects existing VPS configuration in /etc/imgserv/.env
   - Preserves VPS settings during environment file updates
   - Auto-detects Woodland Hills VPS (198.23.249.133) from existing config
   - Excludes false positives (0.0.0.0, local IPs) from detection
8. **INTELLIGENT SSH KEY MANAGEMENT:**
   - Preserves existing SSH keys if they exist and work
   - Validates SSH key integrity (regenerates corrupted keys)
   - Automatically deploys SSH key to VPS when configuration detected
   - Single password prompt for SSH key deployment
   - Tests SSH and RSYNC connectivity after deployment
9. Starts service

**VPS Server (if configured):**
1. Installs nginx, openssl, ufw
2. Creates web directories at /var/www/html/monitoring
3. Configures nginx with self-signed SSL
4. Sets up imgserv user for RSYNC
5. Configures firewall (ports 80, 443, 22)
6. Checks DNS propagation
7. Installs Let's Encrypt SSL certificate
8. Creates monitoring scripts

### Manual VPS Setup (Alternative)

If you prefer manual VPS setup or the automated setup fails:

```bash
# Option 1: Automated from camera server
sudo bash /opt/imgserv/deploy/setup-vps.sh <vps-ip> <vps-user> <vps-password>

# Option 2: Manual on VPS
curl -sSL https://raw.githubusercontent.com/lazerusrm/IMGSRV/main/deploy/vps-deploy.sh | bash
```

### SSH Key Setup (Camera → VPS)

```bash
# Keys generated automatically during install at:
# /opt/imgserv/.ssh/vps_key (private)
# /opt/imgserv/.ssh/vps_key.pub (public)

# Public key must be added to VPS:
# /root/.ssh/authorized_keys

# Interactive installer handles this automatically
# Manual: ssh-copy-id -i /opt/imgserv/.ssh/vps_key root@<vps-ip>
```

### SSL Certificate Setup (Let's Encrypt)

```bash
# Prerequisites:
# 1. DNS A record: woodlandhillswebcam.industrialcamera.com → 198.23.249.133
# 2. Wait 5-30 minutes for DNS propagation
# 3. Ports 80 and 443 open on VPS

# From camera server:
sudo bash /opt/imgserv/deploy/setup-ssl-fresh.sh

# What it does:
# 1. Checks DNS resolution
# 2. Installs certbot on VPS
# 3. Obtains certificate from Let's Encrypt
# 4. Configures nginx for HTTPS
# 5. Sets up HTTP → HTTPS redirect
# 6. Enables auto-renewal (systemd timer)

# Certificate location on VPS:
# /etc/letsencrypt/live/woodlandhillswebcam.industrialcamera.com/
```

---

## Common Tasks

### Update Camera Server

```bash
cd /opt/imgserv
git pull origin main
sudo bash deploy/update-camera.sh

# Or one-liner:
curl -sSL https://raw.githubusercontent.com/lazerusrm/IMGSRV/main/deploy/update-camera.sh | sudo bash
```

### Update VPS (No Login Required)

```bash
# From camera server:
sudo bash /opt/imgserv/deploy/update-vps-remote.sh

# What it does:
# - Fixes permissions on VPS
# - Restarts nginx
# - Updates index.html
# - Forces RSYNC sync
# - Tests endpoints
```

### Change Update Interval

```bash
# Via Web UI (preferred):
# 1. Open http://camera-server:8080/config
# 2. Change "GIF Update Interval" (1-30 minutes)
# 3. Adjust "Images Per Sequence" (5-30)
# 4. Click "Save Configuration"
# Service auto-reloads with new timing

# Example timings:
# - 2 min updates, 10 images = 12-second captures
# - 5 min updates, 10 images = 30-second captures
# - 10 min updates, 15 images = 40-second captures
```

### View Logs

```bash
# Camera server service logs
journalctl -u imgserv -f

# Filter for specific events
journalctl -u imgserv -n 100 | grep -i "rsync\|analytics\|error"

# VPS nginx logs
ssh -i /opt/imgserv/.ssh/vps_key root@198.23.249.133
journalctl -u nginx -f
```

### Test Endpoints

```bash
# Camera server (internal)
curl http://localhost:8080/health
curl http://localhost:8080/status | jq
curl http://localhost:8080/analytics | jq
curl -I http://localhost:8080/analytics/road-boundaries

# VPS (public)
curl -I https://woodlandhillswebcam.industrialcamera.com
curl https://woodlandhillswebcam.industrialcamera.com/health
```

### Manual Service Management

```bash
# Camera server
systemctl status imgserv
systemctl restart imgserv
systemctl stop imgserv
systemctl start imgserv

# VPS nginx
ssh -i /opt/imgserv/.ssh/vps_key root@198.23.249.133
systemctl status nginx
systemctl reload nginx
```

### Force GIF Generation

```bash
# Trigger immediate sequence generation
curl http://localhost:8080/status

# Check if new GIF was created
ls -lht /var/lib/imgserv/sequences/ | head -5

# Manually sync to VPS
sudo bash /opt/imgserv/deploy/update-vps-remote.sh
```

---

## Troubleshooting

### Common Issues

#### 1. Camera Connection Failed
```bash
# Test RTSP stream
ffmpeg -i rtsp://admin:123456@192.168.1.110:554/stream0 -vframes 1 -f image2 test.jpg

# Check camera settings
grep CAMERA /etc/imgserv/.env

# View camera errors
journalctl -u imgserv -n 50 | grep -i camera
```

#### 2. GIF Not Updating
```bash
# Check service status
systemctl status imgserv

# View capture loop
journalctl -u imgserv -f | grep -i "capture\|sequence"

# Check update interval config
cat /etc/imgserv/analytics_config.json | jq '.sequence_update_interval_minutes'

# Check for errors
journalctl -u imgserv -n 100 | grep -i error
```

#### 3. VPS Not Receiving Files
```bash
# Test SSH connection
ssh -i /opt/imgserv/.ssh/vps_key root@198.23.249.133 "echo 'SSH OK'"

# Check RSYNC logs
journalctl -u imgserv -n 50 | grep -i rsync

# Manually trigger sync
sudo bash /opt/imgserv/deploy/update-vps-remote.sh

# Check VPS files
ssh -i /opt/imgserv/.ssh/vps_key root@198.23.249.133 "ls -lh /var/www/html/monitoring/"
```

#### 4. SSL Certificate Issues
```bash
# Check certificate status on VPS
ssh -i /opt/imgserv/.ssh/vps_key root@198.23.249.133 "certbot certificates"

# Test renewal
ssh -i /opt/imgserv/.ssh/vps_key root@198.23.249.133 "certbot renew --dry-run"

# Check nginx SSL config
ssh -i /opt/imgserv/.ssh/vps_key root@198.23.249.133 "nginx -t"

# View certificate logs
ssh -i /opt/imgserv/.ssh/vps_key root@198.23.249.133 "cat /var/log/letsencrypt/letsencrypt.log"
```

#### 5. Configuration Not Applying
```bash
# Check if service reloaded
journalctl -u imgserv -n 20 | grep -i reload

# Manually restart
systemctl restart imgserv

# Verify config file
cat /etc/imgserv/analytics_config.json | jq '.'

# Check for validation errors
journalctl -u imgserv -n 50 | grep -i "config\|validation"
```

#### 6. Analytics Showing No Data
```bash
# Check analytics status
curl http://localhost:8080/analytics | jq '.status'

# View analytics logs
journalctl -u imgserv -n 100 | grep -i analytics

# Test weather API
curl "https://api.weather.gov/points/40.011771,-111.648000" | jq

# Check road boundary visualization
curl -I http://localhost:8080/analytics/road-boundaries
```

#### 7. High GIF File Sizes
```bash
# Check current optimization level
cat /etc/imgserv/analytics_config.json | jq '.gif_optimization_level'

# Change to aggressive (via config UI or manually)
# Expected sizes:
# - Low: 1-2 MB
# - Balanced: 400-800 KB (recommended)
# - Aggressive: 200-400 KB

# Check actual file sizes
ls -lh /var/lib/imgserv/sequences/*.gif
```

### Performance Issues

```bash
# Check resource usage
htop
df -h /var/lib/imgserv

# Check service memory
systemctl status imgserv | grep -i memory

# Reduce capture frequency (via config UI)
# or edit /etc/imgserv/analytics_config.json

# Clear old images
find /var/lib/imgserv/images -name "*.jpg" -mtime +1 -delete

# Clear old sequences
find /var/lib/imgserv/sequences -name "*.gif" -mtime +7 -delete
```

### Network Issues

```bash
# Test camera network
ping 192.168.1.110

# Test VPS network
ping 198.23.249.133

# Test DNS
dig woodlandhillswebcam.industrialcamera.com

# Check firewall on camera server
iptables -L -n

# Check firewall on VPS
ssh -i /opt/imgserv/.ssh/vps_key root@198.23.249.133 "ufw status"
```

---

## Future Development

### Potential Enhancements

1. **Multi-Camera Support**
   - Track multiple cameras simultaneously
   - Separate update intervals per camera
   - Combined dashboard view

2. **Advanced Analytics**
   - Machine learning for snow depth estimation
   - Historical trend analysis
   - Predictive alerts based on forecast data

3. **WebP Format Support**
   - Even smaller file sizes than GIF
   - Better compression for modern browsers
   - Fallback to GIF for older browsers

4. **Real-Time Alerts**
   - Email/SMS notifications for hazardous conditions
   - Webhook integration
   - Discord/Slack notifications

5. **Custom ROI Selection**
   - Web UI for drawing road boundaries
   - Per-camera analytics configuration
   - Save/load ROI presets

6. **Database Integration**
   - Store analytics history in PostgreSQL/SQLite
   - API for historical data queries
   - Graphing and trend visualization

7. **Mobile App**
   - Native iOS/Android apps
   - Push notifications
   - Offline viewing of cached sequences

8. **CDN Integration**
   - CloudFlare or similar for global distribution
   - Edge caching for faster load times
   - Reduced VPS bandwidth usage

### Code Quality Improvements

- Increase test coverage (currently minimal)
- Add integration tests for VPS sync
- Implement CI/CD pipeline improvements
- Add metrics dashboard (Prometheus + Grafana)
- Improve error handling and recovery
- Add configuration validation UI

---

## Important Notes for AI Assistants

### When Making Changes:

1. **Always test in dev first:** Changes affect production monitoring
2. **Respect the two-server architecture:** Camera server = processing, VPS = serving
3. **Maintain backward compatibility:** Existing configs must continue working
4. **Update version numbers:** Increment VERSION file and CHANGELOG.md
5. **Test both servers:** Changes may affect camera server, VPS, or both
6. **Document all changes:** Update README.md and this CONTEXT.md
7. **Consider bandwidth:** VPS has 500GB monthly transfer limit
8. **Preserve security:** Never expose camera credentials, keep config on camera server
9. **Test SSL carefully:** Let's Encrypt rate limits (5 certs/week/domain)
10. **Validate all configs:** Use ConfigManager validation before applying
11. **ENSURE IDEMPOTENCY:** All installers and scripts must be safe to run multiple times
12. **PRESERVE EXISTING KEYS:** Never regenerate SSH keys if they exist and work
13. **TEST CONNECTIVITY:** Always verify SSH/RSYNC before making changes
14. **VALIDATE VPS STATE:** Check nginx/SSL status before offering setup options
15. **PRESERVE VPS CONFIG:** Never overwrite existing VPS settings in .env files
16. **AUTO-DETECT VPS:** Use intelligent detection patterns for VPS configuration
17. **SINGLE PASSWORD PROMPT:** Deploy SSH keys automatically, prompt password only once

### Common Mistakes to Avoid:

- ❌ DON'T expose configuration endpoints on VPS
- ❌ DON'T store credentials in git (use .env files)
- ❌ DON'T use Python docstrings (""") in bash scripts
- ❌ DON'T forget to escape special chars in bash
- ❌ DON'T hardcode timing values (use config)
- ❌ DON'T assume VPS has same packages as camera server
- ❌ DON'T forget to reload service after config changes
- ❌ DON'T break RSYNC (it's the critical link)
- ❌ DON'T regenerate SSH keys if they exist and work
- ❌ DON'T run installers without testing connectivity first
- ❌ DON'T assume VPS needs setup without checking current state
- ❌ DON'T overwrite existing VPS settings in .env files
- ❌ DON'T prompt for password multiple times (deploy SSH key once)
- ❌ DON'T detect 0.0.0.0 or local IPs as VPS configurations

### Testing Checklist:

- [ ] Camera captures frames successfully
- [ ] GIF sequences generate correctly
- [ ] Analytics data appears in overlays
- [ ] RSYNC syncs to VPS
- [ ] VPS serves content over HTTPS
- [ ] Config changes apply without restart
- [ ] SSL certificate auto-renews
- [ ] All logs show no errors
- [ ] Performance is acceptable
- [ ] Documentation is updated

---

## Quick Reference

### Key URLs
- **Public Website:** https://woodlandhillswebcam.industrialcamera.com
- **Camera Server API:** http://localhost:8080 (internal only)
- **Configuration UI:** http://localhost:8080/config (internal only)
  - Interactive configuration page with live road detection visualization
  - Inline road boundary display with metadata (road pixels, coverage %, contours)
  - Refresh button for real-time boundary visualization
  - All settings save without service restart
- **Analytics API:** http://localhost:8080/analytics (internal only)
- **Road Boundaries:** http://localhost:8080/analytics/road-boundaries (internal only, embedded in config page)

### Key Paths
- **Camera Server Code:** /opt/imgserv
- **Camera Server Config:** /etc/imgserv/.env
- **Dynamic Config:** /etc/imgserv/analytics_config.json
- **Data Storage:** /var/lib/imgserv
- **SSH Keys:** /opt/imgserv/.ssh/vps_key
- **Service File:** /etc/systemd/system/imgserv.service
- **VPS Web Root:** /var/www/html/monitoring
- **SSL Certificates:** /etc/letsencrypt/live/woodlandhillswebcam.industrialcamera.com/

### Key Commands
```bash
# Update camera server
curl -sSL https://raw.githubusercontent.com/lazerusrm/IMGSRV/main/deploy/update-camera.sh | sudo bash

# Update VPS (from camera server)
sudo bash /opt/imgserv/deploy/update-vps-remote.sh

# Restart service
systemctl restart imgserv

# View logs
journalctl -u imgserv -f

# Test everything
curl http://localhost:8080/status | jq
```

---

**End of Context Document**

*This document should be updated whenever significant architectural changes are made.*

