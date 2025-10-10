#!/bin/bash
set -e

echo "=========================================="
echo "Unity → Godot Conversion Deployment"
echo "=========================================="

SERVER_USER="root"
SERVER_IP="35.226.93.88"
SERVER_DIR="/opt/unity-mcp/server"

echo "📦 Step 1: Uploading new Godot service files..."
scp src/godot_project_generator.py ${SERVER_USER}@${SERVER_IP}:${SERVER_DIR}/
scp src/godot_build_service.py ${SERVER_USER}@${SERVER_IP}:${SERVER_DIR}/
scp src/production_godot_service.py ${SERVER_USER}@${SERVER_IP}:${SERVER_DIR}/

echo ""
echo "🛑 Step 2: Stopping Unity MCP service..."
ssh ${SERVER_USER}@${SERVER_IP} "systemctl stop unity-mcp || true"

echo ""
echo "📝 Step 3: Installing new systemd service file..."
scp godot-mcp.service ${SERVER_USER}@${SERVER_IP}:/etc/systemd/system/
ssh ${SERVER_USER}@${SERVER_IP} "systemctl daemon-reload"

echo ""
echo "🔧 Step 4: Verifying Godot installation..."
ssh ${SERVER_USER}@${SERVER_IP} "which godot && godot --version || echo 'WARNING: Godot not found!'"

echo ""
echo "🚀 Step 5: Starting Godot MCP service..."
ssh ${SERVER_USER}@${SERVER_IP} "systemctl enable godot-mcp"
ssh ${SERVER_USER}@${SERVER_IP} "systemctl start godot-mcp"

echo ""
echo "⏳ Step 6: Waiting for service to initialize..."
sleep 5

echo ""
echo "✅ Step 7: Checking service status..."
ssh ${SERVER_USER}@${SERVER_IP} "systemctl status godot-mcp --no-pager" || true

echo ""
echo "🔍 Step 8: Testing health endpoint..."
ssh ${SERVER_USER}@${SERVER_IP} "curl -s http://localhost:8080/health | python3 -m json.tool" || echo "Health check failed"

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Service URL: http://35.226.93.88:8080"
echo "Health Check: curl http://35.226.93.88:8080/health"
echo "Service Logs: ssh root@35.226.93.88 'journalctl -u godot-mcp -f'"
echo ""
echo "To test a build:"
echo "curl -X POST http://35.226.93.88:8080/build \\"
echo "  -H 'Authorization: Bearer 013e283d7f3a2d45dcdbe7a2b4676a61ff58e7a576930ac3ea66c85d3882f197' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"user_id\":\"test\",\"game_id\":\"test1\",\"game_name\":\"Test Game\",\"game_type\":\"platformer\"}'"
