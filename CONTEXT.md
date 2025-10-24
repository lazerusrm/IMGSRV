# IMGSRV - Agent Context & Instructions

## 🎯 Purpose

This file provides context for future development sessions to maintain consistency and avoid documentation sprawl. It serves as the single source of truth for how developers and AI tools should interact with the IMGSRV codebase.

---

## 📚 Documentation Structure (STRICT - Do Not Deviate)

### **Core Documentation Files (Only These 6)**

1. **README.md** - Main entry point
   - Quick start (5 minutes)
   - Features overview
   - Setup instructions
   - Troubleshooting

2. **CHANGELOG.md** - Version history
   - Follows Keep a Changelog format
   - Never consolidate or remove
   - Update with each release

3. **CONTEXT.md** - This file (Agent instructions)
   - Architecture overview
   - Coding conventions
   - Common patterns
   - Development guidelines

4. **COSTING.md** - Budget & financial analysis
   - Monthly/annual operating costs
   - Cost optimization features
   - Municipal budget justification
   - ROI analysis

5. **SECURITY.md** - Security architecture
   - Two-server security model
   - Configuration system security
   - Access control guidelines

6. **DEPLOYMENT.md** - Operations guide
   - Production deployment
   - Environment configuration
   - Maintenance procedures
   - Monitoring & scaling

### ⚠️ **IMPORTANT RULES**

**DO NOT:**
- ❌ Create new documentation files
- ❌ Create status/summary/complete documents
- ❌ Create multiple guides for same topic
- ❌ Duplicate information across files

**DO:**
- ✅ Update existing documentation files
- ✅ Add sections to appropriate doc
- ✅ Keep docs in sync with code
- ✅ Follow the 6-file structure

---

## 🏗️ Project Architecture

### Tech Stack

**Backend (Camera Server):**
- Python 3.11+ + FastAPI + uvicorn
- OpenCV (cv2) + NumPy (computer vision)
- Pillow (PIL) + ffmpeg (image processing)
- aiohttp (HTTP client)
- structlog (structured logging)
- pydantic-settings (configuration)

**Frontend (VPS Server):**
- nginx (web server)
- Static HTML + GIF files
- Auto-refresh (HTML meta refresh)
- Let's Encrypt SSL

**Infrastructure:**
- Two-server architecture (security isolation)
- systemd service management
- RSYNC over SSH (one-way sync)
- LXC container deployment

**APIs:**
- NOAA Weather API (api.weather.gov) - FREE
- ONVIF Camera Protocol (RTSP)

### Current Version

**Version**: 2.0.0  
**Release Date**: October 24, 2025  
**Status**: Production Ready - Professional Overlay System Complete

---

## 💰 Cost Management Strategy

### Operating Costs (Monthly)

**Total Monthly Cost: $4.75**  
**Total Annual Cost: $57.00**

| Component | Monthly Cost | Provider | Purpose |
|-----------|-------------|----------|---------|
| **VPS Hosting** | $3.50 | RackNerd | Public content serving |
| **Domain & DNS** | $1.25 | GoDaddy | Domain management |
| **SSL Certificates** | $0.00 | Let's Encrypt | HTTPS encryption |

### Cost Optimization Features

✅ **DO:**
- Use efficient GIF compression (60-80% size reduction)
- Implement smart storage management (automatic cleanup)
- Optimize for minimal resource usage (LXC containers)
- Serve static content only on VPS (no processing)
- Monitor bandwidth usage (~9GB/month vs 1TB limit)

❌ **DON'T:**
- Process analytics on VPS (keep on camera server)
- Store configuration on VPS (security risk)
- Use expensive APIs when free alternatives exist
- Over-provision VPS resources

### Cost Per Citizen Analysis
- **Population**: ~1,000 residents (estimated)
- **Cost Per Citizen**: <$0.01/month
- **Annual Cost Per Citizen**: <$0.06/year
- **Public Safety Value**: 24/7 road condition monitoring

---

## 📁 Project Structure

```
IMGSRV/
├── src/
│   ├── app.py                  # FastAPI application (main entry)
│   ├── config.py               # Settings & environment variables
│   ├── services/
│   │   ├── camera.py           # RTSP capture via ffmpeg
│   │   ├── image_processor.py  # GIF generation & optimization
│   │   ├── sequence_service.py # Orchestration & timing
│   │   ├── storage.py          # File management
│   │   ├── vps_sync.py         # RSYNC to VPS
│   │   ├── snow_analytics.py   # Computer vision analytics
│   │   ├── analytics_overlay.py# Overlay generation
│   │   └── config_manager.py   # Dynamic configuration
│   ├── templates/
│   │   └── config_page.py      # Configuration UI HTML
│   └── utils/
│       ├── logging.py          # Structured logging setup
│       └── security.py         # Security utilities
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
├── tests/
│   └── test_imgserv.py         # Test suite
├── main.py                     # Entry point
├── requirements.txt            # Python dependencies
├── VERSION                     # Single source of truth (v2.0.0)
├── CHANGELOG.md               # Version history
├── README.md                  # Main documentation
├── CONTEXT.md                 # This file (Agent instructions)
├── COSTING.md                 # Budget & financial analysis
├── SECURITY.md                # Security architecture
├── DEPLOYMENT.md              # Operations guide
└── docker-compose.yml         # Container deployment option
```

---

## 🔑 Key Locations

**Core Services**: `src/services/`
- `camera.py` - RTSP capture using ffmpeg subprocess
- `image_processor.py` - GIF generation with optimization (60-80% size reduction)
- `sequence_service.py` - Main orchestration service
- `storage.py` - File management with automatic cleanup
- `vps_sync.py` - RSYNC over SSH with key authentication
- `snow_analytics.py` - Computer vision road detection & surface analysis
- `analytics_overlay.py` - Professional overlay system (v2.0.0)
- `config_manager.py` - Dynamic configuration management

**Configuration**: `/etc/imgserv/`
- `.env` - Environment variables (camera, VPS, analytics settings)
- `analytics_config.json` - Dynamic configuration (web UI managed)

**Data Storage**: `/var/lib/imgserv/`
- `images/` - Captured frames (auto-cleanup)
- `sequences/` - Generated GIFs (rotating)
- `analytics/` - Analytics history

**SSH Keys**: `/opt/imgserv/.ssh/`
- `vps_key` - Private key for VPS sync
- `vps_key.pub` - Public key

**Service**: `/etc/systemd/system/imgserv.service`

**VPS Web Root**: `/var/www/html/monitoring/`
- `index.html` - Main page (auto-generated)
- `sequence_*.gif` - Synced GIF files

---

## 💡 Coding Conventions

### Language & Terminology

**Use Professional Terms:**
- ✅ "Road condition monitoring"
- ✅ "Computer vision analytics"
- ✅ "Real-time weather integration"
- ✅ "Professional overlay system"
- ✅ "Traffic camera-style interface"
- ❌ "AI-powered" (avoid buzzwords)
- ❌ "Smart camera" (too generic)

**Feature Naming:**
- "Snow load monitoring" not "AI snow detection"
- "Road surface analysis" not "AI road analysis"
- "Weather integration" not "AI weather"
- "Professional overlays" not "AI overlays"

### Code Style

**Backend (Python):**
- Follow PEP 8
- Type hints for function parameters
- Docstrings for all classes and methods
- Use f-strings for formatting
- Descriptive variable names
- Async/await for I/O operations

**Configuration:**
- Use pydantic-settings for validation
- Environment variables for secrets
- JSON for dynamic configuration
- Validate all inputs

**Error Handling:**
- Use structlog for structured logging
- Graceful degradation
- Exponential backoff for retries
- Clear error messages

### File Organization

- One service per file
- Group related utilities
- Separate concerns (camera, processing, sync, analytics)
- Clear naming conventions

---

## 🔧 Common Tasks

### Adding a New Feature

1. Update appropriate service in `src/services/`
2. Add configuration options to `config.py` and `analytics_config.json`
3. Update web UI in `src/templates/config_page.py` if needed
4. Add tests in `tests/`
5. Update `CHANGELOG.md`
6. Update `VERSION` file

### Adding Configuration Options

1. Add to `src/config.py` with validation
2. Add to `src/services/config_manager.py` for dynamic updates
3. Update web UI in `src/templates/config_page.py`
4. Test configuration changes apply without restart
5. Document in `README.md`

### Deploying an Update

1. Update `VERSION` file
2. Update `CHANGELOG.md`
3. Test on camera server: `systemctl restart imgserv`
4. Test VPS sync: `sudo bash /opt/imgserv/deploy/update-vps-remote.sh`
5. Monitor: `journalctl -u imgserv -f`

### Adding Analytics Features

1. Update `src/services/snow_analytics.py` for new detection
2. Update `src/services/analytics_overlay.py` for display
3. Test with real camera data
4. Update configuration options
5. Document in `README.md`

---

## 🚨 Critical Rules

### Architecture

1. **Two-Server Model**: Camera server = processing, VPS = serving only
2. **Security Isolation**: Configuration stays on camera server
3. **One-Way Sync**: Camera → VPS only (no reverse sync)
4. **Static Content**: VPS serves only static files
5. **No Processing on VPS**: All analytics on camera server

### Documentation

1. **Never create new .md files** without explicit approval
2. Always update existing documentation
3. Keep README.md as the entry point
4. CHANGELOG.md follows Keep a Changelog format
5. Use CONTEXT.md for development guidelines

### Code Changes

1. Never expose camera credentials publicly
2. Always validate configuration changes
3. Use structured logging for all operations
4. Handle edge cases gracefully
5. Test both camera server and VPS after changes

### Deployment

1. Always backup configuration before changes
2. Test SSH/RSYNC connectivity before deployment
3. Monitor logs after deployment
4. Verify VPS content updates correctly
5. Check SSL certificate status

---

## 📊 Key Metrics

**Services**: 8 core services  
**Configuration Files**: 2 (static + dynamic)  
**Documentation Files**: 6 (keep it this way!)  
**Deploy Scripts**: 12  
**Monthly Operating Cost**: $4.75  
**Annual Operating Cost**: $57.00  
**Cost Per Citizen**: <$0.01/month  

---

## 🎯 Design Principles

1. **Security First**: Two-server architecture with proper isolation
2. **Cost Effective**: Minimal VPS resources, efficient processing
3. **Reliability**: Robust error handling, automatic recovery
4. **Simplicity**: Clear separation of concerns
5. **Professional**: Traffic camera-style interface
6. **Maintainable**: Structured logging, clear configuration
7. **Municipal Focus**: Public safety, budget-conscious

---

## 🔐 Environment Configuration

**Camera Server (`/etc/imgserv/.env`):**

**Required:**
- `CAMERA_IP` - Camera IP address
- `CAMERA_USERNAME` - Camera username
- `CAMERA_PASSWORD` - Camera password
- `SECRET_KEY` - Application secret key

**VPS Sync:**
- `VPS_ENABLED=true`
- `VPS_HOST` - VPS IP address
- `VPS_USER=root`
- `VPS_SSH_KEY_PATH=/opt/imgserv/.ssh/vps_key`

**Analytics:**
- `ANALYTICS_ENABLED=true`
- `WEATHER_LATITUDE` - Location latitude
- `WEATHER_LONGITUDE` - Location longitude

**Optional:**
- `IMAGE_QUALITY=85` - JPEG quality
- `SEQUENCE_UPDATE_INTERVAL_MINUTES=5` - Update frequency
- `MAX_STORAGE_MB=1024` - Storage limit

**Dynamic Configuration (`/etc/imgserv/analytics_config.json`):**
- Managed via web UI at `http://camera-server:8080/config`
- Real-time updates without service restart
- Validated before applying changes

---

## 🎓 Architectural Decisions

### Why Two-Server Architecture?
- **Security**: Camera server behind firewall, no public exposure
- **Isolation**: Configuration and analytics stay private
- **Simplicity**: VPS only serves static content
- **Cost**: Minimal VPS resources needed

### Why FastAPI?
- **Performance**: Async/await for I/O operations
- **Validation**: Built-in request/response validation
- **Documentation**: Automatic API documentation
- **Type Safety**: Python type hints support

### Why OpenCV + NumPy?
- **Computer Vision**: Road detection and surface analysis
- **Performance**: Optimized C++ backend
- **Ecosystem**: Mature library with good documentation
- **Integration**: Works well with Python ecosystem

### Why RSYNC over SSH?
- **Security**: Encrypted transfer with key authentication
- **Reliability**: Built-in retry and resume capabilities
- **Efficiency**: Only transfers changed files
- **Simplicity**: Standard Unix tool

### Why Let's Encrypt?
- **Free**: No SSL certificate costs
- **Automated**: Auto-renewal with systemd timers
- **Trusted**: Widely accepted by browsers
- **Simple**: Easy setup and maintenance

---

## 🚨 Critical Design Decisions

### Professional Overlay System (v2.0.0)

**IMPORTANT**: The overlay system was completely redesigned in v2.0.0 for professional appearance and readability.

**Key Changes:**
1. **Continuous Black Bar**: Replaced individual text boxes with professional black bar across bottom 1/8th
2. **Horizontal Layout**: Road Condition → Alerts → Timestamp → Temperature (far right)
3. **Uniform Font Sizes**: All analytics text uses consistent 36px font
4. **Enhanced Readability**: White/yellow text on continuous black background
5. **Strategic Positioning**: Top-left location name, bottom analytics bar

**Implementation:**
- ✅ `src/services/analytics_overlay.py` - `create_minimal_overlay()` method
- ✅ Deprecated legacy overlay methods with warnings
- ✅ Color-coded road conditions (Green, Yellow, Orange, Red, Purple)
- ✅ Dynamic positioning with bounds checking
- ✅ 30px spacing between elements

**Rationale:**
This provides a professional, traffic camera-style appearance that's highly readable
against any background while maintaining all essential information in a clean layout.

### Raw Image Processing

**IMPORTANT**: Analytics are performed on raw image data directly from the camera, before any compression.

**Why Raw Processing:**
1. **Maximum Accuracy**: No compression artifacts affecting analysis
2. **Better Detection**: Higher quality data for computer vision
3. **Consistent Results**: Same quality regardless of storage settings
4. **Future-Proof**: Ready for higher resolution cameras

**Implementation:**
- ✅ `src/services/sequence_service.py` - `analyze_raw_image()` called before saving
- ✅ `src/services/snow_analytics.py` - `analyze_raw_image()` method
- ✅ Raw bytes processed directly from camera capture

### Configuration Management

**IMPORTANT**: Configuration is split between static (environment) and dynamic (web UI) settings.

**Static Configuration** (`/etc/imgserv/.env`):
- Camera credentials
- VPS connection details
- Basic service settings
- Security keys

**Dynamic Configuration** (`/etc/imgserv/analytics_config.json`):
- Analytics settings
- Update intervals
- ROI boundaries
- Overlay preferences
- Real-time updates without restart

**Rationale:**
This allows for secure credential storage while providing flexible runtime configuration
for operational adjustments without service restarts.

---

## 🚀 Quick Commands

```bash
# Start service
systemctl start imgserv

# View logs
journalctl -u imgserv -f

# Check status
systemctl status imgserv
curl http://localhost:8080/status | jq

# Update camera server
cd /opt/imgserv
git pull origin main
sudo bash deploy/update-camera.sh

# Update VPS (from camera server)
sudo bash /opt/imgserv/deploy/update-vps-remote.sh

# Test endpoints
curl http://localhost:8080/health
curl http://localhost:8080/analytics | jq

# Check version
cat VERSION
curl http://localhost:8080/status | jq '.version'
```

---

## 📝 Update History

- **2025-10-24**: Created v2.0.0 with professional overlay system
- **2025-10-24**: Added comprehensive costing documentation
- **2025-10-24**: Implemented continuous black bar design
- **2025-10-24**: Added horizontal layout with temperature positioning
- **2025-10-24**: Enhanced readability with uniform 36px fonts
- **2025-10-24**: Added raw image processing for maximum accuracy
- **2025-10-24**: Consolidated documentation to 6 core files
- **2025-10-24**: Added municipal budget justification and ROI analysis

---

## 🎯 Development Guidelines

### When Making Changes:

1. **Test Both Servers**: Changes may affect camera server, VPS, or both
2. **Respect Architecture**: Camera server = processing, VPS = serving
3. **Maintain Security**: Never expose camera credentials publicly
4. **Update Documentation**: Keep all 6 docs in sync with code
5. **Version Control**: Update VERSION and CHANGELOG.md
6. **Test Configuration**: Ensure changes apply without restart
7. **Monitor Costs**: Track bandwidth and resource usage
8. **Preserve Quality**: Maintain professional appearance standards

### Common Mistakes to Avoid:

- ❌ DON'T process analytics on VPS (security risk)
- ❌ DON'T store configuration on VPS (keep on camera server)
- ❌ DON'T expose camera credentials in logs or configs
- ❌ DON'T break RSYNC connectivity (critical for operation)
- ❌ DON'T create new documentation files (use existing 6)
- ❌ DON'T ignore error handling in async operations
- ❌ DON'T hardcode values that should be configurable
- ❌ DON'T forget to test both servers after changes

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

**Remember**: Quality over quantity. Update existing docs, don't create new ones!

**End of Context Document**

*This document should be updated whenever significant architectural changes are made.*