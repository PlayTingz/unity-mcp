#!/bin/bash

set -e

INSTANCE_NAME="unity-mcp-server"
ZONE="us-central1-a"

echo "🚀 Deploying Updated Production Service with Package Support"
echo "=============================================================="
echo ""

# Step 1: Upload new service file
echo "📤 Step 1: Uploading updated production service..."
gcloud compute scp /home/jpb/dev/tingz/unity-mcp/unity_production_service_updated.py \
  "$INSTANCE_NAME:/tmp/" --zone="$ZONE"
echo "✅ Service file uploaded"
echo ""

# Step 2: Backup current service and install new one
echo "💾 Step 2: Installing updated service..."
gcloud compute ssh "$INSTANCE_NAME" --zone="$ZONE" << 'ENDSSH'
set -e

# Backup current service
BACKUP_DIR="/opt/unity-mcp/backups/$(date +%Y%m%d-%H%M%S)"
sudo mkdir -p "$BACKUP_DIR"
sudo cp /opt/unity-mcp/server/unity_production_service.py "$BACKUP_DIR/" 2>/dev/null || true

# Install new service
sudo cp /tmp/unity_production_service_updated.py /opt/unity-mcp/server/
sudo chmod +x /opt/unity-mcp/server/unity_production_service_updated.py
sudo chown root:root /opt/unity-mcp/server/unity_production_service_updated.py

echo "✅ New service installed"

# Update systemd service to use new file
echo "Updating systemd service configuration..."
sudo tee /etc/systemd/system/unity-mcp.service > /dev/null << 'SYSTEMD_EOF'
[Unit]
Description=Unity MCP Production Build Service with Package Support
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/unity-mcp/server
Environment=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/opt/unity
Environment=DISPLAY=:99
Environment=PYTHONPATH=/opt/unity-mcp/server/lib
ExecStart=/usr/bin/python3 unity_production_service_updated.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=unity-mcp
KillMode=mixed
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
SYSTEMD_EOF

echo "✅ Systemd service updated"
ENDSSH

echo ""

# Step 3: Reload systemd and restart service
echo "🔄 Step 3: Restarting service..."
gcloud compute ssh "$INSTANCE_NAME" --zone="$ZONE" --command="
sudo systemctl daemon-reload
sudo systemctl restart unity-mcp
sleep 3
sudo systemctl status unity-mcp --no-pager -l
"

echo ""
echo "=============================================================="
echo "✅ Deployment Complete!"
echo "=============================================================="
echo ""
echo "Updated production service features:"
echo "  ✓ Uses modular Unity components from /opt/unity-mcp/server/lib/"
echo "  ✓ Automatic CityThemePackage import during builds"
echo "  ✓ com.unity.cloud.gltfast v6.8.0 support"
echo "  ✓ Enhanced logging and monitoring"
echo ""
echo "Service version: 3.1.0"
echo ""
echo "Test the service:"
echo "  curl http://35.226.93.88:8080/health"
echo ""
echo "View logs:"
echo "  sudo journalctl -u unity-mcp -f"
echo ""
