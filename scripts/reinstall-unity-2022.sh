#!/bin/bash
set -e

echo "🎮 Reinstalling Unity 2022.3.45f1"
echo "================================="

UNITY_VERSION="2022.3.45f1"
CHANGESET="87c2c5a7cd20"

# Create directories
echo "📁 Creating directories..."
sudo mkdir -p /opt/unity/editors/${UNITY_VERSION}
sudo mkdir -p /tmp/unity-download
cd /tmp/unity-download

# Download Unity Editor
echo "⬇️  Downloading Unity Editor ${UNITY_VERSION}..."
UNITY_URL="https://download.unity3d.com/download_unity/${CHANGESET}/LinuxEditorInstaller/Unity.tar.xz"

wget -O Unity.tar.xz "$UNITY_URL" || {
    echo "❌ Download failed"
    exit 1
}

# Extract
echo "📦 Extracting Unity..."
sudo tar -xf Unity.tar.xz -C /opt/unity/editors/${UNITY_VERSION}

# Set permissions
echo "🔐 Setting permissions..."
sudo chown -R unity:unity /opt/unity

# Create symlinks
echo "🔗 Creating symlinks..."
sudo ln -sf /opt/unity/editors/${UNITY_VERSION}/Editor/Unity /opt/unity/Unity
sudo ln -sf /opt/unity/editors/${UNITY_VERSION}/Editor/Unity /usr/local/bin/unity

# Verify
echo "✅ Verifying installation..."
if [ -f "/opt/unity/editors/${UNITY_VERSION}/Editor/Unity" ]; then
    ls -lh /opt/unity/editors/${UNITY_VERSION}/Editor/Unity
    file /opt/unity/editors/${UNITY_VERSION}/Editor/Unity
    echo "✅ Unity installed successfully!"
else
    echo "❌ Installation failed"
    exit 1
fi

# Cleanup
rm -rf /tmp/unity-download

echo "🎉 Done! Restart unity-mcp service with: sudo systemctl restart unity-mcp"
