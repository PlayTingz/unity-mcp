#!/bin/bash
set -e

echo "🚀 Deploying Production Unity MCP Service to VPS"
echo "================================================"

# Configuration
VPS_HOST="35.226.93.88"
VPS_USER="root"
REMOTE_DIR="/opt/unity-mcp/server"
SERVICE_NAME="unity-mcp"

echo "📦 Preparing deployment package..."

# Create temporary deployment directory
DEPLOY_DIR=$(mktemp -d)
echo "   Deployment directory: $DEPLOY_DIR"

# Copy source files (single complete file)
cp unity_production_service_complete.py "$DEPLOY_DIR/unity_production_service.py"

# Create requirements.txt
cat > "$DEPLOY_DIR/requirements.txt" << 'EOF'
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
psutil>=5.9.0
python-multipart>=0.0.6
httpx>=0.25.2
EOF

# Create systemd service file
cat > "$DEPLOY_DIR/unity-mcp-production.service" << 'EOF'
[Unit]
Description=Unity MCP Production Build Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/unity-mcp/server
Environment=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/opt/unity
Environment=DISPLAY=:99
ExecStart=/usr/bin/python3 unity_production_service.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=unity-mcp
KillMode=mixed
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOF

# Create deployment script for the VPS
cat > "$DEPLOY_DIR/deploy_on_vps.sh" << 'EOF'
#!/bin/bash
set -e

echo "🎮 Setting up Unity MCP Production Service on VPS"
echo "================================================"

# Stop existing service if running
systemctl stop unity-mcp || true
systemctl disable unity-mcp || true

# Create directories
mkdir -p /opt/unity-mcp/server
mkdir -p /opt/unity-mcp/builds
mkdir -p /var/www/html/games

# Set permissions
chmod 755 /opt/unity-mcp
chmod 755 /opt/unity-mcp/server
chmod 755 /opt/unity-mcp/builds
chmod 755 /var/www/html/games
chmod 755 /var/www/html

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Install systemd service
cp unity-mcp-production.service /etc/systemd/system/unity-mcp.service
systemctl daemon-reload

# Verify Unity installation
if [ ! -f "/opt/unity/Unity" ]; then
    echo "❌ Unity not found at /opt/unity/Unity"
    echo "Please ensure Unity Pro 2022.3.45f1 is installed and licensed"
    exit 1
fi

# Test Unity license
echo "🔍 Checking Unity license..."
/opt/unity/Unity -batchmode -quit -logFile /tmp/unity_license_check.log || true

if grep -q "License checkout failed" /tmp/unity_license_check.log; then
    echo "❌ Unity license check failed"
    echo "License log:"
    cat /tmp/unity_license_check.log
    exit 1
else
    echo "✅ Unity Pro license verified"
fi

# Start service
echo "🚀 Starting Unity MCP service..."
systemctl enable unity-mcp
systemctl start unity-mcp

# Wait for service to start
sleep 5

# Check service status
if systemctl is-active --quiet unity-mcp; then
    echo "✅ Unity MCP service started successfully"
    systemctl status unity-mcp --no-pager -l
    echo ""
    echo "📊 Service endpoints:"
    echo "   Health: http://35.226.93.88/health"
    echo "   API Docs: http://35.226.93.88/docs"
    echo "   Service Status: http://35.226.93.88/status"
    echo ""
    echo "🔑 API Key: 013e283d7f3a2d45dcdbe7a2b4676a61ff58e7a576930ac3ea66c85d3882f197"
    echo ""
    echo "✅ Deployment completed successfully!"
else
    echo "❌ Service failed to start"
    journalctl -u unity-mcp --no-pager -l
    exit 1
fi
EOF

chmod +x "$DEPLOY_DIR/deploy_on_vps.sh"

echo "📤 Uploading files to VPS..."

# Upload files to VPS
scp -o StrictHostKeyChecking=no -r "$DEPLOY_DIR"/* "$VPS_USER@$VPS_HOST:$REMOTE_DIR/"

echo "🎯 Executing deployment on VPS..."

# Run deployment on VPS
ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_HOST" "cd $REMOTE_DIR && ./deploy_on_vps.sh"

echo ""
echo "🎉 Production Unity MCP Service Deployment Complete!"
echo "================================================"
echo ""
echo "🔗 Service URLs:"
echo "   Health Check: http://$VPS_HOST/health"
echo "   API Documentation: http://$VPS_HOST/docs"
echo "   Service Status: http://$VPS_HOST/status"
echo ""
echo "🔑 API Authentication:"
echo "   Bearer Token: 013e283d7f3a2d45dcdbe7a2b4676a61ff58e7a576930ac3ea66c85d3882f197"
echo ""
echo "🎮 Build Endpoint:"
echo "   POST http://$VPS_HOST/build"
echo "   Authorization: Bearer <token>"
echo ""
echo "✅ Service is now running with real Unity Pro integration!"

# Clean up
rm -rf "$DEPLOY_DIR"
echo "🧹 Cleaned up temporary files"