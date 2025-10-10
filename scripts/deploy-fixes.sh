#!/bin/bash
# Deploy all fixes to production server at 35.226.93.88

set -e

SERVER="root@35.226.93.88"
REMOTE_DIR="/opt/unity-mcp/server"

echo "🚀 Deploying Unity MCP Fixes to Production"
echo "=============================================="
echo ""

# Step 1: Upload updated files
echo "📤 Step 1: Uploading updated Python files..."
scp src/unity_project_generator.py "$SERVER:$REMOTE_DIR/unity_project_generator.py"
scp src/unity_build_service.py "$SERVER:$REMOTE_DIR/unity_build_service.py"
scp src/asset_manager.py "$SERVER:$REMOTE_DIR/asset_manager.py"
scp src/production_unity_service.py "$SERVER:$REMOTE_DIR/unity_production_service.py"
echo "  ✓ Python files uploaded"
echo ""

# Step 2: Upload and run shared project setup script
echo "🏗️  Step 2: Setting up shared Unity project..."
scp scripts/setup-shared-project.py "$SERVER:/tmp/setup-shared-project.py"
ssh "$SERVER" "python3 /tmp/setup-shared-project.py"
echo "  ✓ Shared project created"
echo ""

# Step 3: Import CityThemePackage if it exists
echo "📦 Step 3: Checking for CityThemePackage..."
ssh "$SERVER" << 'EOF'
if [ -f "/opt/unity-mcp/CityThemePackage.unitypackage" ]; then
    echo "  Found CityThemePackage, importing..."
    /opt/unity/Unity \
        -batchmode \
        -quit \
        -projectPath /opt/unity-mcp/shared-project \
        -importPackage /opt/unity-mcp/CityThemePackage.unitypackage \
        -logFile /tmp/import_package.log 2>&1
    echo "  ✓ CityThemePackage imported"
else
    echo "  ⚠ CityThemePackage not found, skipping import"
fi
EOF
echo ""

# Step 4: Set permissions
echo "🔐 Step 4: Setting permissions..."
ssh "$SERVER" << 'EOF'
chmod -R 755 /opt/unity-mcp/shared-project
chmod 644 /opt/unity-mcp/server/*.py
echo "  ✓ Permissions set"
EOF
echo ""

# Step 5: Restart service
echo "🔄 Step 5: Restarting Unity MCP service..."
ssh "$SERVER" << 'EOF'
systemctl restart unity-mcp
sleep 5
systemctl status unity-mcp --no-pager
EOF
echo "  ✓ Service restarted"
echo ""

# Step 6: Health check
echo "🏥 Step 6: Checking service health..."
sleep 3
HEALTH=$(curl -s http://35.226.93.88/health | jq -r '.status' 2>/dev/null || echo "error")
if [ "$HEALTH" = "healthy" ]; then
    echo "  ✅ Service is healthy!"
else
    echo "  ❌ Service health check failed!"
    exit 1
fi
echo ""

echo "=============================================="
echo "✅ Deployment Complete!"
echo ""
echo "Summary of fixes deployed:"
echo "  1. BuildScript.cs now reads from EditorBuildSettings"
echo "  2. SimpleGameManager.cs created with correct GUID"
echo "  3. Shared project structure created at /opt/unity-mcp/shared-project"
echo "  4. Scene name tracking added to build pipeline"
echo "  5. Project generator returns (path, scene_name) tuple"
echo ""
echo "Next: Test a build with:"
echo "  curl -X POST http://35.226.93.88/build \\"
echo "    -H 'Authorization: Bearer 013e283d7f3a2d45dcdbe7a2b4676a61ff58e7a576930ac3ea66c85d3882f197' \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"user_id\":\"test\",\"game_id\":\"test123\",\"game_name\":\"TestGame\",\"game_type\":\"platformer\"}'"
echo ""
