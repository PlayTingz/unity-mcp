# User Asset Integration System

## Overview

The Unity MCP Build Service now supports downloading and integrating user-uploaded assets (images, 3D models, audio, video) into Unity WebGL builds.

## Supported Asset Types

### Images
- `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.tga`, `.psd`
- Automatically detected and organized
- Loaded as Unity Texture2D assets

### 3D Models  
- `.fbx`, `.obj`, `.glb`, `.gltf`, `.blend`, `.dae`
- GLB/GLTF supported natively in Unity
- FBX requires Unity's FBX importer

### Audio
- `.mp3`, `.wav`, `.ogg`, `.aiff`, `.aif`
- Loaded as Unity AudioClip assets

### Video
- `.mp4`, `.mov`, `.avi`, `.webm`
- Loaded as Unity VideoClip assets

## Asset Organization

Assets are organized into **slots** - arrays of related assets:

```json
{
  "assets": [
    ["url1.png", "url2.png"],        // Slot 0: Player sprites
    ["bg1.jpg", "bg2.jpg"],          // Slot 1: Backgrounds  
    ["model1.glb", "model2.glb"]     // Slot 2: 3D models
  ]
}
```

## API Usage

### Build Request with Assets

```bash
curl -X POST http://35.226.93.88/build \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "game_id": "game_456",
    "game_name": "MyGame",
    "theme": "city",
    "assets": [
      [
        "https://example.com/image1.png",
        "https://example.com/image2.png"
      ],
      [
        "https://example.com/model1.glb",
        "https://example.com/model2.glb"
      ]
    ]
  }'
```

### Example: Anshu's Test Payload

```json
{
  "user_id": "019985a1-3ab2-737f-a7b3-d26178612233",
  "game_id": "2d860a59-a64f-4176-a60a-4bd738174210",
  "game_name": "endless_runner",
  "game_type": "3d",
  "theme": "city",
  "assets": [
    [
      "https://zzukvfvsascjizivlszo.supabase.co/storage/v1/object/public/image-tingz/user_123/project_1758802451378_lpiqxio99/z760je/c3rdy5r829rge0csjr3sp8x0tr_1_0.png",
      "https://zzukvfvsascjizivlszo.supabase.co/storage/v1/object/public/image-tingz/user_123/project_1758802451378_lpiqxio99/rlcsoe/f31r97t1c1rge0csjqw8anxyd0_1_2.png"
    ],
    [
      "https://zzukvfvsascjizivlszo.supabase.co/storage/v1/object/image-tingz/user_123/project_1758804683638_4z4vhjjjk/enhebe/4x7cj0tkadrme0csg3qvqqtcqr_1_0_3d.glb",
      "https://zzukvfvsascjizivlszo.supabase.co/storage/v1/object/image-tingz/user_123/project_1758802451378_lpiqxio99/7vz5el/xhh3tx9hc1rm80csg3b8ddc3w4_1_1_3d.glb"
    ]
  ],
  "target_platform": "WebGL"
}
```

## Build Process

When assets are provided, the build process includes these additional steps:

1. **Asset Download** (Progress: 25%)
   - Downloads all assets from provided URLs
   - Validates file types and sizes
   - Stores in temporary build directory

2. **Asset Organization** (After Unity project creation)
   - Copies assets into Unity project structure: `Assets/UserContent/`
   - Organizes by slot: `Assets/UserContent/Slot0/`, `Slot1/`, etc.
   - Creates asset manifest JSON file

3. **Asset Loader Generation**
   - Generates `UserAssetLoader.cs` script
   - Provides API to access assets at runtime
   - Maps slots to asset collections

4. **Unity Build**
   - Assets are included in WebGL build
   - Available for use in game logic

## Unity Project Structure

```
UnityProject/
├── Assets/
│   ├── UserContent/
│   │   ├── Slot0/
│   │   │   ├── slot_0_0.png
│   │   │   └── slot_0_1.png
│   │   ├── Slot1/
│   │   │   ├── slot_1_0.glb
│   │   │   └── slot_1_1.glb
│   │   └── asset_manifest.json
│   ├── Scripts/
│   │   └── UserAssetLoader.cs
│   └── Scenes/
│       └── GameScene.unity
```

## Asset Manifest

The `asset_manifest.json` file contains metadata about all downloaded assets:

```json
{
  "slots": {
    "0": [
      {
        "path": "UserContent/Slot0/slot_0_0.png",
        "type": "image",
        "mime_type": "image/png",
        "size": 477806,
        "original_url": "https://..."
      }
    ]
  },
  "by_type": {
    "images": [...],
    "models": [...],
    "audio": [],
    "video": []
  }
}
```

## Using Assets in Unity

The `UserAssetLoader` script provides methods to access downloaded assets:

```csharp
// Get UserAssetLoader component
UserAssetLoader assetLoader = GetComponent<UserAssetLoader>();

// Get image from slot 0, index 0
Texture2D playerSprite = assetLoader.GetImage(0, 0);

// Get 3D model from slot 1, index 0  
GameObject enemyModel = assetLoader.GetModel(1, 0);

// Get audio clip from slot 2, index 0
AudioClip soundEffect = assetLoader.GetAudio(2, 0);

// Apply texture to a material
GetComponent<Renderer>().material.mainTexture = playerSprite;

// Instantiate a model
Instantiate(enemyModel, transform.position, Quaternion.identity);
```

## Asset Manager Implementation

### Key Classes

**`AssetManager`** (`src/asset_manager.py`)
- Downloads assets from URLs
- Detects asset types
- Organizes files for Unity
- Generates loader scripts

**`AssetType`** Enum
- `IMAGE` - Image files
- `MODEL_3D` - 3D model files
- `AUDIO` - Audio files
- `VIDEO` - Video files
- `UNKNOWN` - Unrecognized types

### Main Methods

```python
# Download a single asset
asset = asset_manager.download_asset(url, output_dir)

# Download assets for a slot
assets = asset_manager.download_asset_set(urls, output_dir, "slot_0")

# Download all assets
all_assets = asset_manager.download_all_assets(asset_slots, build_dir)

# Organize into Unity project
manifest = asset_manager.organize_assets_for_unity(assets, project_dir)

# Generate loader script
asset_manager.create_asset_loader_script(project_dir, manifest)
```

## Testing

### Local Testing

```bash
# Test asset manager directly
python3 tests/test_asset_manager.py

# Expected output:
# ✅ Downloaded 5 assets
# ✅ Organized into Unity project
#    Images: 2
#    3D Models: 3
```

### Production Testing

```bash
# Submit build with assets
curl -X POST http://35.226.93.88/build \
  -H "Authorization: Bearer API_KEY" \
  -H "Content-Type: application/json" \
  -d @tests/test_payload_with_assets.json

# Monitor build progress
curl -H "Authorization: Bearer API_KEY" \
  http://35.226.93.88/build/BUILD_ID/status
```

## Error Handling

The asset system handles errors gracefully:

- **Download failures**: Logged as warnings, build continues
- **Invalid URLs**: Skipped, other assets still processed  
- **Unsupported formats**: Detected and logged
- **Network timeouts**: 30-second timeout per asset

Build logs will show:
```
Downloading 5 user assets...
Downloaded 4 assets
Warning: Some assets failed to download: HTTP 404
Integrating user assets into Unity project...
Integrated 2 images, 2 3D models
```

## Deployment

### Manual Deployment

```bash
# Run deployment script
chmod +x deploy-asset-manager.sh
./deploy-asset-manager.sh
```

### Files to Deploy

1. `src/asset_manager.py` - Asset manager implementation
2. `src/unity_build_service.py` - Updated with asset support

### Service Restart

```bash
sudo systemctl restart unity-mcp
sudo systemctl status unity-mcp
```

## Limitations

- **File Size**: No hard limit, but large files (>100MB) may slow builds
- **Timeout**: 30 seconds per asset download
- **Formats**: Only Unity-supported formats work in-game
- **GLB Models**: Supported natively, FBX may need additional setup

## Future Enhancements

- [ ] Asset preprocessing (resize images, optimize models)
- [ ] Asset caching to avoid re-downloading
- [ ] Support for asset bundles
- [ ] Custom asset import settings
- [ ] Asset validation and sanitization
- [ ] Progress reporting during download

## Support

For issues or questions:
- Check build logs: `sudo journalctl -u unity-mcp -f`
- Review asset manifest in build directory
- Test assets locally first with `test_asset_manager.py`
