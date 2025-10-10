#!/bin/bash
# Deploy asset manager to production server

set -e

echo "Deploying Asset Manager to unity-mcp-server..."

# Upload asset_manager.py
echo "1. Uploading asset_manager.py..."
gcloud compute scp src/asset_manager.py unity-mcp-server:/tmp/asset_manager.py --zone=us-central1-a

# Upload updated unity_build_service.py
echo "2. Uploading updated unity_build_service.py..."
gcloud compute scp src/unity_build_service.py unity-mcp-server:/tmp/unity_build_service.py --zone=us-central1-a

# Install files and restart service
echo "3. Installing files and restarting service..."
gcloud compute ssh unity-mcp-server --zone=us-central1-a << 'EOF'
  sudo cp /tmp/asset_manager.py /opt/unity-mcp/src/
  sudo cp /tmp/unity_build_service.py /opt/unity-mcp/src/
  sudo chown root:root /opt/unity-mcp/src/asset_manager.py
  sudo chown root:root /opt/unity-mcp/src/unity_build_service.py
  sudo chmod 644 /opt/unity-mcp/src/asset_manager.py
  sudo chmod 644 /opt/unity-mcp/src/unity_build_service.py
  
  echo "Restarting unity-mcp service..."
  sudo systemctl restart unity-mcp
  sleep 3
  sudo systemctl status unity-mcp --no-pager
EOF

echo "✅ Deployment complete!"
echo ""
echo "Test with:"
echo 'curl -X POST http://35.226.93.88/build \'
echo '  -H "Authorization: Bearer 013e283d7f3a2d45dcdbe7a2b4676a61ff58e7a576930ac3ea66c85d3882f197" \'
echo '  -H "Content-Type: application/json" \'
echo '  -d @tests/test_payload_with_assets.json'
