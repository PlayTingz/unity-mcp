# Unity Installation for Production Server

## Current Status

❌ **Unity is NOT installed on the production server**

The unity-mcp service requires real Unity Editor 2022.3.45f1 with WebGL Build Support to function. Mock/fallback installations have been removed.

## What Was Done

### ✅ Cleaned Up Mock Installation
- Removed all mock Unity scripts from `/opt/unity/`
- Added binary validation to prevent mock installations
- Service now fails fast with clear error messages

### ✅ Theme Integration Code Ready
All theme integration code is complete and deployed:
- `src/unity_build_service.py` - Theme parameter in BuildRequest
- `src/unity_project_generator.py` - Theme system with ThemeManager/ThemeApplier
- `unity_production_service_updated.py` - `/themes` endpoint
- `CityThemePackage.unitypackage` - Uploaded to `/opt/unity-mcp/packages/`

**The theme system will work as soon as Unity is properly installed.**

## Installation Options

### Option 1: Docker with GameCI (Recommended)

Use the pre-built Dockerfile that includes real Unity:

```bash
# Build image locally
docker build \
  -f docker/Dockerfile.unity-real \
  --build-arg UNITY_VERSION=2022.3.45f1 \
  -t unity-mcp:real \
  .

# Save and upload to VPS
docker save unity-mcp:real | gzip > unity-mcp-real.tar.gz
gcloud compute scp --zone=us-central1-a unity-mcp-real.tar.gz unity-mcp-server:/tmp/

# On VPS: Load and run
docker load < /tmp/unity-mcp-real.tar.gz
docker run -d \
  --name unity-mcp \
  -p 8080:8080 \
  -v /opt/unity-mcp/builds:/app/builds \
  -v /opt/unity-mcp/packages:/app/packages \
  unity-mcp:real
```

**Pros:**
- GameCI provides pre-installed Unity
- Includes all dependencies
- Proven to work
- No manual Unity licensing

**Cons:**
- Requires Docker installation on VPS
- Larger disk footprint

### Option 2: Manual Unity Installation

Install Unity directly on the VPS:

#### Step 1: Install Unity Hub

```bash
# Download Unity Hub
wget https://public-cdn.cloud.unity3d.com/hub/prod/UnityHubSetup.AppImage
chmod +x UnityHubSetup.AppImage

# Install dependencies
apt-get install -y libfuse2 libglu1-mesa xvfb
```

#### Step 2: Install Unity Editor via Hub

```bash
# Start Xvfb for headless
Xvfb :99 -screen 0 1024x768x24 &
export DISPLAY=:99

# Install Unity 2022.3.45f1 with WebGL
./UnityHubSetup.AppImage --headless install \
  --version 2022.3.45f1 \
  --module webgl \
  --installPath /opt/unity/editors
```

#### Step 3: Activate License

You need a Unity Pro, Plus, or Personal license. Options:

**A. Unity Pro (Recommended for production)**
```bash
/opt/unity/editors/2022.3.45f1/Editor/Unity \
  -batchmode -quit \
  -username YOUR_EMAIL \
  -password YOUR_PASSWORD \
  -serial YOUR_SERIAL_KEY
```

**B. Manual Activation (Air-gapped)**
```bash
# 1. Create activation file
/opt/unity/editors/2022.3.45f1/Editor/Unity \
  -batchmode \
  -createManualActivationFile

# 2. Upload Unity_v2022.x.alf to https://license.unity3d.com/manual

# 3. Download .ulf file and place it
mkdir -p ~/.local/share/unity3d/Unity
cp Unity_v2022.x.ulf ~/.local/share/unity3d/Unity/
```

#### Step 4: Update Service Configuration

```bash
# Update unity_production_service_updated.py line with Unity path
UNITY_PATH="/opt/unity/editors/2022.3.45f1/Editor/Unity"

# Restart service
systemctl restart unity-mcp
```

**Pros:**
- Native installation
- Direct control
- Smaller footprint

**Cons:**
- Complex licensing
- Manual dependency management
- Requires valid Unity license

### Option 3: Use Cloud Build Service

Instead of local Unity, integrate with Unity Cloud Build:

**Pros:**
- No local Unity installation
- Unity manages infrastructure
- Always up-to-date

**Cons:**
- Requires Unity Cloud subscription
- External dependency
- API changes required

## Unity License Requirements

### Personal License (Free)
- Revenue < $100k/year
- Requires periodic reactivation
- May not be suitable for production

### Plus License (~$399/year)
- Revenue < $200k/year
- More stable activation
- Supports offline activation

### Pro License (~$2,040/year)
- No revenue limit
- Best for production
- Stable licensing
- Priority support

## Verification

After installation, verify Unity works:

```bash
# Check Unity binary
file /opt/unity/editors/2022.3.45f1/Editor/Unity
# Should output: ELF 64-bit LSB executable

# Test Unity
/opt/unity/editors/2022.3.45f1/Editor/Unity -version

# Check WebGL support
ls /opt/unity/editors/2022.3.45f1/Editor/Data/PlaybackEngines/WebGLSupport
```

## Current Service Configuration

The service expects Unity at:
```
/opt/unity/editors/2022.3.45f1/Editor/Unity
```

To change this path, update `unity_production_service_updated.py`:
```python
UNITY_PATH = "/your/custom/path/Unity"
```

## Next Steps

1. Choose an installation option above
2. Install and license Unity
3. Verify installation
4. Restart unity-mcp service: `systemctl restart unity-mcp`
5. Test theme generation via API

## Testing Theme System

Once Unity is installed, test the theme integration:

```bash
# Check available themes
curl http://35.226.93.88/themes

# Submit build with theme
curl -X POST http://35.226.93.88/build \
  -H "Authorization: Bearer 013e283d7f3a2d45dcdbe7a2b4676a61ff58e7a576930ac3ea66c85d3882f197" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test",
    "game_id": "theme-test-1",
    "game_name": "City Theme Test",
    "game_type": "platformer",
    "theme": "city"
  }'
```

The build will:
1. Generate Unity project with theme parameter
2. Auto-import CityThemePackage.unitypackage
3. Create ThemeManager and ThemeApplier GameObjects
4. Apply city theme at runtime
5. Build to WebGL

## Support

For issues:
- Check service logs: `journalctl -u unity-mcp -f`
- Verify Unity binary: `file /opt/unity/editors/2022.3.45f1/Editor/Unity`
- Test Unity directly: `/opt/unity/editors/2022.3.45f1/Editor/Unity -version`
