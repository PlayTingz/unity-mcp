#!/usr/bin/env python3
"""
Unity Build Service - Production Implementation
Handles real Unity project creation and WebGL builds with no mocks or placeholders.
"""

import os
import json
import shutil
import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
import uuid

from unity_project_generator import UnityProjectGenerator, GameSpec, SceneSpec, GameObjectSpec
from asset_manager import AssetManager

@dataclass
class BuildRequest:
    """Build request from API"""
    user_id: str
    game_id: str
    game_name: str
    game_type: str = "platformer"
    asset_set: str = "v1" 
    assets: Optional[List[List[str]]] = None
    target_platform: str = "WebGL"
    theme: str = "city"

@dataclass 
class BuildJob:
    """Internal build job representation"""
    build_id: str
    user_id: str
    game_id: str
    game_name: str
    game_type: str
    asset_set: str
    assets: List[List[str]]
    target_platform: str
    theme: str = "city"
    status: str = "queued"
    progress: int = 0
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    build_log: List[str] = field(default_factory=list)
    error: Optional[str] = None
    project_dir: Optional[str] = None
    build_output_dir: Optional[str] = None
    scene_name: Optional[str] = None
    play_url: Optional[str] = None
    download_url: Optional[str] = None

class UnityBuildService:
    """Production Unity build service with real Unity integration"""
    
    def __init__(self, base_build_dir: str = "/opt/unity-mcp/builds", 
                 base_game_url: str = "http://35.226.93.88/games",
                 unity_path: str = "/opt/unity/Unity"):
        self.base_build_dir = Path(base_build_dir)
        self.base_build_dir.mkdir(parents=True, exist_ok=True)
        
        self.base_game_url = base_game_url
        self.unity_path = unity_path
        
        # Active build jobs
        self.builds: Dict[str, BuildJob] = {}
        self.build_queue = asyncio.Queue()
        
        # Initialize Unity project generator
        self.unity_generator = UnityProjectGenerator(unity_path)
        
        # Initialize asset manager
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent))
            from asset_manager import AssetManager
            self.asset_manager = AssetManager(logging.getLogger("asset_manager"))
        except Exception as e:
            self.logger.warning(f"Asset manager not available: {e}")
            self.asset_manager = None
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # Start build processor
        self._build_processor_task = None
        
    async def start(self):
        """Start the build service"""
        if self._build_processor_task is None:
            self._build_processor_task = asyncio.create_task(self._process_build_queue())
            self.logger.info("Unity Build Service started")
    
    async def stop(self):
        """Stop the build service"""
        if self._build_processor_task:
            self._build_processor_task.cancel()
            try:
                await self._build_processor_task
            except asyncio.CancelledError:
                pass
            self._build_processor_task = None
            self.logger.info("Unity Build Service stopped")
    
    async def create_build(self, request: BuildRequest) -> Dict[str, Any]:
        """Create a new build job"""
        build_id = str(uuid.uuid4())
        
        build_job = BuildJob(
            build_id=build_id,
            user_id=request.user_id,
            game_id=request.game_id,
            game_name=request.game_name,
            game_type=request.game_type,
            asset_set=request.asset_set,
            assets=request.assets or [],
            target_platform=request.target_platform,
            theme=request.theme,
            created_at=datetime.now()
        )
        
        self.builds[build_id] = build_job
        await self.build_queue.put(build_id)
        
        self.logger.info(f"Created build job {build_id} for {request.game_name}")
        
        return {
            "build_id": build_id,
            "status": "queued",
            "message": "Unity Pro build submitted successfully"
        }
    
    async def get_build_status(self, build_id: str) -> Optional[Dict[str, Any]]:
        """Get build status"""
        if build_id not in self.builds:
            return None
            
        job = self.builds[build_id]
        
        status = {
            "id": build_id,
            "user_id": job.user_id,
            "game_id": job.game_id,
            "game_name": job.game_name,
            "game_type": job.game_type,
            "asset_set": job.asset_set,
            "assets": job.assets,
            "target_platform": job.target_platform,
            "status": job.status,
            "progress": job.progress,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": (job.completed_at or job.started_at or job.created_at).isoformat() if job.created_at else None,
            "unity_version": "2022.3.45f1",
            "license_type": "Unity Pro",
            "build_method": "Unity Pro Headless"
        }
        
        if job.status == "completed":
            status["message"] = "Unity Pro build completed successfully"
            status["play_url"] = job.play_url
            status["download_url"] = job.download_url
        elif job.status == "failed":
            status["message"] = f"Build failed: {job.error}"
        elif job.status == "running":
            status["message"] = "Unity build in progress"
            if job.build_log:
                status["current_step"] = job.build_log[-1]
        else:
            status["message"] = "Build queued for processing"
            
        return status
    
    async def stop_build(self, build_id: str) -> bool:
        """Stop a running build"""
        if build_id not in self.builds:
            return False
            
        job = self.builds[build_id]
        if job.status in ["queued", "running"]:
            job.status = "cancelled"
            job.error = "Build cancelled by user"
            job.completed_at = datetime.now()
            self.logger.info(f"Build {build_id} cancelled")
            return True
            
        return False
    
    async def _process_build_queue(self):
        """Process builds from the queue"""
        while True:
            try:
                build_id = await self.build_queue.get()
                if build_id in self.builds:
                    await self._execute_build(build_id)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error processing build queue: {e}")
    
    async def _execute_build(self, build_id: str):
        """Execute a Unity build"""
        job = self.builds[build_id]
        
        try:
            job.status = "running"
            job.started_at = datetime.now()
            job.progress = 10
            
            self.logger.info(f"Starting Unity build for {build_id}")
            job.build_log.append("Initializing Unity build...")
            
            # Create temporary build directory
            build_workspace = self.base_build_dir / build_id
            build_workspace.mkdir(exist_ok=True)
            
            job.project_dir = str(build_workspace / "UnityProject")
            job.build_output_dir = str(build_workspace / "WebGLBuild")
            
            # Step 1: Generate game specification from request
            job.progress = 20
            job.build_log.append("Generating game specification...")
            game_spec = self._create_game_specification(job)
            
            # Step 2: Download user assets if provided
            if job.assets and self.asset_manager:
                job.progress = 25
                job.build_log.append(f"Downloading {sum(len(slot) for slot in job.assets)} user assets...")
                try:
                    downloaded_assets = await asyncio.get_event_loop().run_in_executor(
                        None, self.asset_manager.download_all_assets, job.assets, build_workspace
                    )
                    job.build_log.append(f"Downloaded {sum(len(assets) for assets in downloaded_assets.values())} assets")
                except Exception as e:
                    self.logger.warning(f"Failed to download some assets: {e}")
                    job.build_log.append(f"Warning: Some assets failed to download: {e}")
            
            # Step 3: Create Unity project (theme package imported automatically if theme specified)
            job.progress = 30
            job.build_log.append("Creating Unity project with theme support...")
            project_path, scene_name = await asyncio.get_event_loop().run_in_executor(
                None, self.unity_generator.create_project, game_spec, str(build_workspace)
            )
            job.project_dir = project_path
            job.scene_name = scene_name
            job.build_log.append(f"Created scene: {scene_name}")
            
            # Step 4: Integrate user assets into Unity project
            if job.assets and self.asset_manager and 'downloaded_assets' in locals():
                job.build_log.append("Integrating user assets into Unity project...")
                try:
                    project_path = Path(job.project_dir) if job.project_dir else Path(build_workspace) / "UnityProject"
                    asset_manifest = await asyncio.get_event_loop().run_in_executor(
                        None, self.asset_manager.organize_assets_for_unity, downloaded_assets, project_path
                    )
                    await asyncio.get_event_loop().run_in_executor(
                        None, self.asset_manager.create_asset_loader_script, project_path, asset_manifest
                    )
                    job.build_log.append(f"Integrated {len(asset_manifest.get('by_type', {}).get('images', []))} images, "
                                       f"{len(asset_manifest.get('by_type', {}).get('models', []))} 3D models")
                except Exception as e:
                    self.logger.warning(f"Failed to integrate assets: {e}")
                    job.build_log.append(f"Warning: Asset integration failed: {e}")
            
            job.progress = 40
            
            # Step 3: Build WebGL with live progress tracking
            job.progress = 50
            job.build_log.append("Building WebGL with Unity Pro...")
            if not job.project_dir or not job.build_output_dir:
                raise Exception("Project directories not initialized")
            
            # Start progress monitor in background
            import threading
            import time
            import re
            
            stop_monitor = threading.Event()
            
            def monitor_unity_log():
                """Monitor Unity log file for IL2CPP compilation progress"""
                import glob
                time.sleep(5)  # Wait for log file to be created
                
                while not stop_monitor.is_set():
                    try:
                        # Find most recent unity log
                        log_files = glob.glob("/tmp/unity_build_*.log")
                        if log_files:
                            latest_log = max(log_files, key=lambda x: Path(x).stat().st_mtime)
                            with open(latest_log, 'r') as f:
                                content = f.read()
                                
                            # Look for IL2CPP progress: [123/456 ...]
                            matches = re.findall(r'\[(\d+)/(\d+)\s+', content)
                            if matches:
                                current, total = matches[-1]
                                current, total = int(current), int(total)
                                # Map IL2CPP progress (0-100%) to build progress (50-75%)
                                il2cpp_percent = (current / total) * 100
                                job.progress = 50 + int((il2cpp_percent / 100) * 25)
                    except Exception as e:
                        pass
                    
                    time.sleep(10)  # Check every 10 seconds
            
            monitor_thread = threading.Thread(target=monitor_unity_log, daemon=True)
            monitor_thread.start()
            
            try:
                build_success = await asyncio.get_event_loop().run_in_executor(
                    None, self.unity_generator.build_webgl, job.project_dir, job.build_output_dir
                )
            finally:
                stop_monitor.set()
                monitor_thread.join(timeout=1)
            
            if not build_success:
                raise Exception("Unity WebGL build failed")
            
            # Step 4: Deploy to web directory
            job.progress = 80
            job.build_log.append("Deploying game...")
            await self._deploy_build(job)
            
            # Step 5: Complete
            job.progress = 100
            job.status = "completed"
            job.completed_at = datetime.now()
            job.build_log.append("Build completed successfully!")
            
            self.logger.info(f"Build {build_id} completed successfully")
            
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = datetime.now()
            job.build_log.append(f"Build failed: {e}")
            self.logger.error(f"Build {build_id} failed: {e}")
    
    def _create_game_specification(self, job: BuildJob) -> GameSpec:
        """Create Unity game specification from build job"""
        
        # Create scene objects based on game type
        scene_objects = []
        
        if job.game_type == "platformer":
            # Create a simple platformer scene
            scene_objects = [
                GameObjectSpec(
                    name="Player",
                    type="Cube",
                    position={"x": 0, "y": 1, "z": 0},
                    rotation={"x": 0, "y": 45, "z": 0},
                    scale={"x": 1, "y": 1, "z": 1},
                    material_color={"r": 1.0, "g": 0.3, "b": 0.3, "a": 1.0}
                ),
                GameObjectSpec(
                    name="Ground",
                    type="Cube", 
                    position={"x": 0, "y": -0.5, "z": 0},
                    rotation={"x": 0, "y": 0, "z": 0},
                    scale={"x": 10, "y": 1, "z": 10},
                    material_color={"r": 0.3, "g": 0.8, "b": 0.3, "a": 1.0}
                ),
                GameObjectSpec(
                    name="BlueSphere",
                    type="Sphere", 
                    position={"x": 2, "y": 1.5, "z": 0},
                    rotation={"x": 0, "y": 0, "z": 0},
                    scale={"x": 1, "y": 1, "z": 1},
                    material_color={"r": 0.2, "g": 0.5, "b": 1.0, "a": 1.0}
                )
            ]
        else:
            # Default: simple cube game
            scene_objects = [
                GameObjectSpec(
                    name="GameCube",
                    type="Cube",
                    position={"x": 0, "y": 0, "z": 0},
                    rotation={"x": 0, "y": 45, "z": 0},
                    scale={"x": 1, "y": 1, "z": 1},
                    material_color={"r": 0.2, "g": 0.8, "b": 1.0, "a": 1.0}
                )
            ]
        
        scene = SceneSpec(
            name="GameScene",
            objects=scene_objects,
            camera_position={"x": 0, "y": 2, "z": -5},
            camera_rotation={"x": 10, "y": 0, "z": 0},
            lighting="Default",
            skybox="Default"
        )
        
        game_spec = GameSpec(
            name=job.game_name,
            company_name="Unity MCP Games",
            version="1.0.0",
            scene=scene,
            theme=job.theme
        )
        
        return game_spec
    
    async def _deploy_build(self, job: BuildJob):
        """Deploy the built game to web-accessible location"""
        if not job.build_output_dir:
            raise Exception("Build output directory not set")
        build_output = Path(job.build_output_dir)
        web_dir = Path("/var/www/html/games") / job.build_id
        
        # Ensure web directory exists
        web_dir.parent.mkdir(parents=True, exist_ok=True)
        
        if build_output.exists() and any(build_output.iterdir()):
            # Copy build output to web directory
            if web_dir.exists():
                shutil.rmtree(web_dir)
            shutil.copytree(build_output, web_dir)
            
            # Set proper permissions
            os.system(f"chmod -R 755 {web_dir}")
            
            # Generate URLs
            job.play_url = f"{self.base_game_url}/{job.build_id}/"
            job.download_url = f"{self.base_game_url}/{job.build_id}/build.zip"
            
            self.logger.info(f"Game deployed to: {job.play_url}")
            
        else:
            raise Exception("Unity build output directory is empty or missing")
    
    def get_build_statistics(self) -> Dict[str, Any]:
        """Get build service statistics"""
        total_builds = len(self.builds)
        completed_builds = sum(1 for job in self.builds.values() if job.status == "completed")
        failed_builds = sum(1 for job in self.builds.values() if job.status == "failed")
        running_builds = sum(1 for job in self.builds.values() if job.status == "running")
        
        return {
            "total_builds": total_builds,
            "completed_builds": completed_builds,
            "failed_builds": failed_builds,
            "running_builds": running_builds,
            "success_rate": (completed_builds / total_builds * 100) if total_builds > 0 else 0,
            "unity_version": "2022.3.45f1",
            "license_type": "Unity Pro",
            "service_status": "operational"
        }
    
    async def cleanup_old_builds(self, max_age_hours: int = 24):
        """Clean up old build directories"""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        cleaned = 0
        
        try:
            for build_path in self.base_build_dir.iterdir():
                if build_path.is_dir() and build_path.stat().st_mtime < cutoff_time:
                    shutil.rmtree(build_path)
                    cleaned += 1
                    
            self.logger.info(f"Cleaned up {cleaned} old build directories")
            return {"cleaned_builds": cleaned}
            
        except Exception as e:
            self.logger.error(f"Error cleaning up builds: {e}")
            return {"error": str(e)}