# Unity MCP API Integration Guide

## Overview

Your external API uploads assets to S3/Supabase, then sends asset URLs to the Unity MCP Build Service. The service downloads the assets and integrates them into Unity WebGL builds.

---

## Workflow

```
External API → Upload Assets to S3/Supabase → Get URLs → Send to Unity MCP → Unity Build with Assets
```

**Example Flow**:
1. User uploads images/models via your API
2. Your API stores them in S3/Supabase bucket
3. Your API gets public URLs for the uploaded files
4. Your API sends build request to Unity MCP with asset URLs
5. Unity MCP downloads assets and builds the game
6. Game is deployed with all assets integrated

---

## API Endpoint

### POST /build

**URL**: `http://35.226.93.88/build`

**Authentication**: Bearer token (API Key)

**Headers**:
```
Authorization: Bearer 013e283d7f3a2d45dcdbe7a2b4676a61ff58e7a576930ac3ea66c85d3882f197
Content-Type: application/json
```

---

## Request Schema

### Basic Request (No Assets)
```json
{
  "user_id": "string",
  "game_id": "string", 
  "game_name": "string",
  "game_type": "platformer|3d|puzzle",
  "theme": "city|farm|space",
  "target_platform": "WebGL"
}
```

### Request with Assets
```json
{
  "user_id": "string",
  "game_id": "string",
  "game_name": "string", 
  "game_type": "3d",
  "theme": "city",
  "assets": [
    ["url1", "url2", ...],  // Slot 0: e.g., character sprites
    ["url3", "url4", ...],  // Slot 1: e.g., 3D models
    ["url5", "url6", ...]   // Slot 2: e.g., background music
  ],
  "target_platform": "WebGL"
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | ✅ Yes | Your user's ID |
| `game_id` | string | ✅ Yes | Unique game identifier |
| `game_name` | string | ✅ Yes | Display name for the game |
| `game_type` | string | No | Game type (default: "platformer") |
| `theme` | string | No | Visual theme (default: "city") |
| `assets` | array | No | Array of asset URL arrays (slots) |
| `target_platform` | string | No | Build platform (default: "WebGL") |

---

## Asset Organization

### Slot-Based System

Assets are organized into **slots** - each slot is an array of related assets:

```json
"assets": [
  // Slot 0: Character/Player assets
  [
    "https://your-bucket.s3.amazonaws.com/user123/character-idle.png",
    "https://your-bucket.s3.amazonaws.com/user123/character-run.png"
  ],
  
  // Slot 1: 3D Models
  [
    "https://your-bucket.s3.amazonaws.com/user123/building-model.glb",
    "https://your-bucket.s3.amazonaws.com/user123/vehicle-model.glb"
  ],
  
  // Slot 2: Audio
  [
    "https://your-bucket.s3.amazonaws.com/user123/background-music.mp3",
    "https://your-bucket.s3.amazonaws.com/user123/jump-sound.wav"
  ]
]
```

### Supported Asset Types

**Images**
- Extensions: `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.tga`, `.psd`
- Use cases: Character sprites, UI elements, backgrounds, textures

**3D Models**
- Extensions: `.glb`, `.gltf`, `.fbx`, `.obj`, `.blend`, `.dae`
- Use cases: Characters, environment objects, vehicles, buildings
- **Recommended**: `.glb` (best Unity WebGL support)

**Audio**
- Extensions: `.mp3`, `.wav`, `.ogg`, `.aiff`, `.aif`
- Use cases: Sound effects, background music, voice

**Video**
- Extensions: `.mp4`, `.mov`, `.avi`, `.webm`
- Use cases: Cutscenes, background animations

---

## Example Requests

### Example 1: Game with Images and 3D Models (Supabase)

```bash
curl -X POST http://35.226.93.88/build \
  -H "Authorization: Bearer 013e283d7f3a2d45dcdbe7a2b4676a61ff58e7a576930ac3ea66c85d3882f197" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_12345",
    "game_id": "racing-game-001",
    "game_name": "City Racer",
    "game_type": "3d",
    "theme": "city",
    "assets": [
      [
        "https://zzukvfvsascjizivlszo.supabase.co/storage/v1/object/public/game-assets/user123/car-texture-1.png",
        "https://zzukvfvsascjizivlszo.supabase.co/storage/v1/object/public/game-assets/user123/car-texture-2.png"
      ],
      [
        "https://zzukvfvsascjizivlszo.supabase.co/storage/v1/object/public/game-assets/user123/race-car.glb",
        "https://zzukvfvsascjizivlszo.supabase.co/storage/v1/object/public/game-assets/user123/track.glb"
      ]
    ],
    "target_platform": "WebGL"
  }'
```

### Example 2: Game with Audio (AWS S3)

```bash
curl -X POST http://35.226.93.88/build \
  -H "Authorization: Bearer 013e283d7f3a2d45dcdbe7a2b4676a61ff58e7a576930ac3ea66c85d3882f197" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_67890",
    "game_id": "puzzle-game-002",
    "game_name": "Block Puzzle",
    "game_type": "puzzle",
    "assets": [
      [
        "https://my-game-assets.s3.us-west-2.amazonaws.com/blocks/red-block.png",
        "https://my-game-assets.s3.us-west-2.amazonaws.com/blocks/blue-block.png"
      ],
      [
        "https://my-game-assets.s3.us-west-2.amazonaws.com/audio/pop-sound.wav",
        "https://my-game-assets.s3.us-west-2.amazonaws.com/audio/victory-sound.mp3"
      ]
    ]
  }'
```

### Example 3: JavaScript/TypeScript Integration

```typescript
interface BuildRequest {
  user_id: string;
  game_id: string;
  game_name: string;
  game_type?: 'platformer' | '3d' | 'puzzle';
  theme?: 'city' | 'farm' | 'space';
  assets?: string[][];
  target_platform?: 'WebGL';
}

async function createUnityBuild(
  userId: string,
  gameId: string,
  gameName: string,
  assetUrls: string[][]
): Promise<string> {
  const API_URL = 'http://35.226.93.88/build';
  const API_KEY = '013e283d7f3a2d45dcdbe7a2b4676a61ff58e7a576930ac3ea66c85d3882f197';
  
  const request: BuildRequest = {
    user_id: userId,
    game_id: gameId,
    game_name: gameName,
    game_type: '3d',
    theme: 'city',
    assets: assetUrls,
    target_platform: 'WebGL'
  };
  
  const response = await fetch(API_URL, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(request)
  });
  
  const data = await response.json();
  return data.build_id;
}

// Usage example
const assetUrls = [
  // Slot 0: Character sprites
  [
    'https://your-bucket.s3.amazonaws.com/player-idle.png',
    'https://your-bucket.s3.amazonaws.com/player-run.png'
  ],
  // Slot 1: 3D models
  [
    'https://your-bucket.s3.amazonaws.com/enemy.glb',
    'https://your-bucket.s3.amazonaws.com/pickup.glb'
  ]
];

const buildId = await createUnityBuild(
  'user_123',
  'game_456', 
  'My Awesome Game',
  assetUrls
);

console.log(`Build started: ${buildId}`);
```

---

## Response Format

### Success Response (202 Accepted)

```json
{
  "build_id": "77403378-a421-4503-9a39-326dd0fd0109",
  "status": "queued",
  "message": "Unity Pro build submitted successfully"
}
```

### Error Responses

**401 Unauthorized** - Invalid API key
```json
{
  "detail": "Invalid API key"
}
```

**422 Validation Error** - Missing required fields
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "user_id"],
      "msg": "Field required"
    }
  ]
}
```

---

## Build Status Monitoring

### GET /build/{build_id}/status

**URL**: `http://35.226.93.88/build/{build_id}/status`

**Headers**:
```
Authorization: Bearer 013e283d7f3a2d45dcdbe7a2b4676a61ff58e7a576930ac3ea66c85d3882f197
```

**Response**:
```json
{
  "id": "77403378-a421-4503-9a39-326dd0fd0109",
  "user_id": "user_123",
  "game_id": "game_456",
  "game_name": "My Game",
  "status": "running",
  "progress": 50,
  "message": "Unity build in progress",
  "play_url": null,
  "download_url": null,
  "created_at": "2025-10-06T09:46:35.184240",
  "updated_at": "2025-10-06T09:56:38.774000"
}
```

### Build Status Values

| Status | Description |
|--------|-------------|
| `queued` | Build is waiting in queue |
| `running` | Build is currently processing |
| `completed` | Build finished successfully |
| `failed` | Build encountered an error |
| `cancelled` | Build was stopped by user |

### Progress Indicators

| Progress | Phase |
|----------|-------|
| 0% | Queued |
| 25% | Downloading assets |
| 30% | Creating Unity project |
| 40% | Importing theme package |
| 50% | Building WebGL |
| 80% | Deploying game |
| 100% | Complete |

### Completed Build Response

```json
{
  "status": "completed",
  "progress": 100,
  "message": "Unity Pro build completed successfully",
  "play_url": "http://35.226.93.88/games/77403378-a421-4503-9a39-326dd0fd0109/",
  "download_url": "http://35.226.93.88/games/77403378-a421-4503-9a39-326dd0fd0109/build.zip"
}
```

---

## Asset Requirements

### URL Requirements

✅ **Must be publicly accessible** (no authentication required)  
✅ **Must use HTTP or HTTPS**  
✅ **Must return correct MIME type** (`image/png`, `model/gltf-binary`, etc.)  
✅ **Should be permanent URLs** (don't expire during build)

❌ Signed/temporary URLs that expire quickly  
❌ URLs requiring authentication headers  
❌ URLs behind VPNs or firewalls

### File Size Limits

- Individual file: No hard limit, but **<100MB recommended**
- Total assets per build: **<500MB recommended**
- Build timeout: 30 minutes

### Best Practices

1. **Use permanent URLs**: Don't use pre-signed URLs that expire
2. **Enable CORS**: If serving from different domain
3. **Optimize assets**: Compress images, optimize 3D models
4. **Use GLB for 3D**: Best Unity WebGL compatibility
5. **Test URLs**: Verify they're accessible before sending to API

---

## Integration Workflow

### Your External API Flow

```typescript
// 1. User uploads file to your API
POST /api/upload-asset
{
  "user_id": "user_123",
  "file": <multipart-file>
}

// 2. Your API uploads to S3/Supabase
const s3Url = await uploadToS3(file);
// Returns: "https://bucket.s3.amazonaws.com/user_123/asset_abc.png"

// 3. Store asset URL in your database
await db.assets.create({
  user_id: "user_123",
  asset_url: s3Url,
  asset_type: "image",
  slot: 0
});

// 4. When user creates game, collect all asset URLs
const userAssets = await db.assets.findMany({
  user_id: "user_123",
  game_id: "game_456"
});

// 5. Organize into slots
const assetsBySlot = [
  userAssets.filter(a => a.slot === 0).map(a => a.asset_url),
  userAssets.filter(a => a.slot === 1).map(a => a.asset_url),
  userAssets.filter(a => a.slot === 2).map(a => a.asset_url)
];

// 6. Send to Unity MCP API
const buildId = await createUnityBuild(
  "user_123",
  "game_456",
  "My Game",
  assetsBySlot
);

// 7. Poll for completion
const checkStatus = setInterval(async () => {
  const status = await getBuildStatus(buildId);
  
  if (status.status === 'completed') {
    clearInterval(checkStatus);
    console.log('Game ready:', status.play_url);
    // Update your database with play_url
    await db.games.update({
      game_id: "game_456",
      play_url: status.play_url
    });
  }
}, 10000); // Check every 10 seconds
```

---

## Asset Manifest

After the build completes, an `asset_manifest.json` is generated inside the Unity project with metadata about all assets:

```json
{
  "slots": {
    "0": [
      {
        "path": "UserContent/Slot0/slot_0_0.png",
        "type": "image",
        "mime_type": "image/png",
        "size": 477806,
        "original_url": "https://your-bucket.s3.amazonaws.com/asset1.png"
      }
    ],
    "1": [...]
  },
  "by_type": {
    "images": [...],
    "models": [...],
    "audio": [...],
    "video": [...]
  }
}
```

---

## Common Issues & Solutions

### Issue: Assets not downloading

**Cause**: URLs are not publicly accessible  
**Solution**: Ensure S3 bucket has public read access or use signed URLs with long expiration

### Issue: Build fails with "timeout"

**Cause**: Assets are too large or network is slow  
**Solution**: Optimize assets, use CDN, or increase timeout

### Issue: 3D models don't appear in game

**Cause**: Unsupported format or large file size  
**Solution**: Convert to GLB format, optimize mesh/textures

### Issue: Images appear black in Unity

**Cause**: Incorrect alpha channel or color space  
**Solution**: Save as PNG with RGB (not CMYK), check alpha transparency

---

## Testing

### Test Payload (Ready to Use)

Save as `test-build.json`:
```json
{
  "user_id": "test-user-001",
  "game_id": "test-game-001",
  "game_name": "Asset Test Game",
  "game_type": "3d",
  "theme": "city",
  "assets": [
    [
      "https://zzukvfvsascjizivlszo.supabase.co/storage/v1/object/public/image-tingz/user_123/project_1758802451378_lpiqxio99/z760je/c3rdy5r829rge0csjr3sp8x0tr_1_0.png"
    ],
    [
      "https://zzukvfvsascjizivlszo.supabase.co/storage/v1/object/image-tingz/user_123/project_1758804683638_4z4vhjjjk/enhebe/4x7cj0tkadrme0csg3qvqqtcqr_1_0_3d.glb"
    ]
  ],
  "target_platform": "WebGL"
}
```

**Test command**:
```bash
curl -X POST http://35.226.93.88/build \
  -H "Authorization: Bearer 013e283d7f3a2d45dcdbe7a2b4676a61ff58e7a576930ac3ea66c85d3882f197" \
  -H "Content-Type: application/json" \
  -d @test-build.json
```

---

## Security

### API Key Management

- **Production Key**: `013e283d7f3a2d45dcdbe7a2b4676a61ff58e7a576930ac3ea66c85d3882f197`
- Store securely in environment variables
- Never expose in client-side code
- Use backend-to-backend communication only

### Asset URL Security

- Use HTTPS for all asset URLs
- Validate URLs before sending to API
- Sanitize user-provided URLs to prevent injection
- Consider using signed URLs for sensitive assets

---

## Rate Limits

- No hard rate limits currently
- Recommended: **Max 10 concurrent builds per user**
- Build queue processes one build at a time
- Typical build time: **15-25 minutes**

---

## Support

**Verified Working**:
- ✅ Supabase Storage URLs
- ✅ AWS S3 public URLs  
- ✅ Cloudflare R2 URLs
- ✅ Google Cloud Storage URLs
- ✅ Any public HTTP/HTTPS URL

**Documentation**:
- API Guide: This document
- Asset System: `ASSET_SYSTEM_GUIDE.md`
- Test Results: `ASSET_INTEGRATION_SUCCESS.md`

**Production Example**:
- Build ID: `77403378-a421-4503-9a39-326dd0fd0109`
- Live Game: http://35.226.93.88/games/77403378-a421-4503-9a39-326dd0fd0109/index.html
