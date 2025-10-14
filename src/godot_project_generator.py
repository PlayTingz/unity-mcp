#!/usr/bin/env python3
"""
Godot Project Generator - Production Implementation
Creates real Godot projects with game content and builds WebGL games.
"""

import os
import json
import shutil
import subprocess
import tempfile
import uuid
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class GameObjectSpec:
    """Specification for a game object to create"""
    name: str
    type: str
    position: Optional[Dict[str, float]] = None
    rotation: Optional[Dict[str, float]] = None
    scale: Optional[Dict[str, float]] = None
    material_color: Optional[Dict[str, float]] = None
    components: Optional[List[str]] = None

@dataclass
class SceneSpec:
    """Specification for a Godot scene"""
    name: str = "GameScene"
    objects: Optional[List[GameObjectSpec]] = None
    camera_position: Optional[Dict[str, float]] = None
    camera_rotation: Optional[Dict[str, float]] = None
    lighting: str = "Default"
    skybox: str = "Default"

@dataclass
class GameSpec:
    """Complete game specification"""
    name: str
    company_name: str = "Generated Games"
    version: str = "1.0.0"
    scene: Optional[SceneSpec] = None
    scripts: Optional[List[str]] = None
    theme: str = "city"

class GodotProjectGenerator:
    """Production Godot project generator with real Godot integration"""
    
    def __init__(self, godot_path: str = "/usr/local/bin/godot"):
        self.godot_path = godot_path
        self.logger = logging.getLogger(__name__)
        
        if not os.path.exists(godot_path):
            raise FileNotFoundError(f"Godot not found at {godot_path}")
    
    def create_project(self, game_spec: GameSpec, output_dir: str, import_theme_package: bool = True) -> tuple[str, str]:
        """
        Create a new Godot project and scene for this game
        Returns tuple of (project_path, scene_name)
        """
        project_dir = Path(output_dir) / "GodotProject"
        project_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Creating Godot project at: {project_dir}")
        
        scene_name = game_spec.scene.name if game_spec.scene and game_spec.scene.name else "GameScene"
        
        self._create_project_structure(project_dir, game_spec)
        
        self._copy_game_scripts(project_dir)
        
        if import_theme_package and game_spec.theme:
            self._copy_theme_assets(project_dir, game_spec.theme)
        
        scene_spec = game_spec.scene or SceneSpec(name=scene_name)
        if scene_spec.name == "RunnerGame":
            self._create_runner_game_scene(project_dir, scene_spec, game_spec.theme)
        else:
            self._create_game_scene(project_dir, scene_spec, game_spec.theme)
        
        if game_spec.scripts:
            self._create_game_scripts(project_dir, game_spec.scripts)
        
        self.logger.info(f"Created Godot scene {scene_name} in project")
        return (str(project_dir), scene_name)
    
    def build_webgl(self, project_dir: str, build_output_dir: str, development_build: bool = False) -> bool:
        """
        Build the Godot project to WebGL
        Returns True if build succeeds
        """
        self.logger.info(f"Building WebGL from {project_dir} to {build_output_dir}")
        
        build_path = Path(build_output_dir)
        build_path.mkdir(parents=True, exist_ok=True)
        
        export_preset_path = Path(project_dir) / "export_presets.cfg"
        if not export_preset_path.exists():
            self._create_export_preset(Path(project_dir))
        
        output_file = build_path / "index.html"
        
        godot_cmd = [
            self.godot_path,
            "--headless",
            "--path", project_dir,
            "--export-release", "Web",
            str(output_file)
        ]
        
        try:
            self.logger.info(f"Executing Godot build: {' '.join(godot_cmd)}")
            
            result = subprocess.run(
                godot_cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            self.logger.info(f"Godot build completed with exit code: {result.returncode}")
            
            if result.returncode == 0:
                expected_files = ['index.html', 'index.wasm', 'index.js']
                missing_files = []
                
                for expected_file in expected_files:
                    file_path = build_path / expected_file
                    if not file_path.exists():
                        missing_files.append(expected_file)
                
                if missing_files:
                    self.logger.error(f"WebGL build incomplete - missing files: {missing_files}")
                    return False
                
                self.logger.info("WebGL build completed successfully")
                return True
            else:
                self.logger.error(f"Godot build failed with exit code: {result.returncode}")
                self.logger.error(f"stdout: {result.stdout}")
                self.logger.error(f"stderr: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Godot build timed out")
            return False
        except Exception as e:
            self.logger.error(f"Godot build error: {e}")
            return False
    
    def _create_project_structure(self, project_dir: Path, game_spec: GameSpec):
        """Create basic Godot project directory structure"""
        directories = [
            "scenes",
            "scripts",
            "assets",
            "assets/materials",
            "assets/models",
            "assets/textures"
        ]
        
        for directory in directories:
            (project_dir / directory).mkdir(parents=True, exist_ok=True)
        
        project_file = project_dir / "project.godot"
        project_content = f'''[application]

config/name="{game_spec.name}"
config/version="{game_spec.version}"
run/main_scene="res://scenes/{game_spec.scene.name if game_spec.scene else 'GameScene'}.tscn"

[display]

window/size/viewport_width=1920
window/size/viewport_height=1080
window/size/mode=2
window/stretch/mode="canvas_items"

[input]

move_left={{
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":65,"key_label":0,"unicode":97,"location":0,"echo":false,"script":null)
, Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":4194319,"key_label":0,"unicode":0,"location":0,"echo":false,"script":null)
]
}}
move_right={{
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":68,"key_label":0,"unicode":100,"location":0,"echo":false,"script":null)
, Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":4194321,"key_label":0,"unicode":0,"location":0,"echo":false,"script":null)
]
}}
jump={{
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":32,"key_label":0,"unicode":32,"location":0,"echo":false,"script":null)
, Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":87,"key_label":0,"unicode":119,"location":0,"echo":false,"script":null)
, Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":4194320,"key_label":0,"unicode":0,"location":0,"echo":false,"script":null)
]
}}

[rendering]

renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"
textures/vram_compression/import_etc2_astc=true
environment/defaults/default_clear_color=Color(0.2, 0.3, 0.5, 1)
'''
        project_file.write_text(project_content)
        
        self.logger.info(f"Created Godot project file: {project_file}")
    
    def _create_export_preset(self, project_dir: Path):
        """Create export_presets.cfg for WebGL export"""
        export_preset_content = '''[preset.0]

name="Web"
platform="Web"
runnable=true
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path="build/index.html"
encryption_include_filters=""
encryption_exclude_filters=""
encrypt_pck=false
encrypt_directory=false

[preset.0.options]

custom_template/debug=""
custom_template/release=""
variant/extensions_support=false
vram_texture_compression/for_desktop=true
vram_texture_compression/for_mobile=false
html/export_icon=true
html/custom_html_shell=""
html/head_include=""
html/canvas_resize_policy=2
html/focus_canvas_on_start=true
html/experimental_virtual_keyboard=false
progressive_web_app/enabled=false
progressive_web_app/offline_page=""
progressive_web_app/display=1
progressive_web_app/orientation=0
progressive_web_app/icon_144x144=""
progressive_web_app/icon_180x180=""
progressive_web_app/icon_512x512=""
progressive_web_app/background_color=Color(0, 0, 0, 1)
'''
        export_preset_file = project_dir / "export_presets.cfg"
        export_preset_file.write_text(export_preset_content)
        self.logger.info(f"Created export preset: {export_preset_file}")
    
    def _create_game_scene(self, project_dir: Path, scene_spec: SceneSpec, theme_name: str = "city"):
        """Create Godot scene with specified game objects"""
        scenes_dir = project_dir / "scenes"
        scenes_dir.mkdir(parents=True, exist_ok=True)
        
        objects = scene_spec.objects or []
        
        camera_pos = scene_spec.camera_position or {"x": 0, "y": 1, "z": -10}
        camera_rot = scene_spec.camera_rotation or {"x": 0, "y": 0, "z": 0}
        
        scene_nodes = []
        
        load_steps = 1 + (len(objects) * 2)
        scene_nodes.append(f'[gd_scene load_steps={load_steps} format=3]\n')
        
        scene_nodes.append('[sub_resource type="Environment" id="Environment_1"]')
        scene_nodes.append('background_mode = 1')
        scene_nodes.append('background_color = Color(0.2, 0.3, 0.5, 1)')
        scene_nodes.append('ambient_light_color = Color(1, 1, 1, 1)')
        scene_nodes.append('ambient_light_energy = 1.0\n')
        
        for idx, obj in enumerate(objects):
            color = obj.material_color or {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0}
            material_name = f"{obj.name}_Material"
            mesh_name = f"{obj.name}_Mesh"
            mesh_type = self._get_godot_mesh_resource(obj.type)
            
            scene_nodes.append(f'[sub_resource type="{mesh_type}" id="{mesh_name}"]')
            if mesh_type == "BoxMesh":
                scene_nodes.append('size = Vector3(1, 1, 1)')
            elif mesh_type == "SphereMesh":
                scene_nodes.append('radius = 0.5')
                scene_nodes.append('height = 1.0')
            elif mesh_type == "CylinderMesh":
                scene_nodes.append('top_radius = 0.5')
                scene_nodes.append('bottom_radius = 0.5')
                scene_nodes.append('height = 2.0')
            elif mesh_type == "PlaneMesh":
                scene_nodes.append('size = Vector2(10, 10)')
            scene_nodes.append('')
            
            scene_nodes.append(f'[sub_resource type="StandardMaterial3D" id="{material_name}"]')
            scene_nodes.append(f'albedo_color = Color({color["r"]}, {color["g"]}, {color["b"]}, {color["a"]})')
            scene_nodes.append('')
        
        scene_nodes.append('[node name="GameScene" type="Node3D"]')
        scene_nodes.append('')
        
        import math
        cam_x, cam_y, cam_z = camera_pos["x"], camera_pos["y"], camera_pos["z"]
        look_at_x, look_at_y, look_at_z = 0, 0, 0
        
        forward_x = look_at_x - cam_x
        forward_y = look_at_y - cam_y
        forward_z = look_at_z - cam_z
        length = math.sqrt(forward_x**2 + forward_y**2 + forward_z**2)
        forward_x /= length
        forward_y /= length
        forward_z /= length
        
        right_x = forward_y * 1 - forward_z * 0
        right_y = forward_z * 0 - forward_x * 1
        right_z = forward_x * 0 - forward_y * 0
        length_r = math.sqrt(right_x**2 + right_y**2 + right_z**2)
        if length_r > 0:
            right_x /= length_r
            right_y /= length_r
            right_z /= length_r
        else:
            right_x, right_y, right_z = 1, 0, 0
        
        up_x = right_y * forward_z - right_z * forward_y
        up_y = right_z * forward_x - right_x * forward_z
        up_z = right_x * forward_y - right_y * forward_x
        
        scene_nodes.append('[node name="Camera3D" type="Camera3D" parent="."]')
        scene_nodes.append(f'transform = Transform3D({right_x:.6f}, {up_x:.6f}, {-forward_x:.6f}, {right_y:.6f}, {up_y:.6f}, {-forward_y:.6f}, {right_z:.6f}, {up_z:.6f}, {-forward_z:.6f}, {cam_x}, {cam_y}, {cam_z})')
        scene_nodes.append('fov = 75.0')
        scene_nodes.append('')
        
        scene_nodes.append('[node name="DirectionalLight3D" type="DirectionalLight3D" parent="."]')
        scene_nodes.append('transform = Transform3D(0.707107, -0.408248, 0.57735, 0, 0.816497, 0.57735, -0.707107, -0.408248, 0.57735, 0, 3, 0)')
        scene_nodes.append('light_energy = 1.0')
        scene_nodes.append('shadow_enabled = true')
        scene_nodes.append('')
        
        scene_nodes.append('[node name="WorldEnvironment" type="WorldEnvironment" parent="."]')
        scene_nodes.append('environment = SubResource("Environment_1")')
        scene_nodes.append('')
        
        for obj in objects:
            pos = obj.position or {"x": 0, "y": 0, "z": 0}
            rot = obj.rotation or {"x": 0, "y": 0, "z": 0}
            scale = obj.scale or {"x": 1, "y": 1, "z": 1}
            
            import math
            rx = math.radians(rot['x'])
            ry = math.radians(rot['y'])
            rz = math.radians(rot['z'])
            
            scene_nodes.append(f'[node name="{obj.name}" type="MeshInstance3D" parent="."]')
            scene_nodes.append(f'transform = Transform3D({scale["x"]}, 0, 0, 0, {scale["y"]}, 0, 0, 0, {scale["z"]}, {pos["x"]}, {pos["y"]}, {pos["z"]})')
            scene_nodes.append(f'mesh = SubResource("{obj.name}_Mesh")')
            scene_nodes.append(f'surface_material_override/0 = SubResource("{obj.name}_Material")')
            scene_nodes.append('')
        
        scene_content = '\n'.join(scene_nodes)
        
        scene_file = scenes_dir / f"{scene_spec.name}.tscn"
        scene_file.write_text(scene_content)
        
        self.logger.info(f"Created Godot scene: {scene_file}")
    
    def _get_godot_mesh_resource(self, obj_type: str) -> str:
        """Get Godot mesh resource type for MeshInstance3D"""
        mesh_types = {
            "Cube": "BoxMesh",
            "Sphere": "SphereMesh",
            "Capsule": "CapsuleMesh",
            "Cylinder": "CylinderMesh",
            "Plane": "PlaneMesh"
        }
        return mesh_types.get(obj_type, "BoxMesh")
    
    def _copy_game_scripts(self, project_dir: Path):
        """Copy pre-written GDScript files from server"""
        scripts_dir = project_dir / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        
        source_scripts = Path("/opt/godot-scripts")
        if source_scripts.exists():
            import shutil
            for script_file in source_scripts.glob("*.gd"):
                dest = scripts_dir / script_file.name
                shutil.copy2(script_file, dest)
                self.logger.info(f"Copied script: {script_file.name}")
        else:
            self.logger.warning("Game scripts directory not found at /opt/godot-scripts")
    
    def _copy_theme_assets(self, project_dir: Path, theme_name: str):
        """Copy theme assets (FBX models and textures) into project"""
        import shutil
        
        # Try multiple possible asset locations
        possible_sources = [
            Path(f"/opt/godot-assets/{theme_name}"),
            Path(f"/opt/godot-themes/{theme_name}"),
            Path.home() / f"godot-assets/{theme_name}"
        ]
        
        theme_source = None
        for source in possible_sources:
            if source.exists():
                theme_source = source
                self.logger.info(f"Found theme assets at: {theme_source}")
                break
        
        if not theme_source:
            self.logger.warning(f"Theme directory not found in any location")
            return
        
        # Copy to assets/city directory for direct access
        assets_dest = project_dir / "assets" / theme_name
        assets_dest.mkdir(parents=True, exist_ok=True)
        
        # Copy FBX models
        for model_file in theme_source.glob("*.fbx"):
            shutil.copy2(model_file, assets_dest / model_file.name)
            self.logger.info(f"Copied model: {model_file.name}")
        
        # Copy GLB models
        for model_file in theme_source.glob("*.glb"):
            shutil.copy2(model_file, assets_dest / model_file.name)
            self.logger.info(f"Copied GLB model: {model_file.name}")
        
        # Copy textures if they exist
        for texture_file in theme_source.glob("*.png"):
            shutil.copy2(texture_file, assets_dest / texture_file.name)
            self.logger.info(f"Copied texture: {texture_file.name}")
    
    def _create_game_scripts(self, project_dir: Path, scripts: List[str]):
        """Create game scripts in GDScript"""
        scripts_dir = project_dir / "scripts"
        
        for script in scripts:
            script_content = f'''extends Node

func _ready():
    print("{script} started")

func _process(delta):
    pass
'''
            (scripts_dir / f"{script}.gd").write_text(script_content)
    
    def _create_runner_game_scene(self, project_dir: Path, scene_spec: SceneSpec, theme_name: str = "city"):
        """Create endless runner game scene with level generation"""
        scenes_dir = project_dir / "scenes"
        scenes_dir.mkdir(parents=True, exist_ok=True)
        
        camera_pos = scene_spec.camera_position or {"x": 0, "y": 5, "z": -15}
        
        scene_nodes = []
        
        # Header with load steps (4 subresources + 4 scripts = 8)
        scene_nodes.append('[gd_scene load_steps=8 format=3]\n')
        
        # Load runner scripts
        scene_nodes.append('[ext_resource type="Script" path="res://scripts/runner_game_manager.gd" id="1"]')
        scene_nodes.append('[ext_resource type="Script" path="res://scripts/runner_player.gd" id="2"]')
        scene_nodes.append('[ext_resource type="Script" path="res://scripts/runner_level_generator.gd" id="3"]')
        scene_nodes.append('[ext_resource type="Script" path="res://scripts/runner_ui.gd" id="4"]\n')
        
        # Sub-resources MUST come before nodes
        scene_nodes.append('[sub_resource type="BoxMesh" id="BoxMesh_Player"]')
        scene_nodes.append('size = Vector3(0.8, 1.6, 0.8)\n')
        
        scene_nodes.append('[sub_resource type="StandardMaterial3D" id="PlayerMaterial"]')
        scene_nodes.append('albedo_color = Color(1.0, 0.2, 0.2, 1.0)\n')
        
        scene_nodes.append('[sub_resource type="BoxShape3D" id="PlayerCollisionShape"]')
        scene_nodes.append('size = Vector3(0.8, 1.6, 0.8)\n')
        
        scene_nodes.append('[sub_resource type="Environment" id="Environment_1"]')
        scene_nodes.append('background_mode = 1')
        scene_nodes.append('background_color = Color(0.5, 0.7, 0.9, 1)')
        scene_nodes.append('ambient_light_color = Color(1, 1, 1, 1)')
        scene_nodes.append('ambient_light_energy = 1.0\n')
        
        # Root node with game manager
        scene_nodes.append('[node name="RunnerGame" type="Node3D"]')
        scene_nodes.append('script = ExtResource("1")')
        scene_nodes.append('initial_world_speed = 10.0')
        scene_nodes.append('speed_increase_milestone = 200.0')
        scene_nodes.append('speed_multiplier = 1.1\n')
        
        # Camera behind player looking forward - using proper look-at matrix like working cube scene
        import math
        cam_x, cam_y, cam_z = camera_pos["x"], camera_pos["y"], camera_pos["z"]
        look_at_x, look_at_y, look_at_z = 0, 0, 0
        
        forward_x = look_at_x - cam_x
        forward_y = look_at_y - cam_y
        forward_z = look_at_z - cam_z
        length = math.sqrt(forward_x**2 + forward_y**2 + forward_z**2)
        forward_x /= length
        forward_y /= length
        forward_z /= length
        
        right_x = forward_y * 1 - forward_z * 0
        right_y = forward_z * 0 - forward_x * 1
        right_z = forward_x * 0 - forward_y * 0
        length_r = math.sqrt(right_x**2 + right_y**2 + right_z**2)
        if length_r > 0:
            right_x /= length_r
            right_y /= length_r
            right_z /= length_r
        else:
            right_x, right_y, right_z = 1, 0, 0
        
        up_x = right_y * forward_z - right_z * forward_y
        up_y = right_z * forward_x - right_x * forward_z
        up_z = right_x * forward_y - right_y * forward_x
        
        scene_nodes.append('[node name="Camera3D" type="Camera3D" parent="."]')
        scene_nodes.append(f'transform = Transform3D({right_x:.6f}, {up_x:.6f}, {-forward_x:.6f}, {right_y:.6f}, {up_y:.6f}, {-forward_y:.6f}, {right_z:.6f}, {up_z:.6f}, {-forward_z:.6f}, {cam_x}, {cam_y}, {cam_z})')
        scene_nodes.append('fov = 75.0\n')
        
        # Directional Light
        scene_nodes.append('[node name="DirectionalLight3D" type="DirectionalLight3D" parent="."]')
        scene_nodes.append('transform = Transform3D(1, 0, 0, 0, 0.707, 0.707, 0, -0.707, 0.707, 0, 10, 0)')
        scene_nodes.append('light_energy = 1.5')
        scene_nodes.append('shadow_enabled = false\n')
        
        # World Environment
        scene_nodes.append('[node name="WorldEnvironment" type="WorldEnvironment" parent="."]')
        scene_nodes.append('environment = SubResource("Environment_1")\n')
        
        # Level Generator (creates moving track segments)
        scene_nodes.append('[node name="LevelGenerator" type="Node3D" parent="."]')
        scene_nodes.append('script = ExtResource("3")')
        scene_nodes.append('segment_length = 20.0')
        scene_nodes.append('segments_on_screen = 8')
        scene_nodes.append('despawn_distance = -30.0\n')
        
        # UI Overlay
        scene_nodes.append('[node name="UI" type="CanvasLayer" parent="."]')
        scene_nodes.append('script = ExtResource("4")\n')
        
        # Player with runner controller (Area3D for collision detection)
        scene_nodes.append('[node name="Player" type="Area3D" parent="."]')
        scene_nodes.append('transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0)')
        scene_nodes.append('script = ExtResource("2")')
        scene_nodes.append('lane_distance = 4.0')
        scene_nodes.append('lane_change_speed = 15.0')
        scene_nodes.append('jump_force = 15.0')
        scene_nodes.append('gravity_strength = 30.0\n')
        
        # Player visual mesh
        scene_nodes.append('[node name="PlayerMesh" type="MeshInstance3D" parent="Player"]')
        scene_nodes.append('mesh = SubResource("BoxMesh_Player")')
        scene_nodes.append('surface_material_override/0 = SubResource("PlayerMaterial")\n')
        
        # Player collision shape
        scene_nodes.append('[node name="CollisionShape3D" type="CollisionShape3D" parent="Player"]')
        scene_nodes.append('shape = SubResource("PlayerCollisionShape")\n')
        
        scene_content = '\n'.join(scene_nodes)
        
        scene_file = scenes_dir / "RunnerGame.tscn"
        scene_file.write_text(scene_content)
        
        self.logger.info(f"Created runner game scene: {scene_file}")
