#!/bin/bash

set -e

INSTANCE_NAME="unity-mcp-server"
ZONE="us-central1-a"

echo "🎨 Deploying Theme Integration to Production"
echo "=============================================="
echo ""

# Upload updated modules
echo "📤 Uploading updated Unity modules..."
gcloud compute scp /home/jpb/dev/tingz/unity-mcp/src/unity_project_generator.py "$INSTANCE_NAME:/tmp/" --zone="$ZONE"
gcloud compute scp /home/jpb/dev/tingz/unity-mcp/src/unity_build_service.py "$INSTANCE_NAME:/tmp/" --zone="$ZONE"
gcloud compute scp /home/jpb/dev/tingz/unity-mcp/unity_production_service_updated.py "$INSTANCE_NAME:/tmp/" --zone="$ZONE"

# Install on server
echo "💾 Installing updated modules..."
gcloud compute ssh "$INSTANCE_NAME" --zone="$ZONE" << 'ENDSSH'
sudo cp /tmp/unity_project_generator.py /opt/unity-mcp/server/lib/
sudo cp /tmp/unity_build_service.py /opt/unity-mcp/server/lib/
sudo cp /tmp/unity_production_service_updated.py /opt/unity-mcp/server/

sudo chmod 644 /opt/unity-mcp/server/lib/*.py
sudo chmod +x /opt/unity-mcp/server/unity_production_service_updated.py

echo "✅ Modules updated"
ENDSSH

# Restart service
echo "🔄 Restarting Unity MCP service..."
gcloud compute ssh "$INSTANCE_NAME" --zone="$ZONE" --command="
sudo systemctl restart unity-mcp
sleep 5
sudo systemctl status unity-mcp --no-pager | head -15
"

echo ""
echo "=============================================="
echo "✅ Theme Integration Deployed!"
echo "=============================================="
echo ""
echo "New features:"
echo "  ✓ Theme parameter in build requests"
echo "  ✓ ThemeManager auto-added to scenes"
echo "  ✓ ThemeApplier script for auto-theme application"
echo "  ✓ /themes endpoint for listing themes"
echo ""
echo "Test with:"
echo '  curl http://35.226.93.88:8080/themes'
echo ""
