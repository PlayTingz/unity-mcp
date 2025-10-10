#!/usr/bin/env python3
"""
Production Godot MCP Service
Real Godot WebGL build service - Production Ready
"""

import os
import sys
import json
import logging
import asyncio
import psutil
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager

current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from godot_build_service import GodotBuildService, BuildRequest as GodotBuildRequest

API_KEY = "j_QJTDk9IfuxWh1G_jqjdLBeLBLuLyaFepi-6Rtfwkg"
GODOT_PATH = "/usr/local/bin/godot"
BUILD_BASE_DIR = "/opt/unity-mcp/builds"
GAME_BASE_URL = "https://35-226-93-88.nip.io/games"

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials

class BuildRequest(BaseModel):
    user_id: str = Field(..., description="User ID")
    game_id: str = Field(..., description="Game ID")  
    game_name: str = Field(..., description="Game name")
    game_type: str = Field(default="platformer", description="Type of game")
    asset_set: str = Field(default="v1", description="Asset set version")
    assets: list = Field(default=[], description="Game assets")
    target_platform: str = Field(default="WebGL", description="Build target platform")
    theme: str = Field(default="city", description="Game theme")

class BuildResponse(BaseModel):
    build_id: str
    status: str
    message: str

class StatusResponse(BaseModel):
    id: str
    user_id: str
    game_id: str
    game_name: str
    game_type: str
    asset_set: str
    assets: list
    target_platform: str
    status: str
    progress: int
    created_at: str
    updated_at: str
    message: str
    game_engine: str
    license_type: str
    build_method: str
    play_url: Optional[str] = None
    download_url: Optional[str] = None

godot_service: Optional[GodotBuildService] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global godot_service
    
    print("🚀 Starting Godot MCP Production Service...")
    
    if not os.path.exists(GODOT_PATH):
        print(f"❌ Godot not found at {GODOT_PATH}")
        sys.exit(1)
    
    godot_service = GodotBuildService(
        base_build_dir=BUILD_BASE_DIR,
        base_game_url=GAME_BASE_URL,
        godot_path=GODOT_PATH
    )
    
    if godot_service:
        await godot_service.start()
    print("✅ Godot Build Service initialized")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('/tmp/godot-mcp-production.log'),
            logging.StreamHandler()
        ]
    )
    
    print("🎮 Godot MCP Production Service ready!")
    
    yield
    
    print("🛑 Shutting down Godot MCP Service...")
    if godot_service:
        await godot_service.stop()
    print("✅ Service shutdown complete")

app = FastAPI(
    title="Godot MCP Build Service - Production",
    description="Production game build service with Godot 4.3 integration",
    version="4.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    """Health check endpoint"""
    system_stats = {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
        "active_builds": 0,
        "total_builds": 0,
        "game_engine": "Godot 4.3",
        "license_type": "MIT"
    }
    
    if godot_service:
        stats = godot_service.get_build_statistics()
        system_stats.update({
            "active_builds": stats["running_builds"],
            "total_builds": stats["total_builds"]
        })
    
    return {
        "status": "healthy",
        "service": "Godot MCP Build Service",
        "version": "4.0.0",
        "timestamp": datetime.now().isoformat(),
        "system": system_stats
    }

@app.get("/status")
async def status(token: str = Depends(verify_token)):
    """Get service status and statistics"""
    if not godot_service:
        raise HTTPException(status_code=503, detail="Build service not initialized")
    
    stats = godot_service.get_build_statistics()
    
    return {
        "service": "Godot MCP Build Service - Production",
        "version": "4.0.0",
        "game_engine": "Godot 4.3",
        "license_type": "MIT",
        "build_statistics": stats,
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage('/').percent,
            "uptime": "N/A"
        }
    }

@app.get("/metrics")
async def metrics():
    """Prometheus-style metrics endpoint"""
    if not godot_service:
        return {"error": "Build service not initialized"}
    
    stats = godot_service.get_build_statistics()
    
    metrics_text = f"""# HELP godot_builds_total Total number of builds
# TYPE godot_builds_total counter
godot_builds_total {stats['total_builds']}

# HELP godot_builds_completed_total Total number of completed builds  
# TYPE godot_builds_completed_total counter
godot_builds_completed_total {stats['completed_builds']}

# HELP godot_builds_failed_total Total number of failed builds
# TYPE godot_builds_failed_total counter
godot_builds_failed_total {stats['failed_builds']}

# HELP godot_builds_running Current number of running builds
# TYPE godot_builds_running gauge
godot_builds_running {stats['running_builds']}

# HELP godot_build_success_rate Build success rate percentage
# TYPE godot_build_success_rate gauge
godot_build_success_rate {stats['success_rate']}

# HELP system_cpu_percent CPU usage percentage
# TYPE system_cpu_percent gauge
system_cpu_percent {psutil.cpu_percent()}

# HELP system_memory_percent Memory usage percentage
# TYPE system_memory_percent gauge
system_memory_percent {psutil.virtual_memory().percent}
"""
    
    return JSONResponse(content={"metrics": metrics_text})

@app.post("/build", response_model=BuildResponse)
async def create_build(
    request: BuildRequest,
    token: str = Depends(verify_token)
):
    """Create a new Godot build"""
    if not godot_service:
        raise HTTPException(status_code=503, detail="Build service not initialized")
    
    try:
        logging.info(f"Build request: {request.game_name} ({request.game_type})")
        
        godot_request = GodotBuildRequest(
            user_id=request.user_id,
            game_id=request.game_id,
            game_name=request.game_name,
            game_type=request.game_type,
            asset_set=request.asset_set,
            assets=request.assets,
            target_platform=request.target_platform,
            theme=request.theme
        )
        
        result = await godot_service.create_build(godot_request)
        
        return BuildResponse(
            build_id=result["build_id"],
            status=result["status"],
            message=result["message"]
        )
        
    except Exception as e:
        logging.error(f"Build creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Build creation failed: {str(e)}")

@app.get("/build/{build_id}/status", response_model=StatusResponse)
async def get_build_status(
    build_id: str,
    token: str = Depends(verify_token)
):
    """Get build status"""
    if not godot_service:
        raise HTTPException(status_code=503, detail="Build service not initialized")
    
    status = await godot_service.get_build_status(build_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Build not found")
    
    return StatusResponse(**status)

@app.put("/build/{build_id}/stop")
async def stop_build(
    build_id: str,
    token: str = Depends(verify_token)
):
    """Stop a running build"""
    if not godot_service:
        raise HTTPException(status_code=503, detail="Build service not initialized")
    
    success = await godot_service.stop_build(build_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Build not found or cannot be stopped")
    
    return {"message": "Build stopped successfully"}

@app.post("/maintenance/cleanup")
async def cleanup_builds(
    max_age_hours: int = 24,
    token: str = Depends(verify_token)
):
    """Clean up old builds"""
    if not godot_service:
        raise HTTPException(status_code=503, detail="Build service not initialized")
    
    result = await godot_service.cleanup_old_builds(max_age_hours)
    return result

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Godot MCP Build Service - Production",
        "version": "4.0.0", 
        "status": "operational",
        "game_engine": "Godot 4.3",
        "license_type": "MIT",
        "documentation": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🎮 Godot MCP Production Service")
    print("=" * 50)
    print(f"Godot Path: {GODOT_PATH}")
    print(f"Build Directory: {BUILD_BASE_DIR}")
    print(f"Game URL: {GAME_BASE_URL}")
    print("=" * 50)
    
    if not os.path.exists(GODOT_PATH):
        print(f"❌ Godot not found at {GODOT_PATH}")
        print("Please ensure Godot 4.3 is installed")
        sys.exit(1)
    
    Path(BUILD_BASE_DIR).mkdir(parents=True, exist_ok=True)
    Path("/var/www/html/games").mkdir(parents=True, exist_ok=True)
    
    print("✅ Starting production server...")
    
    uvicorn.run(
        "production_godot_service:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        access_log=True,
        log_level="info"
    )
