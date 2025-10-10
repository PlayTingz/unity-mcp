#!/bin/bash
set -e

echo "🎮 Installing Real Unity Editor via Unity Hub on VPS"
echo "===================================================="

UNITY_VERSION="2022.3.45f1"
UNITY_INSTALL_DIR="/opt/unity"
UNITY_HUB_URL="https://public-cdn.cloud.unity3d.com/hub/prod/UnityHubSetup.AppImage"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
   echo "❌ Please run as root or with sudo"
   exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
apt-get update
apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    wget \
    libfuse2 \
    libglu1-mesa \
    libasound2 \
    libgconf-2-4 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libsoup2.4-1 \
    libgbm1 \
    libxss1 \
    xvfb \
    xauth \
    fuse

# Create Unity directories
echo "📁 Creating Unity directories..."
mkdir -p "$UNITY_INSTALL_DIR/Hub"
mkdir -p "$UNITY_INSTALL_DIR/editors"

# Download Unity Hub
echo "⬇️  Downloading Unity Hub..."
cd "$UNITY_INSTALL_DIR/Hub"
if [ ! -f "UnityHub.AppImage" ]; then
    wget -O UnityHub.AppImage "$UNITY_HUB_URL"
    chmod +x UnityHub.AppImage
    echo "   ✅ Unity Hub downloaded"
else
    echo "   Unity Hub already exists"
fi

# Install Unity Editor using Unity Hub CLI
echo "⬇️  Installing Unity Editor $UNITY_VERSION..."
# Unity Hub needs to run in CLI mode
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 &
XVFB_PID=$!
sleep 2

# Install Unity version with WebGL support
"$UNITY_INSTALL_DIR/Hub/UnityHub.AppImage" --headless install \
    --version "$UNITY_VERSION" \
    --module webgl \
    --installPath "$UNITY_INSTALL_DIR/editors" || {
    echo "❌ Unity Hub installation failed"
    echo "Trying alternative method..."
    
    # Alternative: Use unity-editor installer
    CHANGESET=$(curl -s "https://unity3d.com/unity/whats-new/${UNITY_VERSION}" | grep -oP 'Changeset:\s*\K[a-f0-9]+' | head -1)
    if [ -z "$CHANGESET" ]; then
        echo "❌ Could not determine Unity changeset"
        kill $XVFB_PID 2>/dev/null || true
        exit 1
    fi
    
    echo "   Found changeset: $CHANGESET"
    
    # Download Unity using direct download
    UNITY_DL_BASE="https://download.unity3d.com/download_unity/$CHANGESET"
    
    # Download Unity Editor
    wget -O "/tmp/UnitySetup-${UNITY_VERSION}" "${UNITY_DL_BASE}/UnitySetup-${UNITY_VERSION}" || {
        echo "❌ Failed to download Unity Editor"
        kill $XVFB_PID 2>/dev/null || true
        exit 1
    }
    
    # Install Unity
    chmod +x "/tmp/UnitySetup-${UNITY_VERSION}"
    yes | "/tmp/UnitySetup-${UNITY_VERSION}" --unattended \
        --install-location="$UNITY_INSTALL_DIR/editors/$UNITY_VERSION" \
        --components=Unity,WebGL
    
    rm "/tmp/UnitySetup-${UNITY_VERSION}"
}

kill $XVFB_PID 2>/dev/null || true

# Create symlink for easier access
echo "🔗 Creating symlinks..."
UNITY_BIN=$(find "$UNITY_INSTALL_DIR/editors" -name "Unity" -type f | grep -E "Editor/Unity$" | head -1)

if [ -n "$UNITY_BIN" ]; then
    ln -sf "$UNITY_BIN" "$UNITY_INSTALL_DIR/Unity"
    echo "   Linked: $UNITY_BIN -> $UNITY_INSTALL_DIR/Unity"
else
    echo "   ⚠️  Could not find Unity binary"
fi

# Set permissions
echo "🔐 Setting permissions..."
chown -R unity:unity "$UNITY_INSTALL_DIR" 2>/dev/null || true
chmod +x "$UNITY_INSTALL_DIR/Unity" 2>/dev/null || true

# Verify installation
echo "✅ Verifying Unity installation..."
if [ -f "$UNITY_INSTALL_DIR/Unity" ]; then
    UNITY_PATH=$(readlink -f "$UNITY_INSTALL_DIR/Unity")
    
    # Check if it's a real binary
    FILE_TYPE=$(file "$UNITY_PATH")
    if [[ "$FILE_TYPE" == *"ELF"* ]] || [[ "$FILE_TYPE" == *"executable"* ]]; then
        echo "   ✅ Unity binary verified: $UNITY_PATH"
        
        # Test Unity version
        echo "🧪 Testing Unity..."
        "$UNITY_PATH" -version 2>/dev/null || echo "   Unity installed (version check requires license)"
    else
        echo "   ❌ Error: Unity binary is not a valid executable"
        echo "   File type: $FILE_TYPE"
        exit 1
    fi
else
    echo "   ❌ Unity binary not found at expected location"
    exit 1
fi

# Check for WebGL support
WEBGL_DIR=$(find "$UNITY_INSTALL_DIR/editors" -type d -name "WebGLSupport" | head -1)
if [ -n "$WEBGL_DIR" ]; then
    echo "   ✅ WebGL Build Support installed at: $WEBGL_DIR"
else
    echo "   ⚠️  Warning: WebGL Build Support not found"
fi

echo ""
echo "✅ Unity Installation Complete!"
echo "======================================"
echo "   Unity Path: $UNITY_PATH"
echo "   Unity Version: $UNITY_VERSION"
echo "   WebGL Support: $([ -n "$WEBGL_DIR" ] && echo "Installed" || echo "Not found")"
echo ""
echo "⚠️  Next Steps:"
echo "   1. Activate Unity license"
echo "   2. Update unity_build_service.py to use: $UNITY_PATH"
echo "   3. Restart unity-mcp service"
