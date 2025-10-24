#!/bin/bash
#
# Fix .env file syntax
# Adds quotes around VPS_RSYNC_OPTIONS to prevent parsing errors
#

echo "Fixing /etc/imgserv/.env syntax..."

# Backup original
cp /etc/imgserv/.env /etc/imgserv/.env.backup

# Fix VPS_RSYNC_OPTIONS line
sed -i 's/^VPS_RSYNC_OPTIONS=-avz --delete/VPS_RSYNC_OPTIONS="-avz --delete"/' /etc/imgserv/.env

echo "Fixed! Backup saved to /etc/imgserv/.env.backup"
echo ""
echo "Verifying..."
grep VPS_RSYNC_OPTIONS /etc/imgserv/.env

