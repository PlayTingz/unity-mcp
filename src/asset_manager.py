#!/usr/bin/env python3
"""
Asset Manager for Unity MCP Build Service
Handles downloading and processing user-uploaded assets (images, 3D models, audio, etc.)
"""

import os
import urllib.request
import urllib.parse
import logging
import hashlib
import mimetypes
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class AssetType(Enum):
    IMAGE = "image"
    MODEL_3D = "3d_model"
    AUDIO = "audio"
    VIDEO = "video"
    UNKNOWN = "unknown"

@dataclass
class DownloadedAsset:
    url: str
    local_path: str
    asset_type: AssetType
    mime_type: str
    file_size: int
    file_hash: str

class AssetManager:
    """Manages downloading and organizing user assets for Unity projects"""
    
    SUPPORTED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tga', '.psd'}
    SUPPORTED_MODEL_EXTENSIONS = {'.fbx', '.obj', '.glb', '.gltf', '.blend', '.dae'}
    SUPPORTED_AUDIO_EXTENSIONS = {'.mp3', '.wav', '.ogg', '.aiff', '.aif'}
    SUPPORTED_VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.webm'}
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
    def detect_asset_type(self, url: str, mime_type: Optional[str] = None) -> AssetType:
        """Detect asset type from URL and MIME type"""
        parsed_url = urllib.parse.urlparse(url)
        path = parsed_url.path.lower()
        ext = os.path.splitext(path)[1]
        
        if ext in self.SUPPORTED_IMAGE_EXTENSIONS:
            return AssetType.IMAGE
        elif ext in self.SUPPORTED_MODEL_EXTENSIONS:
            return AssetType.MODEL_3D
        elif ext in self.SUPPORTED_AUDIO_EXTENSIONS:
            return AssetType.AUDIO
        elif ext in self.SUPPORTED_VIDEO_EXTENSIONS:
            return AssetType.VIDEO
        
        if mime_type:
            if mime_type.startswith('image/'):
                return AssetType.IMAGE
            elif mime_type.startswith('audio/'):
                return AssetType.AUDIO
            elif mime_type.startswith('video/'):
                return AssetType.VIDEO
            elif mime_type in ['model/gltf-binary', 'model/gltf+json']:
                return AssetType.MODEL_3D
                
        return AssetType.UNKNOWN
    
    def download_asset(self, url: str, output_dir: Path, filename: Optional[str] = None) -> DownloadedAsset:
        """
        Download a single asset from URL
        Returns DownloadedAsset with metadata
        """
        self.logger.info(f"Downloading asset: {url}")
        
        try:
            parsed_url = urllib.parse.urlparse(url)
            if not filename:
                filename = os.path.basename(parsed_url.path)
                if not filename or filename == '/':
                    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
                    filename = f"asset_{url_hash}"
            
            output_path = output_dir / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            headers = {
                'User-Agent': 'Unity-MCP-Build-Service/1.0'
            }
            
            request = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(request, timeout=30) as response:
                mime_type = response.headers.get('Content-Type', '').split(';')[0]
                content = response.read()
                
                with open(output_path, 'wb') as f:
                    f.write(content)
                
                file_hash = hashlib.sha256(content).hexdigest()
                file_size = len(content)
                
                asset_type = self.detect_asset_type(url, mime_type)
                
                self.logger.info(f"Downloaded {asset_type.value}: {filename} ({file_size} bytes)")
                
                return DownloadedAsset(
                    url=url,
                    local_path=str(output_path),
                    asset_type=asset_type,
                    mime_type=mime_type,
                    file_size=file_size,
                    file_hash=file_hash
                )
                
        except Exception as e:
            self.logger.error(f"Failed to download asset {url}: {e}")
            raise
    
    def download_asset_set(self, asset_urls: List[str], output_dir: Path, 
                          slot_name: str = "slot") -> List[DownloadedAsset]:
        """
        Download a set of assets (e.g., all player sprites, all backgrounds)
        Returns list of DownloadedAsset objects
        """
        downloaded_assets = []
        
        slot_dir = output_dir / slot_name
        slot_dir.mkdir(parents=True, exist_ok=True)
        
        for idx, url in enumerate(asset_urls):
            try:
                parsed_url = urllib.parse.urlparse(url)
                original_name = os.path.basename(parsed_url.path)
                ext = os.path.splitext(original_name)[1]
                
                filename = f"{slot_name}_{idx}{ext}"
                
                asset = self.download_asset(url, slot_dir, filename)
                downloaded_assets.append(asset)
                
            except Exception as e:
                self.logger.warning(f"Skipping failed asset download: {url} - {e}")
                continue
        
        self.logger.info(f"Downloaded {len(downloaded_assets)}/{len(asset_urls)} assets for {slot_name}")
        return downloaded_assets
    
    def download_all_assets(self, assets: List[List[str]], build_dir: Path) -> Dict[int, List[DownloadedAsset]]:
        """
        Download all user assets organized by slots
        
        Args:
            assets: List of asset URL lists (each list is a slot)
            build_dir: Build directory to store assets
            
        Returns:
            Dictionary mapping slot index to list of downloaded assets
        """
        assets_dir = build_dir / "UserAssets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        downloaded_by_slot = {}
        
        for slot_idx, asset_urls in enumerate(assets):
            if not asset_urls:
                continue
                
            slot_name = f"slot_{slot_idx}"
            downloaded = self.download_asset_set(asset_urls, assets_dir, slot_name)
            downloaded_by_slot[slot_idx] = downloaded
        
        total_assets = sum(len(assets) for assets in downloaded_by_slot.values())
        self.logger.info(f"Downloaded {total_assets} total assets across {len(downloaded_by_slot)} slots")
        
        return downloaded_by_slot
    
    def organize_assets_for_unity(self, downloaded_assets: Dict[int, List[DownloadedAsset]], 
                                  project_dir: Path) -> Dict[str, Any]:
        """
        Organize downloaded assets into Unity project structure
        
        Args:
            downloaded_assets: Assets organized by slot
            project_dir: Unity project directory
            
        Returns:
            Asset manifest with paths and metadata
        """
        unity_assets_dir = project_dir / "Assets" / "UserContent"
        unity_assets_dir.mkdir(parents=True, exist_ok=True)
        
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
            slot_dir = unity_assets_dir / f"Slot{slot_idx}"
            slot_dir.mkdir(parents=True, exist_ok=True)
            
            slot_assets = []
            
            for asset in assets:
                src_path = Path(asset.local_path)
                dest_path = slot_dir / src_path.name
                
                if src_path.exists():
                    import shutil
                    shutil.copy2(src_path, dest_path)
                    
                    relative_path = dest_path.relative_to(project_dir / "Assets")
                    
                    asset_info = {
                        "path": str(relative_path),
                        "type": asset.asset_type.value,
                        "mime_type": asset.mime_type,
                        "size": asset.file_size,
                        "original_url": asset.url
                    }
                    
                    slot_assets.append(asset_info)
                    
                    if asset.asset_type == AssetType.IMAGE:
                        asset_manifest["by_type"]["images"].append(asset_info)
                    elif asset.asset_type == AssetType.MODEL_3D:
                        asset_manifest["by_type"]["models"].append(asset_info)
                    elif asset.asset_type == AssetType.AUDIO:
                        asset_manifest["by_type"]["audio"].append(asset_info)
                    elif asset.asset_type == AssetType.VIDEO:
                        asset_manifest["by_type"]["videos"].append(asset_info)
            
            asset_manifest["slots"][slot_idx] = slot_assets
        
        manifest_path = unity_assets_dir / "asset_manifest.json"
        with open(manifest_path, 'w') as f:
            import json
            json.dump(asset_manifest, f, indent=2)
        
        self.logger.info(f"Organized assets into Unity project: {unity_assets_dir}")
        return asset_manifest
    
    def create_asset_loader_script(self, project_dir: Path, asset_manifest: Dict[str, Any]):
        """
        Create Unity C# script to load and use user assets at runtime
        """
        scripts_dir = project_dir / "Assets" / "Scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        
        script_content = f'''using UnityEngine;
using System.Collections.Generic;
using System.IO;

public class UserAssetLoader : MonoBehaviour
{{
    private Dictionary<int, List<Texture2D>> imagesBySlot = new Dictionary<int, List<Texture2D>>();
    private Dictionary<int, List<GameObject>> modelsBySlot = new Dictionary<int, List<GameObject>>();
    private Dictionary<int, List<AudioClip>> audioBySlot = new Dictionary<int, List<AudioClip>>();
    
    void Start()
    {{
        LoadAllAssets();
    }}
    
    void LoadAllAssets()
    {{
        // Load images from UserContent
{self._generate_image_loading_code(asset_manifest)}
        
        Debug.Log($"Loaded {{GetTotalAssetCount()}} user assets");
    }}
    
    public Texture2D GetImage(int slot, int index)
    {{
        if (imagesBySlot.ContainsKey(slot) && index < imagesBySlot[slot].Count)
            return imagesBySlot[slot][index];
        return null;
    }}
    
    public GameObject GetModel(int slot, int index)
    {{
        if (modelsBySlot.ContainsKey(slot) && index < modelsBySlot[slot].Count)
            return modelsBySlot[slot][index];
        return null;
    }}
    
    public AudioClip GetAudio(int slot, int index)
    {{
        if (audioBySlot.ContainsKey(slot) && index < audioBySlot[slot].Count)
            return audioBySlot[slot][index];
        return null;
    }}
    
    int GetTotalAssetCount()
    {{
        int count = 0;
        foreach (var list in imagesBySlot.Values) count += list.Count;
        foreach (var list in modelsBySlot.Values) count += list.Count;
        foreach (var list in audioBySlot.Values) count += list.Count;
        return count;
    }}
}}
'''
        
        script_path = scripts_dir / "UserAssetLoader.cs"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        self.logger.info(f"Created asset loader script: {script_path}")
    
    def _generate_image_loading_code(self, manifest: Dict[str, Any]) -> str:
        """Generate C# code to load images from Resources"""
        code_lines = []
        
        for slot_idx, assets in manifest.get("slots", {}).items():
            images = [a for a in assets if a["type"] == "image"]
            if images:
                code_lines.append(f'        imagesBySlot[{slot_idx}] = new List<Texture2D>();')
                for img in images:
                    path = img["path"].replace("\\", "/")
                    resource_path = path.replace(".png", "").replace(".jpg", "")
                    code_lines.append(f'        imagesBySlot[{slot_idx}].Add(Resources.Load<Texture2D>("UserContent/{resource_path}"));')
        
        return "\n".join(code_lines) if code_lines else "        // No images to load"
