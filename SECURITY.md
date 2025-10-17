# Security Architecture - Configuration System

## 🏗️ **System Architecture Overview**

The Image Sequence Server uses a **two-server security model** with clear separation of concerns:

### **🔒 Camera Server (Internal/Secure)**
- **Location**: Behind firewall, NAT, internal network
- **Purpose**: Camera capture, analytics processing, configuration management
- **Access**: Internal network only (192.168.x.x, 10.x.x.x, etc.)
- **Port**: 8080 (internal only)

### **🌐 VPS Server (Public/Facing)**
- **Location**: Public internet, DMZ
- **Purpose**: Content serving only (static GIFs)
- **Access**: Public internet
- **Port**: 80/443 (public)

---

## ⚙️ **Configuration System Security**

### **Configuration Location**: ✅ **Camera Server Only**

**Configuration Endpoints** (Camera Server - Internal Only):
- `http://camera-server:8080/config` - Configuration web page
- `http://camera-server:8080/config/analytics` - Configuration API
- `http://camera-server:8080/config/analytics/reset` - Reset to defaults

**Configuration Storage**:
- File: `/etc/imgserv/analytics_config.json`
- Location: Camera server filesystem
- Permissions: `imgserv` user only
- Backup: Included in system backups

### **Security Features**:

1. **Network Isolation**: Configuration only accessible from internal network
2. **Access Logging**: All configuration access logged with client IP
3. **Rate Limiting**: API endpoints protected against abuse
4. **Input Validation**: All configuration updates validated
5. **File Permissions**: Configuration files protected by filesystem permissions

---

## 🚫 **What VPS Does NOT Have**

The VPS server is **configuration-free** and **analytics-free**:

- ❌ No configuration interface
- ❌ No analytics processing
- ❌ No camera access
- ❌ No sensitive data storage
- ❌ No administrative functions

**VPS Only Serves**:
- ✅ Static GIF files (pre-generated)
- ✅ Basic HTML pages
- ✅ Public monitoring interface

---

## 🔐 **Security Benefits**

### **Attack Surface Reduction**:
- Configuration system isolated from public internet
- VPS cannot be compromised to access camera server
- No sensitive data exposed on public server

### **Network Security**:
- Camera server behind NAT/firewall
- No inbound connections from internet
- Configuration only accessible from trusted internal network

### **Data Protection**:
- Analytics data processed on secure server
- Configuration stored on protected filesystem
- No credentials or sensitive data on VPS

---

## 📋 **Access Control**

### **Configuration Access**:
- **Internal Network Only**: Must be on same network as camera server
- **No External Access**: Cannot access from internet
- **VPN Required**: External access requires VPN to internal network

### **VPS Access**:
- **Public Internet**: Anyone can view monitoring page
- **Read-Only**: No configuration or administrative access
- **Static Content**: Only serves pre-generated GIFs

---

## 🛡️ **Security Monitoring**

### **Configuration Access Logging**:
```json
{
  "event": "Configuration page accessed",
  "client_ip": "192.168.1.100",
  "timestamp": "2025-01-17T10:30:00Z"
}
```

### **Configuration Update Logging**:
```json
{
  "event": "Configuration updated successfully",
  "client_ip": "192.168.1.100",
  "changes": ["weather_latitude", "analytics_enabled"],
  "timestamp": "2025-01-17T10:35:00Z"
}
```

---

## 🔧 **Configuration Management**

### **File Locations** (Camera Server):
- **Main Config**: `/etc/imgserv/.env`
- **Analytics Config**: `/etc/imgserv/analytics_config.json`
- **Service Config**: `/etc/systemd/system/imgserv.service`

### **Permissions**:
```bash
# Configuration files
chmod 600 /etc/imgserv/.env
chmod 600 /etc/imgserv/analytics_config.json
chown imgserv:imgserv /etc/imgserv/analytics_config.json

# Service files
chmod 644 /etc/systemd/system/imgserv.service
```

---

## 🚨 **Security Best Practices**

### **For Administrators**:
1. **VPN Access**: Use VPN to access camera server configuration
2. **Internal Network**: Configure from trusted internal network only
3. **Monitor Logs**: Check configuration access logs regularly
4. **Backup Configs**: Include configuration files in backups
5. **Update Regularly**: Keep camera server software updated

### **For Network Security**:
1. **Firewall Rules**: Block inbound connections to camera server
2. **NAT Configuration**: Ensure camera server not directly accessible
3. **VLAN Isolation**: Separate camera server on isolated VLAN
4. **Access Control**: Limit who can access internal network

---

## 📊 **Architecture Diagram**

```
Internet
    │
    ▼
┌─────────────┐
│   VPS       │ ◄── Public Access (80/443)
│ (Public)    │     - Serves GIFs only
│             │     - No configuration
└─────────────┘
    │
    │ RSYNC (SSH)
    ▼
┌─────────────┐
│Camera Server│ ◄── Internal Network Only (8080)
│ (Internal)  │     - Configuration interface
│             │     - Analytics processing
│             │     - Camera capture
└─────────────┘
    │
    ▼
┌─────────────┐
│   Camera    │ ◄── RTSP Stream
│ (192.168.x) │     - Internal network
└─────────────┘
```

This architecture ensures that **configuration remains secure** on the camera server while the VPS serves only public content.
