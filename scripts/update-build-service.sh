#!/bin/bash

set -e

INSTANCE_NAME="unity-mcp-server"
ZONE="us-central1-a"

echo "🔧 Updating Unity Build Service to import CityThemePackage..."

gcloud compute ssh "$INSTANCE_NAME" --zone="$ZONE" --command='cat > /tmp/update_build_service.py << '\''PYEOF'\''
import sys

build_service_path = "/opt/unity-mcp/src/unity_build_service.py"

with open(build_service_path, "r") as f:
    content = f.read()

# Find the _execute_build method and add package import step
search_str = "            # Step 2: Create Unity project"
if search_str in content:
    insert_after = """            # Step 2: Create Unity project
            job.progress = 30
            job.build_log.append("Creating Unity project...")
            await asyncio.get_event_loop().run_in_executor(
                None, self.unity_generator.create_project, game_spec, str(build_workspace)
            )
"""
    
    package_import_code = """
            # Step 2.5: Import CityThemePackage
            city_package_path = "/opt/unity-mcp/packages/CityThemePackage.unitypackage"
            if os.path.exists(city_package_path):
                job.progress = 35
                job.build_log.append("Importing CityThemePackage...")
                await asyncio.get_event_loop().run_in_executor(
                    None, self.unity_generator.import_unity_package, job.project_dir, city_package_path
                )
            else:
                self.logger.warning(f"CityThemePackage not found at {city_package_path}")
"""
    
    # Find position after project creation
    pos = content.find(insert_after)
    if pos != -1:
        # Find end of the project creation block
        end_pos = pos + len(insert_after)
        
        # Insert the package import code
        content = content[:end_pos] + package_import_code + content[end_pos:]
        
        # Add os import if not present
        if "import os" not in content:
            import_pos = content.find("import asyncio")
            if import_pos != -1:
                content = content[:import_pos] + "import os\n" + content[import_pos:]
        
        with open(build_service_path, "w") as f:
            f.write(content)
        
        print("✅ Build service updated to import CityThemePackage")
    else:
        print("❌ Could not find insertion point in build service")
        sys.exit(1)
else:
    print("❌ Could not find project creation step")
    sys.exit(1)
PYEOF
sudo python3 /tmp/update_build_service.py'

echo "✅ Build service update complete"
