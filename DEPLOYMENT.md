# Production Deployment Guide

## Overview

This guide covers deploying the Image Sequence Server in a production environment, specifically optimized for Proxmox LXC containers.

## Prerequisites

- Proxmox VE 7.0+ or similar virtualization platform
- Ubuntu 22.04 LTS LXC container template
- Minimum resources: 1GB RAM, 2GB storage, 1 CPU core
- Network access to IP camera
- Root access to the container

## Step 1: Create LXC Container

### Using Proxmox Web Interface

1. **Create Container**:
   - Template: `ubuntu-22.04-standard_22.04-1_amd64.tar.zst`
   - Memory: 1024 MB
   - Storage: 2 GB
   - CPU: 1 core

2. **Network Configuration**:
   - Bridge: `vmbr0` (or your preferred bridge)
   - IP: Static IP in your network range
   - Gateway: Your network gateway

3. **Start Container**:
   ```bash
   # From Proxmox host
   pct start <container-id>
   ```

### Using Command Line

```bash
# Create container
pct create 100 local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
  --memory 1024 \
  --cores 1 \
  --rootfs local-lvm:2 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.1.100/24,gw=192.168.1.1

# Start container
pct start 100
```

## Step 2: Container Setup

### Access Container

```bash
# From Proxmox host
pct enter 100

# Or SSH if configured
ssh root@192.168.1.100
```

### Update System

```bash
apt update && apt upgrade -y
apt install -y git curl wget
```

## Step 3: Deploy Application

### Clone Repository

```bash
cd /opt
git clone https://github.com/yourusername/image-sequence-server.git
cd image-sequence-server
```

### Run Installer

```bash
# Production installation with custom settings
sudo ./deploy/install.sh --production \
  --camera-ip 192.168.1.110 \
  --camera-user admin \
  --camera-pass your-secure-password
```

### Verify Installation

```bash
# Check service status
systemctl status imgserv

# Check logs
journalctl -u imgserv -f

# Test web interface
curl -k https://localhost/health
```

## Step 4: SSL Certificate Setup

### Option A: Let's Encrypt (Recommended)

```bash
# Install certbot
apt install -y certbot python3-certbot-nginx

# Get certificate
certbot --nginx -d your-domain.com

# Auto-renewal
crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Option B: Self-Signed (Development)

The installer creates self-signed certificates by default. For production, replace them:

```bash
# Generate new certificate
openssl req -x509 -newkey rsa:4096 -keyout /etc/ssl/private/imgserv.key \
  -out /etc/ssl/certs/imgserv.crt -days 365 -nodes \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=your-domain.com"

# Restart nginx
systemctl restart nginx
```

## Step 5: Security Hardening

### Firewall Configuration

```bash
# Review firewall rules
ufw status

# Add specific rules if needed
ufw allow from 192.168.1.0/24 to any port 443
ufw deny 80  # Block HTTP if using HTTPS only
```

### User Security

```bash
# Verify service runs as non-root user
ps aux | grep imgserv

# Check file permissions
ls -la /opt/imgserv/
ls -la /var/lib/imgserv/
```

### Network Security

```bash
# Test camera connectivity
curl -u admin:password http://192.168.1.110/snapshot.cgi

# Verify HTTPS only
curl -I http://your-domain.com  # Should redirect to HTTPS
```

## Step 6: Monitoring Setup

### Log Monitoring

```bash
# Setup log rotation
cat > /etc/logrotate.d/imgserv << EOF
/var/log/imgserv/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 imgserv imgserv
}
EOF
```

### System Monitoring

```bash
# Install monitoring tools
apt install -y htop iotop nethogs

# Monitor resource usage
htop
iotop
```

### Application Monitoring

```bash
# Check service status
curl https://your-domain.com/status

# Monitor storage usage
df -h /var/lib/imgserv
du -sh /var/lib/imgserv/*
```

## Step 7: Backup Strategy

### Data Backup

```bash
# Create backup script
cat > /opt/backup_imgserv.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup configuration
tar -czf $BACKUP_DIR/imgserv_config_$DATE.tar.gz /etc/imgserv/

# Backup data (optional - images are temporary)
tar -czf $BACKUP_DIR/imgserv_data_$DATE.tar.gz /var/lib/imgserv/

# Cleanup old backups (keep 7 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /opt/backup_imgserv.sh

# Schedule daily backups
crontab -e
# Add: 0 2 * * * /opt/backup_imgserv.sh
```

## Step 8: Performance Tuning

### Resource Optimization

Edit `/etc/imgserv/.env`:

```bash
# Reduce image quality for lower bandwidth
IMAGE_QUALITY=70

# Reduce sequence duration
SEQUENCE_DURATION_MINUTES=3

# Reduce capture frequency (edit source)
# In src/services/sequence_service.py line 95:
# await asyncio.sleep(60)  # Change from 30 to 60 seconds
```

### System Optimization

```bash
# Optimize for containers
echo 'vm.swappiness=10' >> /etc/sysctl.conf
echo 'vm.dirty_ratio=15' >> /etc/sysctl.conf
sysctl -p
```

## Troubleshooting

### Common Issues

1. **Service Won't Start**:
   ```bash
   journalctl -u imgserv -n 50
   sudo -u imgserv python /opt/imgserv/main.py
   ```

2. **Camera Connection Failed**:
   ```bash
   # Test camera directly
   curl -u admin:password http://192.168.1.110/snapshot.cgi
   
   # Check network connectivity
   ping 192.168.1.110
   ```

3. **High Memory Usage**:
   ```bash
   # Check memory usage
   free -h
   ps aux --sort=-%mem | head
   
   # Reduce image quality
   IMAGE_QUALITY=60
   ```

4. **Storage Full**:
   ```bash
   # Check storage
   df -h
   du -sh /var/lib/imgserv/*
   
   # Manual cleanup
   find /var/lib/imgserv -name "*.jpg" -mtime +1 -delete
   ```

### Log Analysis

```bash
# Application logs
tail -f /var/log/imgserv/app.log

# System logs
journalctl -u imgserv -f

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

## Security Checklist

- [ ] Service runs as non-root user (`imgserv`)
- [ ] HTTPS enabled with valid certificates
- [ ] Firewall configured and enabled
- [ ] Default passwords changed
- [ ] Log monitoring enabled
- [ ] Backup strategy implemented
- [ ] Resource limits configured
- [ ] Security headers enabled
- [ ] Rate limiting active
- [ ] Input validation working

## Maintenance

### Regular Tasks

1. **Weekly**:
   - Check service status
   - Review logs for errors
   - Monitor resource usage
   - Test camera connectivity

2. **Monthly**:
   - Update system packages
   - Review security logs
   - Test backup restoration
   - Check SSL certificate expiry

3. **Quarterly**:
   - Security audit
   - Performance review
   - Update application dependencies
   - Review and update documentation

### Updates

```bash
# Update application
cd /opt/image-sequence-server
git pull origin main
sudo ./deploy/install.sh --production

# Update system
apt update && apt upgrade -y
```

## Support

For issues and support:
- GitHub Issues: [Repository Issues](https://github.com/yourusername/image-sequence-server/issues)
- Documentation: [Wiki](https://github.com/yourusername/image-sequence-server/wiki)
- Security: Report privately to security@yourdomain.com
