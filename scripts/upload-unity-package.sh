#!/bin/bash

set -e

INSTANCE_NAME="unity-mcp-server"
ZONE="us-central1-a"
PACKAGE_PATH="/home/jpb/dev/tingz/CityThemePackage.unitypackage"
REMOTE_PACKAGE_DIR="/opt/unity-mcp/packages"

echo "🚀 Uploading Unity Package to Server..."

echo "📦 Creating remote package directory..."
gcloud compute ssh "$INSTANCE_NAME" --zone="$ZONE" --command="sudo mkdir -p $REMOTE_PACKAGE_DIR && sudo chmod 755 $REMOTE_PACKAGE_DIR"

echo "📤 Uploading CityThemePackage.unitypackage..."
gcloud compute scp "$PACKAGE_PATH" "$INSTANCE_NAME:~/CityThemePackage.unitypackage" --zone="$ZONE"

echo "📁 Moving package to permanent location..."
gcloud compute ssh "$INSTANCE_NAME" --zone="$ZONE" --command="sudo mv ~/CityThemePackage.unitypackage $REMOTE_PACKAGE_DIR/ && sudo chmod 644 $REMOTE_PACKAGE_DIR/CityThemePackage.unitypackage"

echo "✅ Package uploaded successfully to $REMOTE_PACKAGE_DIR/CityThemePackage.unitypackage"

echo ""
echo "🔧 Updating Unity project generator to import package..."

cat > /tmp/update_generator.sh << 'SCRIPT_EOF'
#!/bin/bash

GENERATOR_FILE="/opt/unity-mcp/src/unity_project_generator.py"

sudo cp "$GENERATOR_FILE" "${GENERATOR_FILE}.backup"

sudo tee /tmp/package_import_method.py > /dev/null << 'EOF'
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
EOF

echo "Package import method created"
SCRIPT_EOF

gcloud compute scp /tmp/update_generator.sh "$INSTANCE_NAME:~/update_generator.sh" --zone="$ZONE"
gcloud compute ssh "$INSTANCE_NAME" --zone="$ZONE" --command="chmod +x ~/update_generator.sh && ~/update_generator.sh"

echo ""
echo "📋 Updating Unity project generator to include package and gltfast..."

gcloud compute ssh "$INSTANCE_NAME" --zone="$ZONE" --command='cat > /tmp/update_project_generator.py << '\''PYEOF'\''
import sys

generator_path = "/opt/unity-mcp/src/unity_project_generator.py"

with open(generator_path, "r") as f:
    content = f.read()

if "import_unity_package" not in content:
    insert_pos = content.find("    def build_webgl(self,")
    if insert_pos == -1:
        print("Could not find insertion point")
        sys.exit(1)
    
    package_import_method = """
    def import_unity_package(self, project_dir: str, package_path: str) -> bool:
        """
        """Import a Unity package into the project
        Returns True if import succeeds
        """
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
            self.logger.info(f"Executing Unity package import: {\" \".join(unity_cmd)}")
            
            env = os.environ.copy()
            env.update({
                \"UNITY_LOG_LEVEL\": \"DEBUG\",
                \"DISPLAY\": \":0\"
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
    
"""
    
    content = content[:insert_pos] + package_import_method + content[insert_pos:]
    
    with open(generator_path, "w") as f:
        f.write(content)
    
    print("Added import_unity_package method")
else:
    print("import_unity_package method already exists")

if "\"com.unity.cloud.gltfast\"" not in content:
    manifest_pos = content.find("    def _create_project_structure(self, project_dir: Path):")
    if manifest_pos != -1:
        end_pos = content.find("def _create_project_settings", manifest_pos)
        if end_pos != -1:
            insert_at = content.rfind("\n", manifest_pos, end_pos)
            
            manifest_method = """
        
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
"""
            
            content = content[:insert_at] + manifest_method + content[insert_at:]
            
            with open(generator_path, "w") as f:
                f.write(content)
            
            print("Added manifest.json creation with gltfast package")
        else:
            print("Could not find end position for manifest insertion")
    else:
        print("Could not find _create_project_structure method")
else:
    print("gltfast package already configured")

print("Unity project generator updated successfully")
PYEOF
python3 /tmp/update_project_generator.py'

echo ""
echo "🔄 Restarting Unity MCP service..."
gcloud compute ssh "$INSTANCE_NAME" --zone="$ZONE" --command="sudo systemctl restart unity-mcp"

echo ""
echo "✅ Setup complete!"
echo ""
echo "Summary:"
echo "  - CityThemePackage.unitypackage uploaded to: $REMOTE_PACKAGE_DIR/"
echo "  - Unity project generator updated to import packages"
echo "  - com.unity.cloud.gltfast package (v6.8.0) will be included in all new projects"
echo "  - Unity MCP service restarted"
echo ""
echo "Next steps:"
echo "  - New Unity projects will automatically include the gltfast package"
echo "  - To import CityThemePackage, the project generator needs to call import_unity_package()"
