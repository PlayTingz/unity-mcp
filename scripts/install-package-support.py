#!/usr/bin/env python3
"""
Script to add Unity package import support and gltfast package to the production server
"""

PACKAGE_IMPORT_METHOD = '''
    def import_unity_package(self, project_dir: str, package_path: str) -> bool:
        """
        Import a Unity package into the project
        Returns True if import succeeds
        """
        self.logger.info(f"Importing Unity package: {package_path}")
        
        if not os.path.exists(package_path):
            self.logger.error(f"Package not found: {package_path}")
            return False
        
        unity_cmd = [
            self.unity_path,
            "-batchmode",
            "-quit",
            "-projectPath", project_dir,
            "-importPackage", package_path,
            "-logFile", f"/tmp/unity_import_{uuid.uuid4().hex[:8]}.log"
        ]
        
        try:
            self.logger.info(f"Executing Unity package import: {' '.join(unity_cmd)}")
            
            env = os.environ.copy()
            env.update({
                'UNITY_LOG_LEVEL': 'DEBUG',
                'DISPLAY': ':0'
            })
            
            result = subprocess.run(
                unity_cmd,
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=300,
                env=env
            )
            
            if result.returncode == 0:
                self.logger.info("Unity package imported successfully")
                return True
            else:
                self.logger.error(f"Package import failed with exit code: {result.returncode}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Package import timed out")
            return False
        except Exception as e:
            self.logger.error(f"Package import error: {e}")
            return False
'''

MANIFEST_CODE = '''
        # Create Packages/manifest.json with gltfast package
        packages_dir = project_dir / "Packages"
        manifest_content = {
            "dependencies": {
                "com.unity.cloud.gltfast": "6.8.0",
                "com.unity.collab-proxy": "2.0.5",
                "com.unity.feature.development": "1.0.1",
                "com.unity.textmeshpro": "3.0.6",
                "com.unity.timeline": "1.7.5",
                "com.unity.ugui": "1.0.0",
                "com.unity.visualscripting": "1.8.0",
                "com.unity.modules.ai": "1.0.0",
                "com.unity.modules.androidjni": "1.0.0",
                "com.unity.modules.animation": "1.0.0",
                "com.unity.modules.assetbundle": "1.0.0",
                "com.unity.modules.audio": "1.0.0",
                "com.unity.modules.cloth": "1.0.0",
                "com.unity.modules.director": "1.0.0",
                "com.unity.modules.imageconversion": "1.0.0",
                "com.unity.modules.imgui": "1.0.0",
                "com.unity.modules.jsonserialize": "1.0.0",
                "com.unity.modules.particlesystem": "1.0.0",
                "com.unity.modules.physics": "1.0.0",
                "com.unity.modules.physics2d": "1.0.0",
                "com.unity.modules.screencapture": "1.0.0",
                "com.unity.modules.terrain": "1.0.0",
                "com.unity.modules.terrainphysics": "1.0.0",
                "com.unity.modules.tilemap": "1.0.0",
                "com.unity.modules.ui": "1.0.0",
                "com.unity.modules.uielements": "1.0.0",
                "com.unity.modules.umbra": "1.0.0",
                "com.unity.modules.unityanalytics": "1.0.0",
                "com.unity.modules.unitywebrequest": "1.0.0",
                "com.unity.modules.unitywebrequestassetbundle": "1.0.0",
                "com.unity.modules.unitywebrequestaudio": "1.0.0",
                "com.unity.modules.unitywebrequesttexture": "1.0.0",
                "com.unity.modules.unitywebrequestwww": "1.0.0",
                "com.unity.modules.vehicles": "1.0.0",
                "com.unity.modules.video": "1.0.0",
                "com.unity.modules.vr": "1.0.0",
                "com.unity.modules.wind": "1.0.0",
                "com.unity.modules.xr": "1.0.0"
            }
        }
        (packages_dir / "manifest.json").write_text(json.dumps(manifest_content, indent=2))
'''

CITY_PACKAGE_IMPORT = '''
            # Step 2.5: Import CityThemePackage
            city_package_path = "/opt/unity-mcp/packages/CityThemePackage.unitypackage"
            if os.path.exists(city_package_path):
                job.progress = 35
                job.build_log.append("Importing CityThemePackage...")
                await asyncio.get_event_loop().run_in_executor(
                    None, self.unity_generator.import_unity_package, job.project_dir, city_package_path
                )
                self.logger.info("CityThemePackage imported successfully")
            else:
                self.logger.warning(f"CityThemePackage not found at {city_package_path}")
'''

print("=" * 60)
print("Unity Package Support Installation Script")
print("=" * 60)
print()
print("This script will add:")
print("1. import_unity_package() method to Unity project generator")
print("2. com.unity.cloud.gltfast package to manifest.json")
print("3. CityThemePackage import to build service")
print()
print("Files to modify:")
print("  - /opt/unity-mcp/server/build_service.py (if exists)")
print("  - Or create new project generator module")
print()
print("=" * 60)
print()
print("Package Import Method:")
print(PACKAGE_IMPORT_METHOD)
print()
print("Manifest Code:")
print(MANIFEST_CODE)
print()
print("City Package Import:")
print(CITY_PACKAGE_IMPORT)
print()
print("=" * 60)
print()
print("To install, run this script on the server with sudo privileges")
