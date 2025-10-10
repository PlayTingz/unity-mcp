# Unity Package Deployment Documentation

## Overview

Successfully deployed CityThemePackage.unitypackage and com.unity.cloud.gltfast support to the Unity MCP production server.

## What Was Deployed

### 1. CityThemePackage.unitypackage
- **Location**: `/opt/unity-mcp/packages/CityThemePackage.unitypackage`
- **Size**: 3.9MB
- **Purpose**: Custom Unity assets for city-themed games

### 2. Updated Unity Modules

#### unity_project_generator.py
- **Location**: `/opt/unity-mcp/server/lib/unity_project_generator.py`
- **New Features**:
  - `import_unity_package()` method for importing .unitypackage files
  - Automatic manifest.json creation with com.unity.cloud.gltfast v6.8.0
  - Enhanced project structure creation

#### unity_build_service.py  
- **Location**: `/opt/unity-mcp/server/lib/unity_build_service.py`
- **New Features**:
  - Automatic CityThemePackage import during build process
  - Integration point at build step 2.5 (after project creation)
  - Enhanced logging for package import operations

## Unity Packages Included

All new Unity projects will now include:

- `com.unity.cloud.gltfast` v6.8.0 - GLB/GLTF model loading
- `com.unity.collab-proxy` v2.0.5
- `com.unity.feature.development` v1.0.1
- `com.unity.textmeshpro` v3.0.6
- `com.unity.timeline` v1.7.5
- `com.unity.ugui` v1.0.0
- `com.unity.visualscripting` v1.8.0
- All standard Unity modules

## How It Works

### Build Process Flow

1. **Build Request** - User submits build via API
2. **Project Creation** - Unity project structure created with manifest.json
3. **Package Import** ⭐ NEW - CityThemePackage.unitypackage imported
4. **GLTFast Install** ⭐ NEW - Package Manager installs gltfast from manifest
5. **WebGL Build** - Unity builds the project
6. **Deployment** - Game deployed to web directory

### Package Import Method

```python
def import_unity_package(self, project_dir: str, package_path: str) -> bool:
    """Import a Unity package into the project"""
    unity_cmd = [
        self.unity_path,
        "-batchmode",
        "-quit",
        "-projectPath", project_dir,
        "-importPackage", package_path,
        "-logFile", f"/tmp/unity_import_{uuid.uuid4().hex[:8]}.log"
    ]
    # ... execution code
```

### Automatic Integration

During build execution:

```python
# Step 2.5: Import CityThemePackage
city_package_path = "/opt/unity-mcp/packages/CityThemePackage.unitypackage"
if os.path.exists(city_package_path):
    job.build_log.append("Importing CityThemePackage...")
    await asyncio.get_event_loop().run_in_executor(
        None, 
        self.unity_generator.import_unity_package,
        job.project_dir,
        city_package_path
    )
```

## Integration with Production Service

To use these new modules in your production service:

### Option 1: Direct Import

```python
from lib.unity_project_generator import UnityProjectGenerator
from lib.unity_build_service import UnityBuildService

# Initialize with Unity path
generator = UnityProjectGenerator(unity_path="/opt/unity/editors/2022.3.45f1/Editor/Unity")
build_service = UnityBuildService(
    base_build_dir="/opt/unity-mcp/builds",
    base_game_url="http://35.226.93.88/games",
    unity_path="/opt/unity/editors/2022.3.45f1/Editor/Unity"
)
```

### Option 2: Update Existing Service

Modify your existing production service to import from `/opt/unity-mcp/server/lib/`:

```python
import sys
sys.path.insert(0, '/opt/unity-mcp/server/lib')

from unity_project_generator import UnityProjectGenerator
from unity_build_service import UnityBuildService
```

## Testing

To test the new functionality:

```bash
# Test package import standalone
curl -X POST http://35.226.93.88:8080/build \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "game_id": "city-test",
    "game_name": "City Test Game",
    "game_type": "city",
    "asset_set": "v1",
    "assets": []
  }'

# Check build status
curl http://35.226.93.88:8080/build/{build_id}/status \
  -H "Authorization: Bearer your-api-key"
```

Look for these log entries:
- "Importing CityThemePackage..."
- "Unity package imported successfully"
- Package Manager installing gltfast

## File Locations

```
/opt/unity-mcp/
├── packages/
│   └── CityThemePackage.unitypackage (3.9MB)
├── server/
│   └── lib/
│       ├── __init__.py
│       ├── unity_project_generator.py (43K)
│       └── unity_build_service.py (14K)
└── builds/
    └── {build-id}/
        └── UnityProject/
            ├── Assets/
            │   ├── CityTheme/  ← Imported from package
            │   ├── Scenes/
            │   └── Scripts/
            └── Packages/
                └── manifest.json  ← Contains gltfast
```

## Troubleshooting

### Package Not Importing

Check logs at `/tmp/unity_import_*.log` for Unity import errors:

```bash
sudo tail -f /tmp/unity_import_*.log
```

### GLTFast Not Installing

1. Check manifest.json was created:
   ```bash
   cat /opt/unity-mcp/builds/{build-id}/UnityProject/Packages/manifest.json
   ```

2. Verify Unity has internet access for Package Manager

3. Check Unity logs for package resolution errors

### Permission Issues

Ensure packages directory is readable:

```bash
sudo chmod 755 /opt/unity-mcp/packages
sudo chmod 644 /opt/unity-mcp/packages/CityThemePackage.unitypackage
```

## Next Steps

1. **Update Production Service** - Integrate new modules into running service
2. **Test Build** - Create test build to verify package import
3. **Monitor Logs** - Check for successful package import messages
4. **Add More Packages** - Place additional .unitypackage files in `/opt/unity-mcp/packages/`

## Rollback

If issues occur, backups are available:

```bash
# List available backups
ls -la /opt/unity-mcp/backups/

# Restore from backup
sudo cp /opt/unity-mcp/backups/{timestamp}/build_service.py /opt/unity-mcp/server/
```

## Server Information

- **Instance**: unity-mcp-server
- **Zone**: us-central1-a  
- **IP**: 35.226.93.88
- **Unity Version**: 2022.3.45f1
- **License**: Unity Pro

## Deployment Date

October 5, 2025, 10:25 UTC

## Contact

For questions or issues, please check:
- Unity logs: `/tmp/unity_*.log`
- Service logs: `/opt/unity-mcp/logs/`
- Build logs: `/opt/unity-mcp/builds/{build-id}/`
