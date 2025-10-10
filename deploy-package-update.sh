#!/bin/bash

set -e

INSTANCE_NAME="unity-mcp-server"
ZONE="us-central1-a"
PACKAGE_PATH="/home/jpb/dev/tingz/CityThemePackage.unitypackage"

echo "🚀 Deploying Unity Package and GLTFast Support"
echo "================================================"
echo ""

# Step 1: Upload the Unity package
echo "📦 Step 1: Uploading CityThemePackage.unitypackage..."
gcloud compute ssh "$INSTANCE_NAME" --zone="$ZONE" --command="sudo mkdir -p /opt/unity-mcp/packages && sudo chmod 755 /opt/unity-mcp/packages"
gcloud compute scp "$PACKAGE_PATH" "$INSTANCE_NAME:/tmp/CityThemePackage.unitypackage" --zone="$ZONE"
gcloud compute ssh "$INSTANCE_NAME" --zone="$ZONE" --command="sudo mv /tmp/CityThemePackage.unitypackage /opt/unity-mcp/packages/ && sudo chmod 644 /opt/unity-mcp/packages/CityThemePackage.unitypackage"
echo "✅ Package uploaded to /opt/unity-mcp/packages/CityThemePackage.unitypackage"
echo ""

# Step 2: Upload the local Unity project generator and build service to the server
echo "📤 Step 2: Uploading updated Unity modules..."
gcloud compute scp /home/jpb/dev/tingz/unity-mcp/src/unity_project_generator.py "$INSTANCE_NAME:/tmp/" --zone="$ZONE"
gcloud compute scp /home/jpb/dev/tingz/unity-mcp/src/unity_build_service.py "$INSTANCE_NAME:/tmp/" --zone="$ZONE"
echo "✅ Files uploaded to /tmp/"
echo ""

# Step 3: Create backup and install files on server
echo "💾 Step 3: Installing updated files..."
gcloud compute ssh "$INSTANCE_NAME" --zone="$ZONE" << 'ENDSSH'
set -e

# Create backup directory
sudo mkdir -p /opt/unity-mcp/backups/$(date +%Y%m%d-%H%M%S)

# Check if server directory has the files
if [ -f /opt/unity-mcp/server/build_service.py ]; then
    echo "Found existing build_service.py, creating backup..."
    sudo cp /opt/unity-mcp/server/build_service.py /opt/unity-mcp/backups/$(date +%Y%m%d-%H%M%S)/
fi

# Create server directory structure
sudo mkdir -p /opt/unity-mcp/server/lib

# Install the Python modules
echo "Installing unity_project_generator.py..."
sudo cp /tmp/unity_project_generator.py /opt/unity-mcp/server/lib/
sudo chmod 644 /opt/unity-mcp/server/lib/unity_project_generator.py

echo "Installing unity_build_service.py..."
sudo cp /tmp/unity_build_service.py /opt/unity-mcp/server/lib/
sudo chmod 644 /opt/unity-mcp/server/lib/unity_build_service.py

# Create __init__.py files
sudo touch /opt/unity-mcp/server/lib/__init__.py
sudo chmod 644 /opt/unity-mcp/server/lib/__init__.py

echo "✅ Modules installed successfully"

# Check Unity installation
if [ -f /opt/unity/editors/2022.3.45f1/Editor/Unity ]; then
    echo "✅ Unity 2022.3.45f1 found"
else
    echo "⚠️  Unity not found at expected location"
fi

ENDSSH

echo ""
echo "✅ Installation complete!"
echo ""

# Step 4: Verify installation
echo "🔍 Step 4: Verifying installation..."
gcloud compute ssh "$INSTANCE_NAME" --zone="$ZONE" --command="ls -lh /opt/unity-mcp/packages/CityThemePackage.unitypackage && ls -lh /opt/unity-mcp/server/lib/"

echo ""
echo "================================================"
echo "✅ Deployment Complete!"
echo "================================================"
echo ""
echo "Summary:"
echo "  ✓ CityThemePackage.unitypackage uploaded"
echo "  ✓ unity_project_generator.py installed"
echo "  ✓ unity_build_service.py installed"
echo ""
echo "The modules include:"
echo "  - import_unity_package() method"
echo "  - com.unity.cloud.gltfast package support"
echo "  - Automatic CityThemePackage import"
echo ""
echo "Next steps:"
echo "  1. Update your production service to use these modules"
echo "  2. Test with a new build request"
echo ""
