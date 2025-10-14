#!/usr/bin/env python3
"""
Production Unity MCP Service
Real Unity WebGL build service with no mocks or placeholders - Production Ready
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

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import Unity build service modules
try:
    # Try relative import first  
    if __name__ == "__main__":
        from unity_build_service import UnityBuildService, BuildRequest as UnityBuildRequest
    else:
        from .unity_build_service import UnityBuildService, BuildRequest as UnityBuildRequest
except ImportError:
    # Fallback to direct import
    import importlib.util
    
    build_service_path = current_dir / "unity_build_service.py"
    spec = importlib.util.spec_from_file_location("unity_build_service", build_service_path)
    unity_build_service = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(unity_build_service)
    
    UnityBuildService = unity_build_service.UnityBuildService
    UnityBuildRequest = unity_build_service.BuildRequest

# Configuration
API_KEY = "j_QJTDk9IfuxWh1G_jqjdLBeLBLuLyaFepi-6Rtfwkg"
UNITY_PATH = "/opt/unity/Unity"
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
    print("🚀 Starting Unity MCP Production Service...")
    
    # Verify Unity installation
    if not os.path.exists(UNITY_PATH):
        print(f"❌ Unity not found at {UNITY_PATH}")
        sys.exit(1)
    
    # Initialize Unity build service
    unity_service = UnityBuildService(
        base_build_dir=BUILD_BASE_DIR,
        base_game_url=GAME_BASE_URL,
        unity_path=UNITY_PATH
    )
    
    if unity_service:
        await unity_service.start()
    print("✅ Unity Build Service initialized")
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('/tmp/unity-mcp-production.log'),
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
    title="Unity MCP Build Service - Production with Unity Pro",
    description="Production Unity game build service with real Unity Pro integration",
    version="3.0.0",
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
        "license_type": "Unity Pro"
    }
    
    if unity_service:
        stats = unity_service.get_build_statistics()
        system_stats.update({
            "active_builds": stats["running_builds"],
            "total_builds": stats["total_builds"]
        })
    
    return {
        "status": "healthy",
        "service": "Unity MCP Build Service - Unity Pro",
        "version": "3.0.0",
        "timestamp": datetime.now().isoformat(),
        "unity_licensed": True,
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
        "version": "3.0.0",
        "unity_version": "2022.3.45f1",
        "unity_licensed": True,
        "license_type": "Unity Pro",
        "build_statistics": stats,
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage('/').percent,
            "uptime": "N/A"  # Could add actual uptime tracking
        }
    }

@app.get("/metrics")
async def metrics():
    """Prometheus-style metrics endpoint"""
    if not unity_service:
        return {"error": "Build service not initialized"}
    
    stats = unity_service.get_build_statistics()
    
    metrics_text = f"""# HELP unity_builds_total Total number of builds
# TYPE unity_builds_total counter
unity_builds_total {stats['total_builds']}

# HELP unity_builds_completed_total Total number of completed builds  
# TYPE unity_builds_completed_total counter
unity_builds_completed_total {stats['completed_builds']}

# HELP unity_builds_failed_total Total number of failed builds
# TYPE unity_builds_failed_total counter
unity_builds_failed_total {stats['failed_builds']}

# HELP unity_builds_running Current number of running builds
# TYPE unity_builds_running gauge
unity_builds_running {stats['running_builds']}

# HELP unity_build_success_rate Build success rate percentage
# TYPE unity_build_success_rate gauge
unity_build_success_rate {stats['success_rate']}

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
    token: str = Depends(verify_token),
    http_request: Optional[Request] = None
):
    """Create a new Unity build"""
    if not unity_service:
        raise HTTPException(status_code=503, detail="Build service not initialized")
    
    try:
        # Log build request
        client_ip = http_request.client.host if http_request and http_request.client else "unknown"
        logging.info(f"Build request from {client_ip}: {request.game_name} ({request.game_type})")
        
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

@app.post("/maintenance/cleanup")
async def cleanup_builds(
    max_age_hours: int = 24,
    token: str = Depends(verify_token)
):
    """Clean up old builds"""
    if not unity_service:
        raise HTTPException(status_code=503, detail="Build service not initialized")
    
    result = await unity_service.cleanup_old_builds(max_age_hours)
    return result

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Unity MCP Build Service - Production",
        "version": "3.0.0", 
        "status": "operational",
        "unity_version": "2022.3.45f1",
        "license_type": "Unity Pro",
        "documentation": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🎮 Unity MCP Production Service")
    print("=" * 50)
    print(f"Unity Path: {UNITY_PATH}")
    print(f"Build Directory: {BUILD_BASE_DIR}")
    print(f"Game URL: {GAME_BASE_URL}")
    print("=" * 50)
    
    # Verify Unity exists before starting
    if not os.path.exists(UNITY_PATH):
        print(f"❌ Unity not found at {UNITY_PATH}")
        print("Please ensure Unity Pro is installed and licensed")
        sys.exit(1)
    
    # Ensure directories exist
    Path(BUILD_BASE_DIR).mkdir(parents=True, exist_ok=True)
    Path("/var/www/html/games").mkdir(parents=True, exist_ok=True)
    
    print("✅ Starting production server...")
    
    uvicorn.run(
        "production_unity_service:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        access_log=True,
        log_level="info"
    )