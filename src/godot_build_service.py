#!/usr/bin/env python3
"""
Godot Build Service - Production Implementation
Handles real Godot project creation and WebGL builds.
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

from godot_project_generator import GodotProjectGenerator, GameSpec, SceneSpec, GameObjectSpec
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

class GodotBuildService:
    """Production Godot build service with real Godot integration"""
    
    def __init__(self, base_build_dir: str = "/opt/unity-mcp/builds", 
                 base_game_url: str = "https://35-226-93-88.nip.io/games",
                 godot_path: str = "/usr/local/bin/godot"):
        self.base_build_dir = Path(base_build_dir)
        self.base_build_dir.mkdir(parents=True, exist_ok=True)
        
        self.base_game_url = base_game_url
        self.godot_path = godot_path
        
        self.builds: Dict[str, BuildJob] = {}
        self.build_queue = asyncio.Queue()
        
        self.godot_generator = GodotProjectGenerator(godot_path)
        
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent))
            from asset_manager import AssetManager
            self.asset_manager = AssetManager(logging.getLogger("asset_manager"))
        except Exception as e:
            self.logger.warning(f"Asset manager not available: {e}")
            self.asset_manager = None
        
        self.logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        self._build_processor_task = None
        
    async def start(self):
        """Start the build service"""
        if self._build_processor_task is None:
            self._build_processor_task = asyncio.create_task(self._process_build_queue())
            self.logger.info("Godot Build Service started")
    
    async def stop(self):
        """Stop the build service"""
        if self._build_processor_task:
            self._build_processor_task.cancel()
            try:
                await self._build_processor_task
            except asyncio.CancelledError:
                pass
            self._build_processor_task = None
            self.logger.info("Godot Build Service stopped")
    
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
            "message": "Godot build submitted successfully"
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
            "game_engine": "Godot 4.3",
            "license_type": "MIT",
            "build_method": "Godot Headless"
        }
        
        if job.status == "completed":
            status["message"] = "Godot build completed successfully"
            status["play_url"] = job.play_url
            status["download_url"] = job.download_url
        elif job.status == "failed":
            status["message"] = f"Build failed: {job.error}"
        elif job.status == "running":
            status["message"] = "Godot build in progress"
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
        """Execute a Godot build"""
        job = self.builds[build_id]
        
        try:
            job.status = "running"
            job.started_at = datetime.now()
            job.progress = 10
            
            self.logger.info(f"Starting Godot build for {build_id}")
            job.build_log.append("Initializing Godot build...")
            
            build_workspace = self.base_build_dir / build_id
            build_workspace.mkdir(exist_ok=True)
            
            job.project_dir = str(build_workspace / "GodotProject")
            job.build_output_dir = str(build_workspace / "WebGLBuild")
            
            job.progress = 20
            job.build_log.append("Generating game specification...")
            game_spec = self._create_game_specification(job)
            
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
            
            job.progress = 30
            job.build_log.append("Creating Godot project...")
            project_path, scene_name = await asyncio.get_event_loop().run_in_executor(
                None, self.godot_generator.create_project, game_spec, str(build_workspace)
            )
            job.project_dir = project_path
            job.scene_name = scene_name
            job.build_log.append(f"Created scene: {scene_name}")
            
            if job.assets and self.asset_manager and 'downloaded_assets' in locals():
                job.build_log.append("Integrating user assets into Godot project...")
                try:
                    project_path_obj = Path(job.project_dir) if job.project_dir else Path(build_workspace) / "GodotProject"
                    asset_manifest = await asyncio.get_event_loop().run_in_executor(
                        None, self._organize_assets_for_godot, downloaded_assets, project_path_obj
                    )
                    job.build_log.append(f"Integrated {len(asset_manifest.get('by_type', {}).get('images', []))} images, "
                                       f"{len(asset_manifest.get('by_type', {}).get('models', []))} 3D models")
                except Exception as e:
                    self.logger.warning(f"Failed to integrate assets: {e}")
                    job.build_log.append(f"Warning: Asset integration failed: {e}")
            
            job.progress = 40
            
            job.progress = 50
            job.build_log.append("Building WebGL with Godot...")
            if not job.project_dir or not job.build_output_dir:
                raise Exception("Project directories not initialized")
            
            build_success = await asyncio.get_event_loop().run_in_executor(
                None, self.godot_generator.build_webgl, job.project_dir, job.build_output_dir
            )
            
            if not build_success:
                raise Exception("Godot WebGL build failed")
            
            job.progress = 80
            job.build_log.append("Deploying game...")
            await self._deploy_build(job)
            
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
        """Create Godot game specification from build job"""
        
        scene_objects = []
        game_type = job.game_type if job.game_type else "cube"
        
        # For platformer/runner games, we'll create a special scene structure
        # For other types, use simple objects
        if game_type == "platformer":
            # Mark this as a runner game - special scene will be created
            scene = SceneSpec(
                name="RunnerGame",
                objects=[],  # Will be handled specially
                camera_position={"x": 0, "y": 5, "z": -15},
                camera_rotation={"x": -20, "y": 0, "z": 0},
                lighting="Default",
                skybox="Default"
            )
        else:
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
                camera_position={"x": 0, "y": 5, "z": -15},
                camera_rotation={"x": 10, "y": 0, "z": 0},
                lighting="Default",
                skybox="Default"
            )
        
        game_spec = GameSpec(
            name=job.game_name,
            company_name="Godot MCP Games",
            version="1.0.0",
            scene=scene,
            theme=job.theme
        )
        
        return game_spec
    
    def _organize_assets_for_godot(self, downloaded_assets: Dict[int, List[Any]], 
                                  project_dir: Path) -> Dict[str, Any]:
        """Organize downloaded assets into Godot project structure"""
        godot_assets_dir = project_dir / "assets" / "user_content"
        godot_assets_dir.mkdir(parents=True, exist_ok=True)
        
        asset_manifest = {
            "slots": {},
            "by_type": {
                "images": [],
                "models": [],
                "audio": [],
                "video": []
            }
        }
        
        for slot_idx, assets in downloaded_assets.items():
            slot_dir = godot_assets_dir / f"slot{slot_idx}"
            slot_dir.mkdir(parents=True, exist_ok=True)
            
            slot_assets = []
            
            for asset in assets:
                src_path = Path(asset.local_path)
                dest_path = slot_dir / src_path.name
                
                if src_path.exists():
                    shutil.copy2(src_path, dest_path)
                    
                    relative_path = dest_path.relative_to(project_dir)
                    
                    asset_info = {
                        "path": str(relative_path),
                        "type": asset.asset_type.value,
                        "mime_type": asset.mime_type,
                        "size": asset.file_size,
                        "original_url": asset.url
                    }
                    
                    slot_assets.append(asset_info)
                    
                    asset_type_name = asset.asset_type.value
                    if asset_type_name == "image":
                        asset_manifest["by_type"]["images"].append(asset_info)
                    elif asset_type_name == "3d_model":
                        asset_manifest["by_type"]["models"].append(asset_info)
                    elif asset_type_name == "audio":
                        asset_manifest["by_type"]["audio"].append(asset_info)
                    elif asset_type_name == "video":
                        asset_manifest["by_type"]["videos"].append(asset_info)
            
            asset_manifest["slots"][slot_idx] = slot_assets
        
        manifest_path = godot_assets_dir / "asset_manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(asset_manifest, f, indent=2)
        
        self.logger.info(f"Organized assets into Godot project: {godot_assets_dir}")
        return asset_manifest
    
    async def _deploy_build(self, job: BuildJob):
        """Deploy the built game to web-accessible location"""
        if not job.build_output_dir:
            raise Exception("Build output directory not set")
        build_output = Path(job.build_output_dir)
        web_dir = Path("/var/www/html/games") / job.build_id
        
        web_dir.parent.mkdir(parents=True, exist_ok=True)
        
        if build_output.exists() and any(build_output.iterdir()):
            if web_dir.exists():
                shutil.rmtree(web_dir)
            shutil.copytree(build_output, web_dir)
            
            os.system(f"chmod -R 755 {web_dir}")
            
            job.play_url = f"{self.base_game_url}/{job.build_id}/index.html"
            job.download_url = f"{self.base_game_url}/{job.build_id}/build.zip"
            
            self.logger.info(f"Game deployed to: {job.play_url}")
            
        else:
            raise Exception("Godot build output directory is empty or missing")
    
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
            "game_engine": "Godot 4.3",
            "license_type": "MIT",
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
