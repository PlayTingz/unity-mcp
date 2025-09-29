#!/usr/bin/env python3
"""
Direct Unity WebGL Build Script - Creates a real Unity project and builds it
"""

import os
import sys
import subprocess
import tempfile
import shutil
import uuid

def create_unity_project(project_dir):
    """Create a Unity project with a cube scene"""
    print(f"Creating Unity project at: {project_dir}")
    
    # Create directory structure
    os.makedirs(os.path.join(project_dir, "Assets", "Scenes"), exist_ok=True)
    os.makedirs(os.path.join(project_dir, "Assets", "Scripts"), exist_ok=True)
    os.makedirs(os.path.join(project_dir, "ProjectSettings"), exist_ok=True)
    
    # Create ProjectVersion.txt
    version_content = """m_EditorVersion: 2022.3.45f1
m_EditorVersionWithRevision: 2022.3.45f1 (e5503b4cfcf4)
"""
    with open(os.path.join(project_dir, "ProjectSettings", "ProjectVersion.txt"), 'w') as f:
        f.write(version_content)
    
    # Create basic ProjectSettings.asset
    project_guid = str(uuid.uuid4()).replace('-', '')
    settings_content = f"""%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!129 &1
PlayerSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 23
  productGUID: {project_guid}
  companyName: TestCompany
  productName: SimpleCubeGame
  defaultCursor: {{fileID: 0}}
  cursorHotspot: {{x: 0, y: 0}}
  m_SplashScreenBackgroundColor: {{r: 0.13725491, g: 0.12156863, b: 0.1254902, a: 1}}
  m_ShowUnitySplashScreen: 1
--- !u!47 &1
QualitySettings:
  m_ObjectHideFlags: 0
  serializedVersion: 5
  m_CurrentQuality: 2
  m_QualitySettings:
  - serializedVersion: 2
    name: Low
    pixelLightCount: 0
    shadows: 0
    shadowResolution: 0
    shadowProjection: 1
    shadowCascades: 1
    shadowDistance: 15
    shadowNearPlaneOffset: 3
    shadowCascade2Split: 0.33333334
    shadowCascade4Split: {{x: 0.06666667, y: 0.2, z: 0.46666667}}
    shadowmaskMode: 0
    blendWeights: 1
    textureQuality: 1
    anisotropicTextures: 0
    antiAliasing: 0
    softParticles: 0
    softVegetation: 0
    realtimeReflectionProbes: 0
    billboardsFaceCameraPosition: 0
    vSyncCount: 0
    lodBias: 0.3
    maximumLODLevel: 0
    streamingMipmapsActive: 0
    streamingMipmapsAddAllCameras: 1
    streamingMipmapsMemoryBudget: 512
    streamingMipmapsRenderersPerFrame: 512
    streamingMipmapsMaxLevelReduction: 2
    streamingMipmapsMaxFileIORequests: 1024
    particleRaycastBudget: 4
    asyncUploadTimeSlice: 2
    asyncUploadBufferSize: 16
    asyncUploadPersistentBuffer: 1
    resolutionScalingFixedDPIFactor: 1
    excludedTargetPlatforms: []
  m_PerPlatformDefaultQuality:
    Android: 1
    Lumin: 5
    Nintendo Switch: 5
    PS4: 5
    PSP2: 2
    Stadia: 5
    Standalone: 5
    WebGL: 1
    Windows Store Apps: 5
    XboxOne: 5
    iPhone: 1
    tvOS: 2
"""
    
    with open(os.path.join(project_dir, "ProjectSettings", "ProjectSettings.asset"), 'w') as f:
        f.write(settings_content)
    
    # Create simple scene with a cube
    scene_content = """%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!29 &1
OcclusionCullingSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 2
  m_OcclusionBakeSettings:
    smallestOccluder: 5
    smallestHole: 0.25
    backfaceThreshold: 100
  m_SceneGUID: 00000000000000000000000000000000
  m_OcclusionCullingData: {fileID: 0}
--- !u!104 &2
RenderSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 9
  m_Fog: 0
  m_FogColor: {r: 0.5, g: 0.5, b: 0.5, a: 1}
  m_FogMode: 3
  m_FogDensity: 0.01
  m_LinearFogStart: 0
  m_LinearFogEnd: 300
  m_AmbientSkyColor: {r: 0.212, g: 0.227, b: 0.259, a: 1}
  m_AmbientEquatorColor: {r: 0.114, g: 0.125, b: 0.133, a: 1}
  m_AmbientGroundColor: {r: 0.047, g: 0.043, b: 0.035, a: 1}
  m_AmbientIntensity: 1
  m_AmbientMode: 0
  m_SubtractiveShadowColor: {r: 0.42, g: 0.478, b: 0.627, a: 1}
  m_SkyboxMaterial: {fileID: 10304, guid: 0000000000000000f000000000000000, type: 0}
  m_HaloStrength: 0.5
  m_FlareStrength: 1
  m_FlareFadeSpeed: 3
  m_HaloTexture: {fileID: 0}
  m_SpotCookie: {fileID: 10001, guid: 0000000000000000e000000000000000, type: 0}
  m_DefaultReflectionMode: 0
  m_DefaultReflectionResolution: 128
  m_ReflectionBounces: 1
  m_ReflectionIntensity: 1
  m_CustomReflection: {fileID: 0}
  m_Sun: {fileID: 705507994}
  m_IndirectSpecularColor: {r: 0.44657898, g: 0.4964133, b: 0.5748178, a: 1}
  m_UseRadianceAmbientProbe: 0
--- !u!1 &705507993
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  serializedVersion: 6
  m_Component:
  - component: {fileID: 705507995}
  - component: {fileID: 705507994}
  m_Layer: 0
  m_Name: Directional Light
  m_TagString: Untagged
  m_Icon: {fileID: 0}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!108 &705507994
Light:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: 705507993}
  m_Enabled: 1
  serializedVersion: 10
  m_Type: 1
  m_Shape: 0
  m_Color: {r: 1, g: 0.95686275, b: 0.8392157, a: 1}
  m_Intensity: 1
  m_Range: 10
  m_SpotAngle: 30
  m_InnerSpotAngle: 21.80208
  m_CookieSize: 10
  m_Shadows:
    m_Type: 2
    m_Resolution: -1
    m_CustomResolution: -1
    m_Strength: 1
    m_Bias: 0.05
    m_NormalBias: 0.4
    m_NearPlane: 2
  m_Cookie: {fileID: 0}
  m_DrawHalo: 0
  m_Flare: {fileID: 0}
  m_RenderMode: 0
  m_CullingMask:
    serializedVersion: 2
    m_Bits: 4294967295
  m_RenderingLayerMask: 1
  m_Lightmapping: 1
  m_AreaSize: {x: 1, y: 1}
  m_BounceIntensity: 1
  m_ColorTemperature: 6570
  m_UseColorTemperature: 0
  m_ShadowRadius: 0
  m_ShadowAngle: 0
--- !u!4 &705507995
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: 705507993}
  m_LocalRotation: {x: 0.40821788, y: -0.23456968, z: 0.10938163, w: 0.8754261}
  m_LocalPosition: {x: 0, y: 3, z: 0}
  m_LocalScale: {x: 1, y: 1, z: 1}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {fileID: 0}
  m_RootOrder: 1
  m_LocalEulerAnglesHint: {x: 50, y: -30, z: 0}
--- !u!1 &963194225
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  serializedVersion: 6
  m_Component:
  - component: {fileID: 963194228}
  - component: {fileID: 963194227}
  - component: {fileID: 963194226}
  m_Layer: 0
  m_Name: Main Camera
  m_TagString: MainCamera
  m_Icon: {fileID: 0}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!81 &963194226
AudioListener:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: 963194225}
  m_Enabled: 1
--- !u!20 &963194227
Camera:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: 963194225}
  m_Enabled: 1
  serializedVersion: 2
  m_ClearFlags: 1
  m_BackGroundColor: {r: 0.19215687, g: 0.3019608, b: 0.4745098, a: 0}
  m_projectionMatrixMode: 1
  m_GateFitMode: 2
  m_FOVAxisMode: 0
  m_SensorSize: {x: 36, y: 24}
  m_LensShift: {x: 0, y: 0}
  m_FocalLength: 50
  m_NormalizedViewPortRect:
    serializedVersion: 2
    x: 0
    y: 0
    width: 1
    height: 1
  m_near: 0.3
  m_far: 1000
  m_orthographic: 0
  m_orthographicSize: 5
  m_targetTexture: {fileID: 0}
  m_targetDisplay: 0
  m_targetEye: 3
  m_HDR: 1
  m_AllowMSAA: 1
  m_AllowDynamicResolution: 0
  m_ForceIntoRT: 0
  m_OcclusionCulling: 1
  m_StereoConvergence: 10
  m_StereoSeparation: 0.022
--- !u!4 &963194228
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: 963194225}
  m_LocalRotation: {x: 0, y: 0, z: 0, w: 1}
  m_LocalPosition: {x: 0, y: 1, z: -10}
  m_LocalScale: {x: 1, y: 1, z: 1}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {fileID: 0}
  m_RootOrder: 0
  m_LocalEulerAnglesHint: {x: 0, y: 0, z: 0}
--- !u!1 &1234567890
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  serializedVersion: 6
  m_Component:
  - component: {fileID: 1234567894}
  - component: {fileID: 1234567893}
  - component: {fileID: 1234567892}
  - component: {fileID: 1234567891}
  m_Layer: 0
  m_Name: Cube
  m_TagString: Untagged
  m_Icon: {fileID: 0}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!65 &1234567891
BoxCollider:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: 1234567890}
  m_Material: {fileID: 0}
  m_IsTrigger: 0
  m_Enabled: 1
  serializedVersion: 2
  m_Size: {x: 1, y: 1, z: 1}
  m_Center: {x: 0, y: 0, z: 0}
--- !u!23 &1234567892
MeshRenderer:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: 1234567890}
  m_Enabled: 1
  m_CastShadows: 1
  m_ReceiveShadows: 1
  m_DynamicOccludee: 1
  m_StaticShadowCaster: 0
  m_MotionVectors: 1
  m_LightProbeUsage: 1
  m_ReflectionProbeUsage: 1
  m_RayTracingMode: 2
  m_RayTraceProcedural: 0
  m_RenderingLayerMask: 1
  m_RendererPriority: 0
  m_Materials:
  - {fileID: 10303, guid: 0000000000000000f000000000000000, type: 0}
  m_StaticBatchInfo:
    firstSubMesh: 0
    subMeshCount: 0
  m_StaticBatchRoot: {fileID: 0}
  m_ProbeAnchor: {fileID: 0}
  m_LightProbeVolumeOverride: {fileID: 0}
  m_ScaleInLightmap: 1
  m_ReceiveGI: 1
  m_PreserveUVs: 0
  m_IgnoreNormalsForChartDetection: 0
  m_ImportantGI: 0
  m_StitchLightmapSeams: 1
  m_SelectedEditorRenderState: 3
  m_MinimumChartSize: 4
  m_AutoUVMaxDistance: 0.5
  m_AutoUVMaxAngle: 89
  m_LightmapParameters: {fileID: 0}
  m_SortingLayerID: 0
  m_SortingLayer: 0
  m_SortingOrder: 0
  m_AdditionalVertexStreams: {fileID: 0}
--- !u!33 &1234567893
MeshFilter:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: 1234567890}
  m_Mesh: {fileID: 10202, guid: 0000000000000000e000000000000000, type: 0}
--- !u!4 &1234567894
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: 1234567890}
  m_LocalRotation: {x: 0, y: 0.38268343, z: 0, w: 0.92387956}
  m_LocalPosition: {x: 0, y: 0, z: 0}
  m_LocalScale: {x: 1, y: 1, z: 1}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {fileID: 0}
  m_RootOrder: 2
  m_LocalEulerAnglesHint: {x: 0, y: 45, z: 0}
"""
    
    with open(os.path.join(project_dir, "Assets", "Scenes", "SampleScene.unity"), 'w') as f:
        f.write(scene_content)
    
    print("✅ Unity project structure created")

def build_webgl_with_unity(project_dir, output_dir, unity_path="/opt/unity/Unity"):
    """Build WebGL using Unity command line"""
    print(f"Building WebGL with Unity from: {project_dir}")
    print(f"Output directory: {output_dir}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Unity build command
    unity_cmd = [
        unity_path,
        "-batchmode",
        "-quit",
        "-projectPath", project_dir,
        "-buildTarget", "WebGL",
        "-executeMethod", "UnityEditor.BuildPipeline.BuildPlayer",
        "-logFile", "/tmp/unity_direct_build.log"
    ]
    
    print(f"Running Unity: {' '.join(unity_cmd)}")
    
    try:
        # Set environment for Unity
        env = os.environ.copy()
        env['UNITY_LOG_LEVEL'] = 'DEBUG'
        
        result = subprocess.run(
            unity_cmd,
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minutes
            env=env
        )
        
        print(f"Unity exit code: {result.returncode}")
        
        # Show Unity log
        log_file = "/tmp/unity_direct_build.log"
        if os.path.exists(log_file):
            print("\n=== Unity Build Log ===")
            with open(log_file, 'r') as f:
                log_content = f.read()
                print(log_content[-2000:])  # Show last 2000 chars
        
        if result.stdout:
            print("\n=== Unity STDOUT ===")
            print(result.stdout)
            
        if result.stderr:
            print("\n=== Unity STDERR ===")
            print(result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Unity build timed out!")
        return False
    except Exception as e:
        print(f"❌ Unity build error: {e}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 create_real_unity_build.py <output_directory>")
        print("Example: python3 create_real_unity_build.py /tmp/test_webgl_build")
        sys.exit(1)
    
    output_dir = sys.argv[1]
    
    print("🎮 Unity WebGL Direct Build Test")
    print("=" * 50)
    
    # Create temporary project directory
    temp_project = tempfile.mkdtemp(prefix="unity_test_")
    
    try:
        # Step 1: Create Unity project
        print("\n1️⃣ Creating Unity project...")
        create_unity_project(temp_project)
        
        # Step 2: Build WebGL
        print("\n2️⃣ Building WebGL...")
        if build_webgl_with_unity(temp_project, output_dir):
            print("✅ Unity build completed!")
            
            # Check output
            if os.path.exists(output_dir):
                files = []
                for root, dirs, filenames in os.walk(output_dir):
                    for filename in filenames:
                        files.append(os.path.join(root, filename))
                
                print(f"\n📁 Output files ({len(files)}):")
                for f in sorted(files)[:15]:  # Show first 15 files
                    rel_path = os.path.relpath(f, output_dir)
                    size = os.path.getsize(f)
                    print(f"  - {rel_path} ({size} bytes)")
                
                if len(files) > 15:
                    print(f"  ... and {len(files) - 15} more files")
                    
                # Check for key WebGL files
                webgl_files = ['index.html', 'Build', 'TemplateData']
                found_files = []
                for wf in webgl_files:
                    check_path = os.path.join(output_dir, wf)
                    if os.path.exists(check_path):
                        found_files.append(wf)
                        
                print(f"\n🎯 WebGL files found: {', '.join(found_files)}")
                
                if 'index.html' in found_files:
                    print("\n🎉 SUCCESS: WebGL build appears to be complete!")
                    print(f"📍 To test, serve the directory: {output_dir}")
                    return True
                else:
                    print("\n⚠️  WebGL build incomplete - no index.html found")
                    return False
            else:
                print(f"❌ Output directory not found: {output_dir}")
                return False
        else:
            print("❌ Unity build failed!")
            return False
            
    finally:
        # Cleanup
        if os.path.exists(temp_project):
            shutil.rmtree(temp_project)
            print(f"🧹 Cleaned up: {temp_project}")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)