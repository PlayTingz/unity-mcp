# Unity MCP Production Service - Deployment Instructions

## 🎮 Complete Production Unity WebGL Build Service
**Real Unity Pro integration with no mocks or placeholders**

---

## Files to Deploy

### Main Service File
- `unity_production_service_complete.py` - Complete production service (all-in-one)

### Deployment Configuration

**Requirements file content:**
```txt
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
psutil>=5.9.0
python-multipart>=0.0.6
httpx>=0.25.2
```

**Systemd service file content (`/etc/systemd/system/unity-mcp.service`):**
```ini
[Unit]
Description=Unity MCP Production Build Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/unity-mcp/server
Environment=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/opt/unity
Environment=DISPLAY=:99
ExecStart=/usr/bin/python3 unity_production_service.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=unity-mcp
KillMode=mixed
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
```

---

## Manual Deployment Steps

### 1. Connect to VPS
```bash
ssh root@35.226.93.88
```

### 2. Stop Current Service
```bash
systemctl stop unity-mcp || true
systemctl disable unity-mcp || true
```

### 3. Setup Directories
```bash
mkdir -p /opt/unity-mcp/server
mkdir -p /opt/unity-mcp/builds  
mkdir -p /var/www/html/games
chmod 755 /opt/unity-mcp /opt/unity-mcp/server /opt/unity-mcp/builds /var/www/html/games
```

### 4. Copy Service File
Copy the content of `unity_production_service_complete.py` to:
```bash
/opt/unity-mcp/server/unity_production_service.py
```

### 5. Install Dependencies
```bash
cd /opt/unity-mcp/server
pip3 install fastapi>=0.104.1 uvicorn[standard]>=0.24.0 pydantic>=2.5.0 psutil>=5.9.0 python-multipart>=0.0.6 httpx>=0.25.2
```

### 6. Create Systemd Service
Copy the systemd service content to:
```bash
/etc/systemd/system/unity-mcp.service
```

Then:
```bash
systemctl daemon-reload
```

### 7. Verify Unity Installation
```bash
/opt/unity/Unity -batchmode -quit -logFile /tmp/unity_license_check.log
cat /tmp/unity_license_check.log
```

Should show Unity Pro license is active.

### 8. Start Production Service
```bash
systemctl enable unity-mcp
systemctl start unity-mcp
```

### 9. Verify Service
```bash
systemctl status unity-mcp
curl http://localhost:8080/health
```

### 10. Update Nginx (if needed)
The service runs on port 8080, should be proxied through existing nginx config.

---

## Service Features

### ✅ Real Unity Integration
- **Unity Pro 2022.3.45f1** with active license
- **Real project generation** with scenes, game objects, cameras, lighting
- **Actual WebGL compilation** using Unity command line
- **C# build scripts** for automated WebGL builds
- **Production error handling** and build monitoring

### ✅ Complete Build Pipeline
1. **Game Specification** → Generate Unity project with real scenes
2. **Project Creation** → Create Unity project structure, settings, scripts
3. **Unity Compilation** → Execute Unity batchmode WebGL build
4. **Web Deployment** → Deploy to `/var/www/html/games/`
5. **URL Generation** → Generate playable game URLs

### ✅ Production API
- **FastAPI** with full OpenAPI documentation
- **JWT Authentication** with bearer token
- **Build Queue** with async processing
- **Real-time Status** tracking and progress updates
- **Health Monitoring** with system metrics
- **Error Handling** with detailed build logs

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|---------|---------|
| `/health` | GET | Service health (no auth required) |
| `/status` | GET | Detailed service status |
| `/build` | POST | Create Unity build |
| `/build/{id}/status` | GET | Get build progress |
| `/build/{id}/stop` | PUT | Cancel running build |
| `/docs` | GET | Interactive API documentation |

### Authentication
All endpoints (except health) require:
```
Authorization: Bearer 013e283d7f3a2d45dcdbe7a2b4676a61ff58e7a576930ac3ea66c85d3882f197
```

---

## Build Request Format

```json
{
  "user_id": "test-user-123",
  "game_id": "cube-game-456", 
  "game_name": "My Unity Game",
  "game_type": "platformer",
  "asset_set": "v1",
  "assets": [],
  "target_platform": "WebGL"
}
```

### Game Types Supported
- `"platformer"` - Creates player + ground scene
- `"default"` - Creates simple rotating cube scene

---

## Expected Results

### ✅ After Deployment
- Service running on http://35.226.93.88:8080
- Health endpoint: http://35.226.93.88/health  
- API docs: http://35.226.93.88/docs

### ✅ After Build Request
- Real Unity project generated in `/opt/unity-mcp/builds/{build_id}/`
- Unity WebGL compilation using Unity Pro headless
- Game deployed to `/var/www/html/games/{build_id}/`
- Playable game at http://35.226.93.88/games/{build_id}/

### ✅ No More Placeholders
- **Real Unity scenes** with actual game objects
- **Real WebGL builds** with Unity loader, WASM, data files
- **Real error handling** when Unity builds fail
- **Real build progress** tracking through Unity compilation stages

---

## Monitoring

### Service Logs
```bash
journalctl -u unity-mcp -f
```

### Build Logs  
```bash
ls /tmp/unity_build_*.log
tail -f /tmp/unity-mcp-production.log
```

### Build Status
```bash
curl -H "Authorization: Bearer 013e283d7f3a2d45dcdbe7a2b4676a61ff58e7a576930ac3ea66c85d3882f197" http://35.226.93.88/status
```

---

## 🎉 Production Ready!

This deployment provides a **complete production Unity WebGL build service** with:

- ✅ **Real Unity Pro integration** (no mocks/placeholders)
- ✅ **Automated project generation** with scenes and game objects  
- ✅ **WebGL compilation** using Unity command line tools
- ✅ **Production API** with authentication and monitoring
- ✅ **Scalable architecture** with async build processing
- ✅ **Web deployment** with playable game URLs

The service transforms API requests into real, playable Unity WebGL games using production Unity Pro licensing and compilation.