#!/usr/bin/env python3
"""
Test Asset Manager functionality
Tests downloading and processing user assets
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from asset_manager import AssetManager, AssetType

def test_asset_download():
    """Test downloading assets from provided URLs"""
    
    print("=" * 60)
    print("Testing Asset Manager")
    print("=" * 60)
    
    # Test URLs provided by Anshu
    test_assets = [
        [
            "https://zzukvfvsascjizivlszo.supabase.co/storage/v1/object/public/image-tingz/user_123/project_1758802451378_lpiqxio99/z760je/c3rdy5r829rge0csjr3sp8x0tr_1_0.png",
            "https://zzukvfvsascjizivlszo.supabase.co/storage/v1/object/public/image-tingz/user_123/project_1758802451378_lpiqxio99/rlcsoe/f31r97t1c1rge0csjqw8anxyd0_1_2.png"
        ],
        [
            "https://zzukvfvsascjizivlszo.supabase.co/storage/v1/object/image-tingz/user_123/project_1758804683638_4z4vhjjjk/enhebe/4x7cj0tkadrme0csg3qvqqtcqr_1_0_3d.glb",
            "https://zzukvfvsascjizivlszo.supabase.co/storage/v1/object/image-tingz/user_123/project_1758802451378_lpiqxio99/7vz5el/xhh3tx9hc1rm80csg3b8ddc3w4_1_1_3d.glb",
            "https://zzukvfvsascjizivlszo.supabase.co/storage/v1/object/image-tingz/user_123/project_1758802451378_lpiqxio99/83f8y5/xkgthtqt55rmc0csg3f95mcb7r_1_2_3d.glb"
        ]
    ]
    
    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Initialize asset manager
        asset_manager = AssetManager()
        
        print("\n1. Testing asset type detection...")
        for slot_idx, slot_assets in enumerate(test_assets):
            for url in slot_assets:
                asset_type = asset_manager.detect_asset_type(url)
                print(f"   Slot {slot_idx}: {asset_type.value} - {url.split('/')[-1]}")
        
        print("\n2. Downloading all assets...")
        downloaded_assets = asset_manager.download_all_assets(test_assets, temp_dir)
        
        total_downloaded = sum(len(assets) for assets in downloaded_assets.values())
        print(f"   ✅ Downloaded {total_downloaded} assets")
        
        print("\n3. Asset details:")
        for slot_idx, assets in downloaded_assets.items():
            print(f"\n   Slot {slot_idx}:")
            for asset in assets:
                print(f"      - {Path(asset.local_path).name}")
                print(f"        Type: {asset.asset_type.value}")
                print(f"        MIME: {asset.mime_type}")
                print(f"        Size: {asset.file_size:,} bytes")
                print(f"        Hash: {asset.file_hash[:16]}...")
        
        print("\n4. Creating mock Unity project structure...")
        unity_project = temp_dir / "UnityProject"
        unity_assets_dir = unity_project / "Assets"
        unity_assets_dir.mkdir(parents=True, exist_ok=True)
        
        print("\n5. Organizing assets for Unity...")
        asset_manifest = asset_manager.organize_assets_for_unity(downloaded_assets, unity_project)
        
        print(f"   ✅ Organized into Unity project")
        print(f"      Images: {len(asset_manifest['by_type']['images'])}")
        print(f"      3D Models: {len(asset_manifest['by_type']['models'])}")
        print(f"      Audio: {len(asset_manifest['by_type']['audio'])}")
        
        print("\n6. Creating asset loader script...")
        asset_manager.create_asset_loader_script(unity_project, asset_manifest)
        
        loader_script = unity_project / "Assets" / "Scripts" / "UserAssetLoader.cs"
        if loader_script.exists():
            print(f"   ✅ Created: {loader_script}")
            print(f"      Size: {loader_script.stat().st_size:,} bytes")
        
        print("\n7. Verifying file structure:")
        user_content = unity_project / "Assets" / "UserContent"
        if user_content.exists():
            for item in sorted(user_content.rglob("*")):
                if item.is_file():
                    rel_path = item.relative_to(user_content)
                    print(f"      {rel_path} ({item.stat().st_size:,} bytes)")
        
        manifest_file = user_content / "asset_manifest.json"
        if manifest_file.exists():
            print(f"\n   ✅ Asset manifest created: {manifest_file.stat().st_size:,} bytes")
        
        print("\n" + "=" * 60)
        print("✅ All Asset Manager tests passed!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        if temp_dir.exists():
            print(f"\nCleaning up: {temp_dir}")
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    success = test_asset_download()
    sys.exit(0 if success else 1)
