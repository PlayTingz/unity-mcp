#!/bin/bash
# Unity MCP Production Service - Manual Deployment Commands
# Copy and paste these commands in your VPS terminal (web console, etc.)

echo "🎮 Unity MCP Production Deployment Starting..."

# Stop current service
systemctl stop unity-mcp

# Backup current service (optional)
cp /opt/unity-mcp/server/unity_production_service.py /opt/unity-mcp/server/unity_production_service.py.backup 2>/dev/null || true

# Create the new production service
cat > /opt/unity-mcp/server/unity_production_service.py << 'UNITY_SERVICE_EOF'