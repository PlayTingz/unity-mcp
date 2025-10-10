# 🚀 Quick Start: Deploy Fixes to Production

## One-Command Deployment

```bash
./scripts/deploy-fixes.sh
```

This will:
1. ✅ Upload updated Python files
2. ✅ Create shared Unity project  
3. ✅ Import CityThemePackage (if available)
4. ✅ Set permissions
5. ✅ Restart service
6. ✅ Health check

---

## Manual Deployment (if needed)

### 1. Setup Shared Project (Local Test)
```bash
# Test locally first
sudo python3 scripts/setup-shared-project.py
ls -la /opt/unity-mcp/shared-project/
```

### 2. Upload Files
```bash
scp src/unity_project_generator.py root@35.226.93.88:/opt/unity-mcp/server/
scp src/unity_build_service.py root@35.226.93.88:/opt/unity-mcp/server/
scp src/asset_manager.py root@35.226.93.88:/opt/unity-mcp/server/
scp src/production_unity_service.py root@35.226.93.88:/opt/unity-mcp/server/unity_production_service.py
```

### 3. Setup Shared Project on Server
```bash
ssh root@35.226.93.88
python3 /tmp/setup-shared-project.py
```

### 4. Import CityTheme (Optional)
```bash
# On server
/opt/unity/Unity -batchmode -quit \
  -projectPath /opt/unity-mcp/shared-project \
  -importPackage /opt/unity-mcp/CityThemePackage.unitypackage \
  -logFile /tmp/import.log
```

### 5. Restart Service
```bash
systemctl restart unity-mcp
systemctl status unity-mcp
```

### 6. Test
```bash
curl http://35.226.93.88/health
```

---

## Test a Build

```bash
curl -X POST http://35.226.93.88/build \
  -H 'Authorization: Bearer 013e283d7f3a2d45dcdbe7a2b4676a61ff58e7a576930ac3ea66c85d3882f197' \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "test",
    "game_id": "test123",
    "game_name": "TestGame",
    "game_type": "platformer"
  }'
```

Expected response:
```json
{
  "build_id": "abc-123-def",
  "status": "queued",
  "message": "Build started"
}
```

Check status:
```bash
curl http://35.226.93.88/status/abc-123-def
```

---

## What Changed?

### Files Modified
- ✏️ `src/unity_project_generator.py` - BuildScript now uses EditorBuildSettings
- ✏️ `src/unity_build_service.py` - Tracks scene names
- ➕ `scripts/setup-shared-project.py` - Creates shared project
- ➕ `scripts/deploy-fixes.sh` - Automated deployment

### New Files on Server
- `/opt/unity-mcp/shared-project/` - Complete Unity project
- `/opt/unity-mcp/shared-project/Assets/Scripts/SimpleGameManager.cs` - Game loop script
- `/opt/unity-mcp/shared-project/Assets/Editor/BuildScript.cs` - Fixed build script

---

## Troubleshooting

### "Shared project not found"
```bash
# Run setup script on server
ssh root@35.226.93.88 "python3 /tmp/setup-shared-project.py"
```

### Service won't start
```bash
# Check logs
ssh root@35.226.93.88 "journalctl -u unity-mcp -n 50"
```

### Build fails
```bash
# Check Unity logs
ssh root@35.226.93.88 "tail -100 /tmp/unity_build_*.log"
```

---

## Rollback (if needed)

```bash
# SSH to server
ssh root@35.226.93.88

# Restore previous version
cd /opt/unity-mcp/server
cp unity_production_service.py.backup unity_production_service.py

# Restart
systemctl restart unity-mcp
```

---

## Success Criteria

✅ Health endpoint returns `{"status": "healthy"}`
✅ Build completes in ~6 minutes (not 20+)
✅ WebGL game loads in browser
✅ No "Script terminated by timeout" errors
✅ SimpleGameManager appears in Unity console logs

---

**Need Help?** Check `FIXES_APPLIED.md` for detailed technical documentation.
