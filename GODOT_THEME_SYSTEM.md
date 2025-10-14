# Godot Theme System - City Theme Integration

## Overview

This document describes the conversion of the Unity City Theme package to Godot, including 3D models and gameplay scripts.

## Assets Extracted

### City Theme 3D Models (FBX)
Uploaded to server at `/opt/godot-themes/city/models/`:

1. **Env_Road_Straight_01.fbx** (19KB) - Straight road segment
2. **Prop_OilBerrel_01.fbx** (32KB) - Oil barrel obstacle
3. **Prop_Plant_01.fbx** (26KB) - Decorative plant
4. **Prop_RoadCone_01.fbx** (21KB) - Traffic cone obstacle
5. **Prop_StreetSign_Stop.fbx** (36KB) - Stop sign prop

### Textures
Uploaded to `/opt/godot-themes/city/textures/`:
- **PandaMat.png** (8.8KB) - Main material texture for city assets

## Scripts Converted

### Core Game Scripts (Unity C# → Godot GDScript)

#### 1. game_manager.gd
**Original**: `Assets/Scripts/GameManager.cs`

**Purpose**: Singleton game manager handling:
- World speed and progression
- Score tracking
- Coin collection
- Power-up state management (magnet, multiplier)
- UI updates

**Key Features**:
- Static instance pattern
- Progressive speed increase every 200 points
- Score multiplier system
- Magnet power-up with duration timer

#### 2. environment_mover.gd
**Original**: `Assets/Scripts/EnvironmentMover.cs`

**Purpose**: Moves objects backward to simulate forward player movement

**Usage**: Attach to track segments, obstacles, and decorations

#### 3. collectible.gd
**Original**: `Assets/Scripts/Collectible.cs`

**Purpose**: Handles coins and collectible items with:
- Rotation animation
- Magnet attraction effect
- Player collision detection
- Automatic collection

#### 4. player_controller.gd
**Original**: `Assets/Scripts/PlayerController.cs`

**Purpose**: 3-lane endless runner player control with:
- Lane switching (left/center/right)
- Jumping physics
- Gravity
- Input handling (keyboard)
- Death state

## Unity vs Godot Script Differences

| Feature | Unity (C#) | Godot (GDScript) |
|---------|------------|------------------|
| Singleton | `public static GameManager Instance` | `static var instance: Node` |
| Update Loop | `void Update()` | `func _process(delta):` |
| Physics | `void FixedUpdate()` | `func _physics_process(delta):` |
| Collision | `OnTriggerEnter(Collider other)` | `body_entered.connect()` |
| Transform | `transform.Translate()` | `translate()` |
| Tags | `CompareTag("Player")` | `is_in_group("player")` |
| Find Objects | `FindObjectsOfType<T>()` | `get_tree().get_nodes_in_group()` |
| Destroy | `Destroy(gameObject)` | `queue_free()` |

## Scripts Still Needed

### High Priority
1. **level_generator.gd** - Spawn track segments dynamically
2. **obstacle.gd** - Handle obstacle collisions (game over)
3. **smooth_follow_camera.gd** - Camera following player
4. **floating_animation.gd** - Bob and rotate collectibles

### Medium Priority
5. **power_up.gd** - Power-up types and effects
6. **theme_manager.gd** - Load and apply City theme assets

### Low Priority
7. **random_rotator.gd** - Random rotation for props
8. **scroller.gd** - Scrolling background/skybox

## Integration Plan

### Phase 1: Basic Runner (Current)
- ✅ Core scripts converted
- ✅ City theme models uploaded
- ⏳ Generate simple 3-lane runner scene
- ⏳ Test player movement and collisions

### Phase 2: Level Generation
- Create track segment prefabs using City models
- Implement LevelGenerator for infinite track
- Spawn obstacles and collectibles
- Test continuous level scrolling

### Phase 3: Theme System
- Load FBX models from `/opt/godot-themes/city/`
- Create Godot scene variants for each prop
- Implement theme selection API parameter
- Generate themed game builds

### Phase 4: Polish
- Add power-ups (magnet, multiplier)
- Smooth camera following
- Floating coin animations
- UI (score, coins, power-up indicators)

## File Locations

### Server
- **Theme Assets**: `/opt/godot-themes/city/`
- **Build Service**: `/opt/unity-mcp/server/`
- **Godot Scripts**: Embedded in generated projects

### Local
- **Scripts**: `/home/jpb/dev/tingz/unity-mcp/src/godot_scripts/`
- **Extracted Assets**: `/home/jpb/dev/tingz/unity-mcp/godot-city-theme/`

## Next Steps

1. Update `godot_project_generator.py` to:
   - Copy theme assets into generated projects
   - Include converted GDScript files
   - Create proper 3-lane runner scene structure

2. Implement `level_generator.gd`:
   - Spawn track segments from City theme
   - Place obstacles (barrels, cones, signs)
   - Add collectibles (coins)

3. Create runner game scene template:
   - Player (CharacterBody3D with controller)
   - Camera (following player)
   - GameManager (autoload singleton)
   - Track segments with City models

4. Test complete gameplay loop:
   - Player movement (3 lanes, jumping)
   - Obstacle collisions (game over)
   - Coin collection
   - Score progression

## API Compatibility

The theme system will integrate seamlessly with the existing build API:

```json
{
  "user_id": "user123",
  "game_id": "game456",
  "game_name": "City Runner",
  "game_type": "platformer",
  "theme": "city",
  "assets": []
}
```

The `theme` parameter will load City theme 3D models and apply appropriate styling.
