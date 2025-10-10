#!/bin/bash
set -e

echo "🐳 Deploying Unity MCP with Real Unity via Docker"
echo "=================================================="

UNITY_VERSION="2022.3.45f1"
VPS_HOST="35.226.93.88"
VPS_USER="root"

# Build Unity Docker image with real Unity using GameCI
echo "🔨 Building Unity Docker image with GameCI..."
docker build \
    -f docker/Dockerfile.unity-real \
    --build-arg UNITY_VERSION="${UNITY_VERSION}" \
    -t unity-mcp:real \
    .

# Save Docker image
echo "💾 Saving Docker image..."
docker save unity-mcp:real | gzip > /tmp/unity-mcp-real.tar.gz

# Upload to VPS
echo "📤 Uploading Docker image to VPS..."
gcloud compute scp --zone=us-central1-a /tmp/unity-mcp-real.tar.gz "${VPS_USER}@unity-mcp-server:/tmp/"

# Load and run on VPS
echo "🚀 Deploying on VPS..."
gcloud compute ssh unity-mcp-server --zone=us-central1-a --command="
set -e

echo '📦 Loading Docker image...'
docker load < /tmp/unity-mcp-real.tar.gz
rm /tmp/unity-mcp-real.tar.gz

echo '🛑 Stopping existing service...'
systemctl stop unity-mcp || true

echo '🗑️  Removing old containers...'
docker rm -f unity-mcp-container 2>/dev/null || true

echo '🚀 Starting Unity MCP container...'
docker run -d \
  --name unity-mcp-container \
  --restart unless-stopped \
  -p 8080:8080 \
  -p 6400:6400 \
  -v /opt/unity-mcp/builds:/app/builds \
  -v /opt/unity-mcp/packages:/app/packages \
  -v /var/www/html/games:/var/www/html/games \
  -e UNITY_VERSION='${UNITY_VERSION}' \
  -e LOG_LEVEL=INFO \
  unity-mcp:real

echo '⏳ Waiting for container to start...'
sleep 10

echo '✅ Checking container status...'
docker ps | grep unity-mcp-container

echo '🔍 Checking Unity installation...'
docker exec unity-mcp-container ls -lh /opt/unity/editors/${UNITY_VERSION}/Editor/Unity || echo 'Unity path check failed'

echo '✅ Deployment complete!'
echo 'Container logs: docker logs unity-mcp-container'
"

echo ""
echo "✅ Deployment Complete!"
echo "======================="
echo "   Container: unity-mcp-container"
echo "   Unity Version: ${UNITY_VERSION}"
echo "   API: http://${VPS_HOST}:8080"
echo ""
echo "Check logs: gcloud compute ssh unity-mcp-server --zone=us-central1-a --command='docker logs unity-mcp-container'"
