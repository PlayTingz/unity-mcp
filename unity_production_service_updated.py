#!/usr/bin/env python3
"""
Unity MCP Production Service - Updated with Package Import Support
Uses modular Unity components from /opt/unity-mcp/server/lib/
"""

import os
import sys
import json
import logging
import asyncio
import psutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add lib directory to Python path
sys.path.insert(0, '/opt/unity-mcp/server/lib')

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager

# Import Unity modules with package support
from unity_project_generator import UnityProjectGenerator
from unity_build_service import UnityBuildService, BuildRequest as UnityBuildRequest

# Configuration
API_KEY = "013e283d7f3a2d45dcdbe7a2b4676a61ff58e7a576930ac3ea66c85d3882f197"
UNITY_PATH = "/opt/unity/editors/2022.3.45f1/Editor/Unity"
BUILD_BASE_DIR = "/opt/unity-mcp/builds"
GAME_BASE_URL = "http://35.226.93.88/games"

# Security
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials

# Pydantic models
class BuildRequest(BaseModel):
    user_id: str = Field(..., description="User ID")
    game_id: str = Field(..., description="Game ID")  
    game_name: str = Field(..., description="Game name")
    game_type: str = Field(default="platformer", description="Type of game")
    asset_set: str = Field(default="v1", description="Asset set version")
    assets: list = Field(default=[], description="Game assets")
    target_platform: str = Field(default="WebGL", description="Build target platform")
    theme: str = Field(default="city", description="Game theme (city, farm, space)")

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
    unity_version: str
    license_type: str
    build_method: str
    play_url: Optional[str] = None
    download_url: Optional[str] = None

# Global build service instance
unity_service: Optional[UnityBuildService] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global unity_service
    
    # Startup
    print("🚀 Starting Unity MCP Production Service with Package Support...")
    
    # Verify Unity installation
    if not os.path.exists(UNITY_PATH):
        print(f"❌ Unity not found at {UNITY_PATH}")
        sys.exit(1)
    
    # Initialize Unity build service with new modules
    unity_service = UnityBuildService(
        base_build_dir=BUILD_BASE_DIR,
        base_game_url=GAME_BASE_URL,
        unity_path=UNITY_PATH
    )
    
    if unity_service:
        await unity_service.start()
    print("✅ Unity Build Service initialized with package import support")
    print("✅ CityThemePackage will be imported automatically")
    print("✅ com.unity.cloud.gltfast v6.8.0 included in all projects")
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('/opt/unity-mcp/logs/unity-mcp-production.log'),
            logging.StreamHandler()
        ]
    )
    
    print("🎮 Unity MCP Production Service ready!")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Unity MCP Service...")
    if unity_service:
        await unity_service.stop()
    print("✅ Service shutdown complete")

# FastAPI app
app = FastAPI(
    title="Unity MCP Build Service - Production with Package Support",
    description="Production Unity game build service with Unity package import and gltfast support",
    version="3.1.0",
    lifespan=lifespan
)

# CORS middleware
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
        "unity_licensed": True,
        "unity_version": "2022.3.45f1",
        "license_type": "Unity Pro",
        "package_support": True,
        "city_package_enabled": True,
        "gltfast_enabled": True
    }
    
    if unity_service:
        stats = unity_service.get_build_statistics()
        system_stats.update({
            "active_builds": stats["running_builds"],
            "total_builds": stats["total_builds"]
        })
    
    return {
        "status": "healthy",
        "service": "Unity MCP Build Service - Production with Package Support",
        "version": "3.1.0",
        "timestamp": datetime.now().isoformat(),
        "unity_licensed": True,
        "features": {
            "city_package_import": True,
            "gltfast_support": True,
            "webgl_builds": True
        },
        "system": system_stats
    }

@app.get("/status")
async def status(token: str = Depends(verify_token)):
    """Get service status and statistics"""
    if not unity_service:
        raise HTTPException(status_code=503, detail="Build service not initialized")
    
    stats = unity_service.get_build_statistics()
    
    return {
        "service": "Unity MCP Build Service - Production",
        "version": "3.1.0",
        "unity_version": "2022.3.45f1",
        "unity_licensed": True,
        "license_type": "Unity Pro",
        "features": {
            "city_package_import": True,
            "gltfast_version": "6.8.0",
            "package_path": "/opt/unity-mcp/packages/CityThemePackage.unitypackage"
        },
        "build_statistics": stats,
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage('/').percent,
        }
    }

@app.post("/build", response_model=BuildResponse)
async def create_build(
    request: BuildRequest,
    token: str = Depends(verify_token)
):
    """Create a new Unity build with automatic package import"""
    if not unity_service:
        raise HTTPException(status_code=503, detail="Build service not initialized")
    
    try:
        # Log build request
        logging.info(f"Build request: {request.game_name} ({request.game_type})")
        
        # Convert to internal build request
        unity_request = UnityBuildRequest(
            user_id=request.user_id,
            game_id=request.game_id,
            game_name=request.game_name,
            game_type=request.game_type,
            asset_set=request.asset_set,
            assets=request.assets,
            target_platform=request.target_platform
        )
        
        # Submit build
        result = await unity_service.create_build(unity_request)
        
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
    if not unity_service:
        raise HTTPException(status_code=503, detail="Build service not initialized")
    
    status = await unity_service.get_build_status(build_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Build not found")
    
    return StatusResponse(**status)

@app.put("/build/{build_id}/stop")
async def stop_build(
    build_id: str,
    token: str = Depends(verify_token)
):
    """Stop a running build"""
    if not unity_service:
        raise HTTPException(status_code=503, detail="Build service not initialized")
    
    success = await unity_service.stop_build(build_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Build not found or cannot be stopped")
    
    return {"message": "Build stopped successfully"}

@app.get("/themes")
async def list_themes():
    """List available themes"""
    return {
        "themes": [
            {
                "id": "city",
                "name": "City",
                "description": "Urban city theme with buildings, roads, and vehicles",
                "assets": ["buildings", "roads", "vehicles", "decorations", "obstacles"],
                "status": "available"
            }
        ]
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Unity MCP Build Service - Production",
        "version": "3.1.0", 
        "status": "operational",
        "unity_version": "2022.3.45f1",
        "license_type": "Unity Pro",
        "features": {
            "city_package_import": True,
            "gltfast_support": "6.8.0",
            "webgl_builds": True,
            "theme_support": True
        },
        "documentation": "/docs",
        "health": "/health",
        "themes": "/themes"
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🎮 Unity MCP Production Service - Package Support Edition")
    print("=" * 60)
    print(f"Unity Path: {UNITY_PATH}")
    print(f"Build Directory: {BUILD_BASE_DIR}")
    print(f"Game URL: {GAME_BASE_URL}")
    print("Features:")
    print("  ✓ CityThemePackage automatic import")
    print("  ✓ com.unity.cloud.gltfast v6.8.0")
    print("  ✓ Unity Pro 2022.3.45f1")
    print("=" * 60)
    
    # Verify Unity exists before starting
    if not os.path.exists(UNITY_PATH):
        print(f"❌ Unity not found at {UNITY_PATH}")
        print("Please ensure Unity Pro is installed and licensed")
        sys.exit(1)
    
    # Ensure directories exist
    Path(BUILD_BASE_DIR).mkdir(parents=True, exist_ok=True)
    Path("/var/www/html/games").mkdir(parents=True, exist_ok=True)
    Path("/opt/unity-mcp/logs").mkdir(parents=True, exist_ok=True)
    
    print("✅ Starting production server...")
    
    uvicorn.run(
        "unity_production_service_updated:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        access_log=True,
        log_level="info"
    )
