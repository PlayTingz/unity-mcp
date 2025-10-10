# CityThemePackage - Theme System Integration Guide

## Overview

The CityThemePackage includes a complete theme switching system that allows dynamic asset swapping at runtime. This document explains how to integrate it with the Unity MCP API.

## Theme System Architecture

### Core Components

1. **ThemeData.cs** - ScriptableObject that defines a theme
   - Contains theme name and tagged assets
   - Maps tags to prefabs

2. **ThemeManager.cs** - Runtime theme controller
   - `SetTheme(ThemeData)` - Switches to a new theme
   - `ApplyTheme()` - Applies current theme to all Themeable objects
   - `ResetTheme()` - Reverts to original assets

3. **Themeable.cs** - Component for objects that can be themed
   - Automatically swaps prefabs when theme changes
   - Maintains reference to original
   - Instantiates themed replacement

4. **ThemeTag.cs** - Identifies what type of object this is
   - Tags: "Theme", "Decorations", "Obstacle"

### Included Theme: CityTheme

**Theme Name**: `City`

**Tagged Assets**:
- `Theme` → Track.prefab (city-style track/road)
- `Decorations` → Decorations.prefab (city buildings, signs)
- `Obstacle` → Obstacles.prefab (city-themed obstacles)

**Asset Packs Included**:
- Pandazole City Town Pack (buildings, roads, props)
- Pandazole Farm Ranch Pack (farm assets - for future themes)
- Drivable Low Poly Cars
- PolygonSciFiSpace (for future space theme)

## How Theme Switching Works

### Runtime Flow

1. **Scene Setup**:
   - Objects have `Themeable` + `ThemeTag` components
   - Original prefabs are in the scene
   - ThemeManager exists in scene

2. **Theme Application**:
   ```csharp
   // Set and apply a theme
   themeManager.SetTheme(cityThemeData);
   
   // Process:
   // 1. ThemeManager finds all Themeable objects
   // 2. For each Themeable:
   //    - Gets its ThemeTag (e.g., "Obstacle")
   //    - Looks up prefab in theme's assets
   //    - Destroys current themed instance (if any)
   //    - Instantiates new themed prefab
   //    - Hides original object
   ```

3. **Theme Reset**:
   ```csharp
   themeManager.ResetTheme();
   // - Destroys themed instances
   // - Shows original objects
   ```

## API Integration

### Option 1: Add Theme Parameter to Build Request

Add a `theme` parameter to the build API:

```json
{
  "user_id": "user-123",
  "game_id": "city-game",
  "game_name": "City Runner",
  "game_type": "platformer",
  "theme": "city",  // ← NEW PARAMETER
  "assets": []
}
```

### Option 2: Theme Selection in Game Scene

Modify the generated Unity scene to include ThemeManager and apply theme at startup:

```csharp
// In generated scene's startup script
void Start()
{
    // Load theme based on build request
    ThemeData theme = Resources.Load<ThemeData>($"Themes/{themeName}Theme");
    FindObjectOfType<ThemeManager>().SetTheme(theme);
}
```

### Option 3: WebGL Theme API

Add JavaScript interface for runtime theme switching in WebGL:

```csharp
// In Unity C# script
[DllImport("__Internal")]
private static extern void ReceiveThemeChange(string themeName);

public void SetThemeFromJS(string themeName)
{
    ThemeData theme = Resources.Load<ThemeData>($"Themes/{themeName}Theme");
    themeManager.SetTheme(theme);
}
```

```javascript
// In WebGL game page
function changeTheme(themeName) {
    gameInstance.SendMessage("ThemeManager", "SetThemeFromJS", themeName);
}
```

## Implementation Plan

### Step 1: Update Build Service to Support Themes

Modify `unity_build_service.py`:

```python
@dataclass
class BuildRequest:
    user_id: str
    game_id: str
    game_name: str
    game_type: str = "platformer"
    asset_set: str = "v1"
    assets: Optional[List[List[str]]] = None
    target_platform: str = "WebGL"
    theme: str = "city"  # ← Add theme parameter
```

### Step 2: Generate Theme-Aware Scene

Modify `_create_game_scene()` in `unity_project_generator.py`:

1. Add ThemeManager GameObject
2. Add ThemeData ScriptableObject reference
3. Add Themeable + ThemeTag components to objects
4. Create startup script that applies theme

### Step 3: Create Theme Application Script

Add to project generation:

```csharp
// Assets/Scripts/ThemeApplier.cs
using UnityEngine;

public class ThemeApplier : MonoBehaviour
{
    [SerializeField] private string themeName = "City";
    
    void Start()
    {
        var themeData = Resources.Load<ThemeData>($"Themes/{themeName}Theme");
        if (themeData != null)
        {
            var manager = FindObjectOfType<ThemeManager>();
            if (manager != null)
            {
                manager.SetTheme(themeData);
            }
        }
    }
}
```

### Step 4: Available Themes

Based on the package contents:

1. **City Theme** (implemented) ✅
   - City buildings and roads
   - Urban obstacles
   - City decorations

2. **Farm Theme** (assets included, needs ThemeData)
   - Farm buildings
   - Trees and farmland
   - Farm obstacles

3. **Space Theme** (assets included, needs ThemeData)
   - Sci-fi space assets
   - Future implementation

## API Endpoints for Theme Management

### Recommended API Additions

```python
# GET /themes - List available themes
@app.get("/themes")
async def list_themes():
    return {
        "themes": [
            {
                "id": "city",
                "name": "City",
                "description": "Urban city theme with buildings and roads",
                "assets": ["buildings", "roads", "vehicles", "decorations"]
            },
            {
                "id": "farm",
                "name": "Farm",
                "description": "Rural farm theme with barns and fields",
                "assets": ["barn", "farmland", "trees", "animals"]
            }
        ]
    }

# POST /build with theme support
@app.post("/build")
async def create_build(request: BuildRequest):
    # request.theme = "city" or "farm"
    # Pass to build service
    # Build service generates scene with correct theme applied
    pass
```

### Build Request with Theme

```bash
curl -X POST http://35.226.93.88:8080/build \
  -H "Authorization: Bearer {API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "game_id": "themed-game",
    "game_name": "City Runner",
    "game_type": "runner",
    "theme": "city",
    "assets": []
  }'
```

## Theme Data Structure

### ThemeData ScriptableObject Format

```yaml
%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!114 &11400000
MonoBehaviour:
  m_Script: {fileID: 11500000, guid: ThemeData-GUID}
  m_Name: CityTheme
  m_EditorClassIdentifier: 
  themeName: City
  assets:
  - tag: Track
    prefab: {fileID: xxx, guid: track-prefab-guid, type: 3}
  - tag: Decorations
    prefab: {fileID: xxx, guid: decorations-guid, type: 3}
  - tag: Obstacle
    prefab: {fileID: xxx, guid: obstacle-guid, type: 3}
```

## Integration Checklist

- [ ] Add `theme` parameter to BuildRequest model
- [ ] Update API documentation with theme support
- [ ] Modify scene generator to include ThemeManager
- [ ] Add ThemeApplier startup script to generated scenes
- [ ] Create ThemeData assets for available themes
- [ ] Add theme validation in build service
- [ ] Update /themes endpoint to list available themes
- [ ] Test theme switching with CityTheme
- [ ] Create additional themes (Farm, Space)
- [ ] Add theme preview images/screenshots

## Testing Theme System

### Test 1: Build with City Theme

```bash
curl -X POST http://35.226.93.88:8080/build \
  -H "Authorization: Bearer {API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test",
    "game_id": "city-test",
    "game_name": "City Theme Test",
    "theme": "city"
  }'
```

### Test 2: Verify Theme Assets in Build

After build completes:
1. Check `/opt/unity-mcp/builds/{build-id}/UnityProject/Assets/Themes/CityTheme.asset` exists
2. Check `ThemeManager` GameObject in scene
3. Check `Themeable` components on game objects
4. Verify city assets are loaded in WebGL build

### Test 3: Runtime Theme Switch (Future)

WebGL game with theme switcher UI:
```html
<button onclick="changeTheme('city')">City</button>
<button onclick="changeTheme('farm')">Farm</button>
```

## Summary

The CityThemePackage provides a complete theme system with:

✅ **Theme Switching**: Runtime asset swapping via ThemeManager
✅ **City Theme**: Complete city-themed assets ready to use
✅ **Extensible**: Easy to add new themes (farm, space, etc.)
✅ **API Ready**: Can integrate with build requests

**Next Steps**:
1. Add `theme` parameter to build API
2. Generate scenes with ThemeManager and theme applied
3. Test with CityTheme
4. Expand to additional themes

**Files to Modify**:
- `unity_build_service.py` - Add theme parameter
- `unity_project_generator.py` - Generate theme-aware scenes
- Production service API - Add theme endpoints

The theme system is fully functional in the package and ready for API integration!
