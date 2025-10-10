#!/usr/bin/env python3
"""
Unity Project Generator - Production Implementation
Creates real Unity projects with game content and builds WebGL games.
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
    type: str  # Cube, Sphere, Capsule, etc.
    position: Optional[Dict[str, float]] = None
    rotation: Optional[Dict[str, float]] = None
    scale: Optional[Dict[str, float]] = None
    material_color: Optional[Dict[str, float]] = None
    components: Optional[List[str]] = None

@dataclass
class SceneSpec:
    """Specification for a Unity scene"""
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

class UnityProjectGenerator:
    """Production Unity project generator with real Unity integration"""
    
    def __init__(self, unity_path: str = "/opt/unity/Unity"):
        self.unity_path = unity_path
        self.logger = logging.getLogger(__name__)
        
        # Verify Unity installation
        if not os.path.exists(unity_path):
            raise FileNotFoundError(f"Unity not found at {unity_path}")
    
    def create_project(self, game_spec: GameSpec, output_dir: str, import_theme_package: bool = True) -> tuple[str, str]:
        """
        Use shared Unity project and create a new scene for this game
        Returns tuple of (shared_project_path, scene_name)
        """
        shared_project_dir = Path("/opt/unity-mcp/shared-project")
        
        if not shared_project_dir.exists():
            raise FileNotFoundError(f"Shared Unity project not found at {shared_project_dir}")
        
        self.logger.info(f"Using shared Unity project at: {shared_project_dir}")
        
        # Get scene name from game_spec.scene if it exists, otherwise generate one
        if game_spec.scene and game_spec.scene.name:
            scene_name = game_spec.scene.name
        else:
            scene_name = game_spec.name.replace(" ", "_") + "_" + uuid.uuid4().hex[:8]
        
        # Create the scene (returns the scene GUID that was generated)
        scene_guid = self._create_game_scene(shared_project_dir, game_spec.scene or SceneSpec(name=scene_name), game_spec.theme)
        
        # Update EditorBuildSettings to include this scene with matching GUID
        self._update_build_settings(shared_project_dir, scene_name, scene_guid)
        
        if game_spec.scripts:
            self._create_game_scripts(shared_project_dir, game_spec.scripts)
        
        self.logger.info(f"Created scene {scene_name} in shared project")
        return (str(shared_project_dir), scene_name)
    
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
                'DISPLAY': ':99'
            })
            
            result = subprocess.run(
                unity_cmd,
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=900,  # 15 minutes for package import
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
    
    def build_webgl(self, project_dir: str, build_output_dir: str, development_build: bool = False) -> bool:
        """
        Build the Unity project to WebGL
        Returns True if build succeeds
        """
        self.logger.info(f"Building WebGL from {project_dir} to {build_output_dir}")
        
        build_path = Path(build_output_dir)
        build_path.mkdir(parents=True, exist_ok=True)
        
        # Unity build command using our custom build script
        unity_cmd = [
            self.unity_path,
            "-batchmode",
            "-quit",
            "-projectPath", project_dir,
            "-executeMethod", "BuildScript.BuildWebGL",
            "-buildPath", str(build_path),
            "-logFile", f"/tmp/unity_build_{uuid.uuid4().hex[:8]}.log"
        ]
        
        if development_build:
            unity_cmd.append("-developmentBuild")
        
        try:
            self.logger.info(f"Executing Unity build: {' '.join(unity_cmd)}")
            
            # Set Unity environment
            env = os.environ.copy()
            env.update({
                'UNITY_LOG_LEVEL': 'DEBUG',
                'DISPLAY': ':99'  # For headless display (Xvfb)
            })
            
            # Open log file for Unity output
            log_file_path = unity_cmd[unity_cmd.index("-logFile") + 1]
            
            result = subprocess.run(
                unity_cmd,
                cwd=project_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=1800,  # 30 minutes for WebGL build
                env=env
            )
            
            self.logger.info(f"Unity build completed with exit code: {result.returncode}")
            self.logger.info(f"Unity build log: {log_file_path}")
            
            # Check if build succeeded
            if result.returncode == 0:
                # Verify WebGL build files exist
                expected_files = ['index.html', 'Build', 'TemplateData']
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
                self.logger.error(f"Unity build failed with exit code: {result.returncode}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.warning("Unity build timed out, but checking if build completed anyway...")
            # Unity might have finished even though subprocess timed out
            # Check if build files exist
            expected_files = ['index.html', 'Build', 'TemplateData']
            missing_files = []
            
            for expected_file in expected_files:
                file_path = build_path / expected_file
                if not file_path.exists():
                    missing_files.append(expected_file)
            
            if missing_files:
                self.logger.error(f"Build timed out and files are missing: {missing_files}")
                return False
            else:
                self.logger.info("Build timed out but all files are present - build succeeded!")
                return True
        except Exception as e:
            self.logger.error(f"Unity build error: {e}")
            return False
    
    def _update_build_settings(self, project_dir: Path, scene_name: str, scene_guid: str):
        """Update EditorBuildSettings to build the specified scene with matching GUID"""
        settings_dir = project_dir / "ProjectSettings"
        
        build_settings_content = f"""%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!1045 &1
EditorBuildSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 2
  m_Scenes:
  - enabled: 1
    path: Assets/Scenes/{scene_name}.unity
    guid: {scene_guid}
  m_configObjects: {{}}
"""
        (settings_dir / "EditorBuildSettings.asset").write_text(build_settings_content)
        self.logger.info(f"Updated build settings for scene: {scene_name} with GUID: {scene_guid}")
    
    def _create_project_structure(self, project_dir: Path):
        """Create basic Unity project directory structure"""
        directories = [
            "Assets/Scenes",
            "Assets/Scripts", 
            "Assets/Materials",
            "Assets/Editor",
            "ProjectSettings",
            "Packages"
        ]
        
        for directory in directories:
            (project_dir / directory).mkdir(parents=True, exist_ok=True)
        
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
    
    def _create_project_settings(self, project_dir: Path, game_spec: GameSpec):
        """Create Unity ProjectSettings files"""
        settings_dir = project_dir / "ProjectSettings"
        
        # ProjectVersion.txt
        version_content = """m_EditorVersion: 2022.3.48f1
m_EditorVersionWithRevision: 2022.3.48f1 (8bf49c377ebf)
"""
        (settings_dir / "ProjectVersion.txt").write_text(version_content)
        
        # ProjectSettings.asset
        project_guid = str(uuid.uuid4()).replace('-', '')
        settings_content = f"""%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!129 &1
PlayerSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 23
  productGUID: {project_guid}
  AndroidProfiler: 0
  AndroidFilterTouchesWhenObscured: 0
  AndroidEnableSustainedPerformanceMode: 0
  defaultScreenOrientation: 3
  targetDevice: 2
  useOnDemandResources: 0
  accelerometerFrequency: 60
  companyName: {game_spec.company_name}
  productName: {game_spec.name}
  defaultCursor: {{fileID: 0}}
  cursorHotspot: {{x: 0, y: 0}}
  m_SplashScreenBackgroundColor: {{r: 0.13725491, g: 0.12156863, b: 0.1254902, a: 1}}
  m_ShowUnitySplashScreen: 0
  m_ShowUnitySplashLogo: 0
  m_SplashScreenOverlayOpacity: 1
  m_SplashScreenAnimation: 1
  m_SplashScreenLogoStyle: 1
  m_SplashScreenDrawMode: 0
  bundleVersion: {game_spec.version}
  preloadedAssets: []
  metroInputSource: 0
  wsaTransparentSwapchain: 0
  m_HolographicPauseOnTrackingLoss: 1
  xboxOneDisableKinectGpuReservation: 1
  xboxOneEnable7thCore: 1
  vrSettings:
    cardboard:
      depthFormat: 0
      enableTransitionView: 0
    daydream:
      depthFormat: 0
      useSustainedPerformanceMode: 0
      enableVideoLayer: 0
      useProtectedVideoMemory: 0
    hololens:
      depthFormat: 1
      depthBufferSharingEnabled: 1
    lumin:
      depthFormat: 0
      frameTiming: 2
      enableGLCache: 0
      glCacheMaxBlobSize: 524288
      glCacheMaxFileSize: 8388608
    oculus:
      sharedDepthBuffer: 1
      dashSupport: 1
      lowOverheadMode: 0
      protectedContext: 0
      v2Signing: 1
    enable360StereoCapture: 0
  isWsaHolographicRemotingEnabled: 0
  protectGraphicsMemory: 0
  enableFrameTimingStats: 0
  useHDRDisplay: 0
  m_ColorGamuts: 00000000
  targetPixelDensity: 30
  resolutionScalingMode: 0
  androidSupportedAspectRatio: 1
  androidMaxAspectRatio: 2.1
  applicationIdentifier: {{}}
  buildNumber: {{}}
  AndroidBundleVersionCode: 1
  AndroidMinSdkVersion: 19
  AndroidTargetSdkVersion: 0
  AndroidPreferredInstallLocation: 1
  aotOptions: 
  stripEngineCode: 1
  iPhoneStrippingLevel: 0
  iPhoneScriptCallOptimization: 0
  ForceInternetPermission: 0
  ForceSDCardPermission: 0
  CreateWallpaper: 0
  APKExpansionFiles: 0
  keepLoadedShadersAlive: 0
  StripUnusedMeshComponents: 1
  VertexChannelCompressionMask: 4054
  iPhoneSdkVersion: 988
  iOSTargetOSVersionString: 11.0
  tvOSSdkVersion: 0
  tvOSRequireExtendedGameController: 0
  tvOSTargetOSVersionString: 11.0
  uIPrerenderedIcon: 0
  uIRequiresPersistentWiFi: 0
  uIRequiresFullScreen: 1
  uIStatusBarHidden: 1
  uIExitOnSuspend: 0
  uIStatusBarStyle: 0
  appleDeveloperTeamID: 
  iOSManualSigningProvisioningProfileID: 
  tvOSManualSigningProvisioningProfileID: 
  iOSManualSigningProvisioningProfileType: 0
  tvOSManualSigningProvisioningProfileType: 0
  appleEnableAutomaticSigning: 0
  iOSRequireARKit: 0
  iOSAutomaticallyDetectAndAddCapabilities: 1
  appleEnableProMotion: 0
  clonedFromGUID: 10ad67313c32b4133841a28e8b4e2b2b
  templatePackageId: com.unity.template.3d@4.2.8
  templateDefaultScene: Assets/Scenes/SampleScene.unity
  AndroidTargetArchitectures: 1
  AndroidSplashScreenScale: 0
  androidSplashScreen: {{fileID: 0}}
  AndroidKeystoreName: 
  AndroidKeyaliasName: 
  AndroidBuildApkPerCpuArchitecture: 0
  AndroidTVCompatibility: 0
  AndroidIsGame: 1
  AndroidEnableTango: 0
  androidEnableBanner: 1
  androidUseLowAccuracyLocation: 0
  androidUseCustomKeystore: 0
  m_AndroidBanners:
  - width: 320
    height: 180
    banner: {{fileID: 0}}
  androidGamepadSupportLevel: 0
  AndroidValidateAppBundleSize: 1
  AndroidAppBundleSizeToValidate: 150
  m_BuildTargetIcons: []
  m_BuildTargetPlatformIcons: []
  m_BuildTargetBatching:
  - m_BuildTarget: Standalone
    m_StaticBatching: 1
    m_DynamicBatching: 0
  - m_BuildTarget: tvOS
    m_StaticBatching: 1
    m_DynamicBatching: 0
  - m_BuildTarget: Android
    m_StaticBatching: 1
    m_DynamicBatching: 0
  - m_BuildTarget: iPhone
    m_StaticBatching: 1
    m_DynamicBatching: 0
  - m_BuildTarget: WebGL
    m_StaticBatching: 0
    m_DynamicBatching: 0
  m_BuildTargetGraphicsJobs:
  - m_BuildTarget: MacStandaloneSupport
    m_GraphicsJobs: 0
  - m_BuildTarget: Switch
    m_GraphicsJobs: 1
  - m_BuildTarget: MetroSupport
    m_GraphicsJobs: 0
  - m_BuildTarget: AppleTVSupport
    m_GraphicsJobs: 0
  - m_BuildTarget: BJMSupport
    m_GraphicsJobs: 1
  - m_BuildTarget: LinuxStandaloneSupport
    m_GraphicsJobs: 1
  - m_BuildTarget: PS4Player
    m_GraphicsJobs: 1
  - m_BuildTarget: iOSSupport
    m_GraphicsJobs: 0
  - m_BuildTarget: WindowsStandaloneSupport
    m_GraphicsJobs: 1
  - m_BuildTarget: XboxOnePlayer
    m_GraphicsJobs: 1
  - m_BuildTarget: LuminSupport
    m_GraphicsJobs: 0
  - m_BuildTarget: AndroidPlayer
    m_GraphicsJobs: 0
  - m_BuildTarget: WebGLSupport
    m_GraphicsJobs: 0
  m_BuildTargetGraphicsJobMode:
  - m_BuildTarget: PS4Player
    m_GraphicsJobMode: 0
  - m_BuildTarget: XboxOnePlayer
    m_GraphicsJobMode: 0
  m_BuildTargetGraphicsAPIs:
  - m_BuildTarget: AndroidPlayer
    m_APIs: 150000000b000000
    m_Automatic: 0
  - m_BuildTarget: iOSSupport
    m_APIs: 10000000
    m_Automatic: 1
  - m_BuildTarget: AppleTVSupport
    m_APIs: 10000000
    m_Automatic: 0
  - m_BuildTarget: WebGLSupport
    m_APIs: 0b000000
    m_Automatic: 1
  m_BuildTargetVRSettings:
  - m_BuildTarget: Standalone
    m_Enabled: 0
    m_Devices:
    - Oculus
    - OpenVR
  openGLRequireES31: 0
  openGLRequireES31AEP: 0
  openGLRequireES32: 0
  m_TemplateCustomTags: {{}}
  mobileMTRendering:
    Android: 1
    iPhone: 1
    tvOS: 1
  m_BuildTargetGroupLightmapEncodingQuality:
  - m_BuildTarget: Android
    m_EncodingQuality: 1
  - m_BuildTarget: iPhone
    m_EncodingQuality: 1
  - m_BuildTarget: tvOS
    m_EncodingQuality: 1
  m_BuildTargetGroupLightmapSettings: []
  playModeTestRunnerEnabled: 0
  runPlayModeTestAsEditModeTest: 0
  actionOnDotNetUnhandledException: 1
  enableInternalProfiler: 0
  logObjCUncaughtExceptions: 1
  enableCrashReportAPI: 0
  cameraUsageDescription: 
  locationUsageDescription: 
  microphoneUsageDescription: 
  switchScreenResolutionBehavior: 2
  switchNMETAOverride: 
  switchNetLibKey: 
  switchSocketMemoryPoolSize: 6144
  switchSocketAllocatorPoolSize: 128
  switchSocketConcurrencyLimit: 14
  switchUseCPUProfiler: 0
  switchApplicationID: 0x01004b9000490000
  switchNSODependencies: 
  switchTitleNames_0: 
  switchTitleNames_1: 
  switchTitleNames_2: 
  switchTitleNames_3: 
  switchTitleNames_4: 
  switchTitleNames_5: 
  switchTitleNames_6: 
  switchTitleNames_7: 
  switchTitleNames_8: 
  switchTitleNames_9: 
  switchTitleNames_10: 
  switchTitleNames_11: 
  switchTitleNames_12: 
  switchTitleNames_13: 
  switchTitleNames_14: 
  switchPublisherNames_0: 
  switchPublisherNames_1: 
  switchPublisherNames_2: 
  switchPublisherNames_3: 
  switchPublisherNames_4: 
  switchPublisherNames_5: 
  switchPublisherNames_6: 
  switchPublisherNames_7: 
  switchPublisherNames_8: 
  switchPublisherNames_9: 
  switchPublisherNames_10: 
  switchPublisherNames_11: 
  switchPublisherNames_12: 
  switchPublisherNames_13: 
  switchPublisherNames_14: 
  switchIcons_0: {{fileID: 0}}
  switchIcons_1: {{fileID: 0}}
  switchIcons_2: {{fileID: 0}}
  switchIcons_3: {{fileID: 0}}
  switchIcons_4: {{fileID: 0}}
  switchIcons_5: {{fileID: 0}}
  switchIcons_6: {{fileID: 0}}
  switchIcons_7: {{fileID: 0}}
  switchIcons_8: {{fileID: 0}}
  switchIcons_9: {{fileID: 0}}
  switchIcons_10: {{fileID: 0}}
  switchIcons_11: {{fileID: 0}}
  switchIcons_12: {{fileID: 0}}
  switchIcons_13: {{fileID: 0}}
  switchIcons_14: {{fileID: 0}}
  switchSmallIcons_0: {{fileID: 0}}
  switchSmallIcons_1: {{fileID: 0}}
  switchSmallIcons_2: {{fileID: 0}}
  switchSmallIcons_3: {{fileID: 0}}
  switchSmallIcons_4: {{fileID: 0}}
  switchSmallIcons_5: {{fileID: 0}}
  switchSmallIcons_6: {{fileID: 0}}
  switchSmallIcons_7: {{fileID: 0}}
  switchSmallIcons_8: {{fileID: 0}}
  switchSmallIcons_9: {{fileID: 0}}
  switchSmallIcons_10: {{fileID: 0}}
  switchSmallIcons_11: {{fileID: 0}}
  switchSmallIcons_12: {{fileID: 0}}
  switchSmallIcons_13: {{fileID: 0}}
  switchSmallIcons_14: {{fileID: 0}}
  switchManualHTML: 
  switchAccessibleURLs: 
  switchLegalInformation: 
  switchMainThreadStackSize: 1048576
  switchPresenceGroupId: 
  switchLogoHandling: 0
  switchReleaseVersion: 0
  switchDisplayVersion: 1.0.0
  switchStartupUserAccount: 0
  switchTouchScreenUsage: 0
  switchSupportedLanguagesMask: 0
  switchLogoType: 0
  switchApplicationErrorCodeCategory: 
  switchUserAccountSaveDataSize: 0
  switchUserAccountSaveDataJournalSize: 0
  switchApplicationAttribute: 0
  switchCardSpecSize: -1
  switchCardSpecClock: -1
  switchRatingsMask: 0
  switchRatingsInt_0: 0
  switchRatingsInt_1: 0
  switchRatingsInt_2: 0
  switchRatingsInt_3: 0
  switchRatingsInt_4: 0
  switchRatingsInt_5: 0
  switchRatingsInt_6: 0
  switchRatingsInt_7: 0
  switchRatingsInt_8: 0
  switchRatingsInt_9: 0
  switchRatingsInt_10: 0
  switchRatingsInt_11: 0
  switchRatingsInt_12: 0
  switchLocalCommunicationIds_0: 
  switchLocalCommunicationIds_1: 
  switchLocalCommunicationIds_2: 
  switchLocalCommunicationIds_3: 
  switchLocalCommunicationIds_4: 
  switchLocalCommunicationIds_5: 
  switchLocalCommunicationIds_6: 
  switchLocalCommunicationIds_7: 
  switchParentalControl: 0
  switchAllowsScreenshot: 1
  switchAllowsVideoCapturing: 1
  switchAllowsRuntimeAddOnContentInstall: 0
  switchDataLossConfirmation: 0
  switchUserAccountLockEnabled: 0
  switchSystemResourceMemory: 16777216
  switchSupportedNpadStyles: 22
  switchNativeFsCacheSize: 32
  switchIsHoldTypeHorizontal: 0
  switchSupportedNpadCount: 8
  switchSocketConfigEnabled: 0
  switchTcpInitialSendBufferSize: 32
  switchTcpInitialReceiveBufferSize: 64
  switchTcpAutoSendBufferSizeMax: 256
  switchTcpAutoReceiveBufferSizeMax: 256
  switchUdpSendBufferSize: 9
  switchUdpReceiveBufferSize: 42
  switchSocketBufferEfficiency: 4
  switchSocketInitializeEnabled: 1
  switchNetworkInterfaceManagerInitializeEnabled: 1
  switchPlayerConnectionEnabled: 1
  ps4NPAgeRating: 12
  ps4NPTitleSecret: 
  ps4NPTrophyPackPath: 
  ps4ParentalLevel: 11
  ps4ContentID: ED1633-NPXX51362_00-0000000000000000
  ps4Category: 0
  ps4MasterVersion: 01.00
  ps4AppVersion: 01.00
  ps4AppType: 0
  ps4ParamSfxPath: 
  ps4VideoOutPixelFormat: 0
  ps4VideoOutInitialWidth: 1920
  ps4VideoOutBaseModeInitialWidth: 1920
  ps4VideoOutReprojectionRate: 60
  ps4PronunciationXMLPath: 
  ps4PronunciationSIGPath: 
  ps4BackgroundImagePath: 
  ps4StartupImagePath: 
  ps4StartupImagesFolder: 
  ps4IconImagesFolder: 
  ps4SaveDataImagePath: 
  ps4SdkOverride: 
  ps4BGMPath: 
  ps4ShareFilePath: 
  ps4ShareOverlayImagePath: 
  ps4PrivacyGuardImagePath: 
  ps4ExtraSceSysFile: 
  ps4NPtitleDatPath: 
  ps4RemotePlayKeyAssignment: -1
  ps4RemotePlayKeyMappingDir: 
  ps4PlayTogetherPlayerCount: 0
  ps4EnterButtonAssignment: 1
  ps4ApplicationParam1: 0
  ps4ApplicationParam2: 0
  ps4ApplicationParam3: 0
  ps4ApplicationParam4: 0
  ps4DownloadDataSize: 0
  ps4GarlicHeapSize: 2147483648
  ps4ProGarlicHeapSize: 2684354560
  playerPrefsMaxSize: 32768
  ps4Passcode: frAQBc8Wsa1xVPfvJcrgRYwTiizs2trQ
  ps4pnSessions: 1
  ps4pnPresence: 1
  ps4pnFriends: 1
  ps4pnGameCustomData: 1
  playerPrefsSupport: 0
  enableApplicationExit: 0
  resetTempFolder: 1
  restrictedAudioUsageRights: 0
  ps4UseResolutionFallback: 0
  ps4ReprojectionSupport: 0
  ps4UseAudio3dBackend: 0
  ps4UseLowGarlicHeapForOno: 0
  ps4SocialScreenEnabled: 0
  ps4ScriptOptimizationLevel: 0
  ps4Audio3dVirtualSpeakerCount: 14
  ps4attribCpuUsage: 1
  ps4PatchPkgPath: 
  ps4PatchLatestPkgPath: 
  ps4PatchChangeinfoPath: 
  ps4PatchDayOne: 0
  ps4attribUserManagement: 0
  ps4attribMoveSupport: 0
  ps4attrib3DSupport: 0
  ps4attribShareSupport: 0
  ps4attribExclusiveVR: 0
  ps4disableAutoHideSplash: 0
  ps4videoRecordingFeaturesUsed: 0
  ps4contentSearchFeaturesUsed: 0
  ps4CompatibilityPS5: 0
  ps4GPU800MHz: 1
  ps4attribEyeToEyeDistanceSettingVR: 0
  ps4IncludedModules: []
  ps4attribVROutputEnabled: 0
  monoEnv: 
  splashScreenBackgroundSourceLandscape: {{fileID: 0}}
  splashScreenBackgroundSourcePortrait: {{fileID: 0}}
  blurSplashScreenBackground: 1
  spritePackerPolicy: 
  webGLMemorySize: 16
  webGLExceptionSupport: 1
  webGLNameFilesAsHashes: 0
  webGLDataCaching: 1
  webGLDebugSymbols: 0
  webGLEmscriptenArgs: 
  webGLModulesDirectory: 
  webGLTemplate: APPLICATION:Default
  webGLAnalyzeBuildSize: 0
  webGLUseEmbeddedResources: 0
  webGLCompressionFormat: 1
  webGLLinkerTarget: 1
  webGLThreadsSupport: 0
  webGLWasmStreaming: 0
  scriptingDefineSymbols: {{}}
  platformArchitecture: {{}}
  scriptingBackend: {{}}
  il2cppCompilerConfiguration: {{}}
  managedStrippingLevel: {{}}
  incrementalIl2cppBuild: {{}}
  allowUnsafeCode: 0
  additionalIl2CppArgs: 
  scriptingRuntimeVersion: 1
  gcIncremental: 1
  assemblyVersionValidation: 1
  gcWBarrierValidation: 0
  apiCompatibilityLevelPerPlatform: {{}}
  m_RenderingPath: 1
  m_MobileRenderingPath: 1
  metroPackageName: Template_3D
  metroPackageVersion: 
  metroCertificatePath: 
  metroCertificatePassword: 
  metroCertificateSubject: 
  metroCertificateIssuer: 
  metroCertificateNotAfter: 0000000000000000
  metroApplicationDescription: Template_3D
  wsaImages: {{}}
  metroTileShortName: 
  metroTileShowName: 0
  metroMediumTileShowName: 0
  metroLargeTileShowName: 0
  metroWideTileShowName: 0
  metroSupportStreamingInstall: 0
  metroLastRequiredScene: 0
  metroDefaultTileSize: 1
  metroTileForegroundText: 2
  metroTileBackgroundColor: {{r: 0.13333334, g: 0.17254902, b: 0.21568628, a: 0}}
  metroSplashScreenBackgroundColor: {{r: 0.12941177, g: 0.17254902, b: 0.21568628, a: 1}}
  metroSplashScreenUseBackgroundColor: 0
  platformCapabilities: {{}}
  metroTargetDeviceFamilies: {{}}
  metroFTAName: 
  metroFTAFileTypes: []
  metroProtocolName: 
  XboxOneProductId: 
  XboxOneUpdateKey: 
  XboxOneSandboxId: 
  XboxOneContentId: 
  XboxOneTitleId: 
  XboxOneSCId: 
  XboxOneGameOsOverridePath: 
  XboxOnePackagingOverridePath: 
  XboxOneAppManifestOverridePath: 
  XboxOneVersion: 1.0.0.0
  XboxOnePackageEncryption: 0
  XboxOnePackageUpdateGranularity: 2
  XboxOneDescription: 
  XboxOneLanguage:
  - enus
  XboxOneCapability: []
  XboxOneGameRating: {{}}
  XboxOneIsContentPackage: 0
  XboxOneEnhancedXboxCompatibilityMode: 0
  XboxOneEnableGPUVariability: 1
  XboxOneSockets: {{}}
  XboxOneSplashScreen: {{fileID: 0}}
  XboxOneAllowedProductIds: []
  XboxOnePersistentLocalStorageSize: 0
  XboxOneXTitleMemory: 8
  XboxOneOverrideIdentityName: 
  XboxOneOverrideIdentityPublisher: 
  vrEditorSettings: {{}}
  cloudServicesEnabled:
    UNet: 1
  luminIcon:
    m_Name: 
    m_ModelFolderPath: 
    m_PortalFolderPath: 
  luminCert:
    m_CertPath: 
    m_SignPackage: 1
  luminIsChannelApp: 0
  luminVersion:
    m_VersionCode: 1
    m_VersionName: 
  apiCompatibilityLevel: 6
  cloudProjectId: 
  framebufferDepthMemorylessMode: 0
  projectName: 
  organizationId: 
  cloudEnabled: 0
  enableNativePlatformBackendsForNewInputSystem: 0
  disableOldInputManagerSupport: 0
  legacyClampBlendShapeWeights: 0
  virtualTexturingSupportEnabled: 0
"""
        
        (settings_dir / "ProjectSettings.asset").write_text(settings_content)
        
        # EditorBuildSettings.asset - defines scenes in build
        build_settings_content = """%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!1045 &1
EditorBuildSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 2
  m_Scenes:
  - enabled: 1
    path: Assets/Scenes/GameScene.unity
    guid: 99c9720ab356a0642a771bea13969a05
  m_configObjects: {}
"""
        (settings_dir / "EditorBuildSettings.asset").write_text(build_settings_content)
    
    def _create_editor_build_script(self, project_dir: Path):
        """Create C# Editor script for building"""
        editor_dir = project_dir / "Assets" / "Editor"
        
        build_script_content = """using UnityEngine;
using UnityEditor;
using UnityEditor.Build.Reporting;
using System.IO;
using System.Linq;

public class BuildScript
{
    [MenuItem("Build/Build WebGL")]
    public static void BuildWebGL()
    {
        BuildWebGLFromCommandLine();
    }
    
    public static void BuildWebGLFromCommandLine()
    {
        // Get build path from command line arguments
        string buildPath = GetArg("-buildPath");
        if (string.IsNullOrEmpty(buildPath))
        {
            buildPath = "Build/WebGL";
        }
        
        Debug.Log($"Building WebGL to: {buildPath}");
        
        // Get scenes from EditorBuildSettings (respects what was configured)
        string[] scenePaths = EditorBuildSettings.scenes
            .Where(s => s.enabled)
            .Select(s => s.path)
            .ToArray();
        
        if (scenePaths.Length == 0)
        {
            Debug.LogError("No scenes enabled in EditorBuildSettings!");
            EditorApplication.Exit(1);
            return;
        }
        
        Debug.Log($"Building {scenePaths.Length} scene(s): {string.Join(", ", scenePaths)}");
        
        // Configure build settings
        BuildPlayerOptions buildPlayerOptions = new BuildPlayerOptions();
        buildPlayerOptions.scenes = scenePaths;
        buildPlayerOptions.locationPathName = buildPath;
        buildPlayerOptions.target = BuildTarget.WebGL;
        buildPlayerOptions.options = BuildOptions.None;
        
        // Check for development build flag
        if (HasArg("-developmentBuild"))
        {
            buildPlayerOptions.options |= BuildOptions.Development;
        }
        
        // Perform the build
        BuildReport report = BuildPipeline.BuildPlayer(buildPlayerOptions);
        BuildSummary summary = report.summary;
        
        if (summary.result == BuildResult.Succeeded)
        {
            Debug.Log($"Build succeeded: {summary.outputPath}");
            Debug.Log($"Build size: {summary.totalSize} bytes");
            
            // Ensure we have proper WebGL template
            EnsureWebGLTemplate(buildPath);
            
            EditorApplication.Exit(0);
        }
        else
        {
            Debug.LogError($"Build failed with {summary.totalErrors} errors");
            foreach (BuildStep step in report.steps)
            {
                foreach (BuildStepMessage message in step.messages)
                {
                    if (message.type == LogType.Error || message.type == LogType.Exception)
                    {
                        Debug.LogError($"Build Error: {message.content}");
                    }
                }
            }
            EditorApplication.Exit(1);
        }
    }
    
    private static void EnsureWebGLTemplate(string buildPath)
    {
        // Ensure index.html exists and is properly configured
        string indexPath = Path.Combine(buildPath, "index.html");
        if (!File.Exists(indexPath))
        {
            Debug.LogWarning("index.html not found, Unity should have created it");
        }
    }
    
    private static string GetArg(string name)
    {
        var args = System.Environment.GetCommandLineArgs();
        for (int i = 0; i < args.Length; i++)
        {
            if (args[i] == name && args.Length > i + 1)
            {
                return args[i + 1];
            }
        }
        return null;
    }
    
    private static bool HasArg(string name)
    {
        var args = System.Environment.GetCommandLineArgs();
        for (int i = 0; i < args.Length; i++)
        {
            if (args[i] == name)
            {
                return true;
            }
        }
        return false;
    }
}
"""
        
        (editor_dir / "BuildScript.cs").write_text(build_script_content)
    
    def _create_theme_applier_script(self, project_dir: Path, theme_name: str):
        """Create theme applier script for automatic theme application"""
        scripts_dir = project_dir / "Assets" / "Scripts"
        
        theme_applier_content = f"""using UnityEngine;

public class ThemeApplier : MonoBehaviour
{{
    void Start()
    {{
        // Apply theme automatically on start
        ApplyTheme("{theme_name}");
    }}
    
    void ApplyTheme(string themeName)
    {{
        // Find ThemeManager in scene
        var themeManager = FindObjectOfType<ThemeManager>();
        if (themeManager == null)
        {{
            Debug.LogWarning("ThemeManager not found in scene");
            return;
        }}
        
        // Load theme data from Resources
        var themeData = Resources.Load<ThemeData>($"Themes/{{themeName}}Theme");
        if (themeData == null)
        {{
            Debug.LogWarning($"Theme '{{themeName}}' not found in Resources/Themes/");
            return;
        }}
        
        // Apply the theme
        themeManager.SetTheme(themeData);
        Debug.Log($"Applied theme: {{themeName}}");
    }}
}}
"""
        (scripts_dir / "ThemeApplier.cs").write_text(theme_applier_content)
        self.logger.info(f"Created ThemeApplier script for theme: {theme_name}")
    
    def _create_gamemanager_script(self, project_dir: Path):
        """Create GameManager script to keep game loop running"""
        scripts_dir = project_dir / "Assets" / "Scripts"
        
        gamemanager_content = """using UnityEngine;

public class GameManager : MonoBehaviour
{
    void Start()
    {
        Debug.Log("=== GAME STARTED ===");
        Debug.Log("GameManager initialized successfully!");
        DontDestroyOnLoad(gameObject);
    }
    
    void Update()
    {
        // Keep game loop running
    }
}
"""
        (scripts_dir / "GameManager.cs").write_text(gamemanager_content)
        self.logger.info("Created GameManager script")
    
    def _create_game_scene(self, project_dir: Path, scene_spec: SceneSpec, theme_name: str = "city") -> str:
        """Create Unity scene with specified game objects"""
        scenes_dir = project_dir / "Assets" / "Scenes"
        
        # Generate unique random object IDs for this scene to avoid conflicts
        import random
        random.seed()  # Ensure different IDs each time
        camera_id = random.randint(1000000000, 2000000000)
        light_id = random.randint(1000000000, 2000000000)
        theme_manager_id = random.randint(1000000000, 2000000000)
        theme_applier_id = random.randint(1000000000, 2000000000)
        gamemanager_id = random.randint(1000000000, 2000000000)
        
        objects = scene_spec.objects or []
        scene_objects = []
        
        # Add camera
        camera_pos = scene_spec.camera_position or {"x": 0, "y": 1, "z": -10}
        camera_rot = scene_spec.camera_rotation or {"x": 0, "y": 0, "z": 0}
        
        scene_objects.append(self._create_camera_yaml(camera_id, camera_pos, camera_rot))
        
        # Add directional light
        scene_objects.append(self._create_light_yaml(light_id))
        
        # Note: Removed ThemeManager, ThemeApplier, and SimpleGameManager because:
        # - ThemeApplier script doesn't exist in shared project
        # - SimpleGameManager script reference causes Unity runtime initialization failure
        # - Not needed for basic game scenes - Unity runs without them
        
        # SimpleGameManager removed - was causing "missing script" errors
        # scene_objects.append(self._create_gamemanager_yaml(gamemanager_id))
        
        # Add SceneInitializer to ensure Unity WebGL initialization completes
        # COMMENTED OUT - SceneInitializer script doesn't exist, causes missing script errors
        # initializer_id = random.randint(4000000000, 5000000000)
        # scene_objects.append(self._create_scene_initializer_yaml(initializer_id))
        
        # Add game objects with random unique IDs
        for i, obj in enumerate(objects):
            obj_id = random.randint(2000000000, 3000000000)
            scene_objects.append(self._create_game_object_yaml(obj_id, obj))
        
        # Create scene YAML
        scene_content = f"""%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!29 &1
OcclusionCullingSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 2
  m_OcclusionBakeSettings:
    smallestOccluder: 5
    smallestHole: 0.25
    backfaceThreshold: 100
  m_SceneGUID: 99c9720ab356a0642a771bea13969a05
  m_OcclusionCullingData: {{fileID: 0}}
--- !u!104 &2
RenderSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 9
  m_Fog: 0
  m_FogColor: {{r: 0.5, g: 0.5, b: 0.5, a: 1}}
  m_FogMode: 3
  m_FogDensity: 0.01
  m_LinearFogStart: 0
  m_LinearFogEnd: 300
  m_AmbientSkyColor: {{r: 0.212, g: 0.227, b: 0.259, a: 1}}
  m_AmbientEquatorColor: {{r: 0.4, g: 0.4, b: 0.4, a: 1}}
  m_AmbientGroundColor: {{r: 0.3, g: 0.3, b: 0.3, a: 1}}
  m_AmbientIntensity: 2
  m_AmbientMode: 1
  m_SubtractiveShadowColor: {{r: 0.42, g: 0.478, b: 0.627, a: 1}}
  m_SkyboxMaterial: {{fileID: 10304, guid: 0000000000000000f000000000000000, type: 0}}
  m_HaloStrength: 0.5
  m_FlareStrength: 1
  m_FlareFadeSpeed: 3
  m_HaloTexture: {{fileID: 0}}
  m_SpotCookie: {{fileID: 10001, guid: 0000000000000000e000000000000000, type: 0}}
  m_DefaultReflectionMode: 0
  m_DefaultReflectionResolution: 128
  m_ReflectionBounces: 1
  m_ReflectionIntensity: 1
  m_CustomReflection: {{fileID: 0}}
  m_Sun: {{fileID: {light_id}}}
  m_IndirectSpecularColor: {{r: 0.44657898, g: 0.4964133, b: 0.5748178, a: 1}}
  m_UseRadianceAmbientProbe: 0
--- !u!157 &3
LightmapSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 12
  m_GIWorkflowMode: 1
  m_GISettings:
    serializedVersion: 2
    m_BounceScale: 1
    m_IndirectOutputScale: 1
    m_AlbedoBoost: 1
    m_EnvironmentLightingMode: 0
    m_EnableBakedLightmaps: 1
    m_EnableRealtimeLightmaps: 0
  m_LightmapEditorSettings:
    serializedVersion: 12
    m_Resolution: 2
    m_BakeResolution: 40
    m_AtlasSize: 1024
    m_AO: 0
    m_AOMaxDistance: 1
    m_CompAOExponent: 1
    m_CompAOExponentDirect: 0
    m_ExtractAmbientOcclusion: 0
    m_Padding: 2
    m_LightmapParameters: {{fileID: 0}}
    m_LightmapsBakeMode: 1
    m_TextureCompression: 1
    m_FinalGather: 0
    m_FinalGatherFiltering: 1
    m_FinalGatherRayCount: 256
    m_ReflectionCompression: 2
    m_MixedBakeMode: 2
    m_BakeBackend: 1
    m_PVRSampling: 1
    m_PVRDirectSampleCount: 32
    m_PVRSampleCount: 500
    m_PVRBounces: 2
    m_PVREnvironmentSampleCount: 500
    m_PVREnvironmentReferencePointCount: 2048
    m_PVRFilteringMode: 2
    m_PVRDenoiserTypeDirect: 0
    m_PVRDenoiserTypeIndirect: 0
    m_PVRDenoiserTypeAO: 0
    m_PVRFilterTypeDirect: 0
    m_PVRFilterTypeIndirect: 0
    m_PVRFilterTypeAO: 0
    m_PVREnvironmentMIS: 0
    m_PVRCulling: 1
    m_PVRFilteringGaussRadiusDirect: 1
    m_PVRFilteringGaussRadiusIndirect: 5
    m_PVRFilteringGaussRadiusAO: 2
    m_PVRFilteringAtrousPositionSigmaDirect: 0.5
    m_PVRFilteringAtrousPositionSigmaIndirect: 2
    m_PVRFilteringAtrousPositionSigmaAO: 1
    m_ExportTrainingData: 0
    m_TrainingDataDestination: TrainingData
    m_LightProbeSampleCountMultiplier: 4
  m_LightingDataAsset: {{fileID: 0}}
  m_LightingSettings: {{fileID: 0}}
--- !u!196 &4
NavMeshSettings:
  serializedVersion: 2
  m_ObjectHideFlags: 0
  m_BuildSettings:
    serializedVersion: 2
    agentTypeID: 0
    agentRadius: 0.5
    agentHeight: 2
    agentSlope: 45
    agentClimb: 0.4
    ledgeDropHeight: 0
    maxJumpAcrossDistance: 0
    minRegionArea: 2
    manualCellSize: 0
    cellSize: 0.16666667
    manualTileSize: 0
    tileSize: 256
    accuratePlacement: 0
    maxJobWorkers: 0
    preserveTilesOutsideBounds: 0
    debug:
      m_Flags: 0
  m_NavMeshData: {{fileID: 0}}
{chr(10).join(scene_objects)}
"""
        
        # Write the scene file
        scene_file = scenes_dir / f"{scene_spec.name}.unity"
        scene_file.write_text(scene_content)
        
        # Create matching .meta file with the GUID used in EditorBuildSettings
        scene_guid = str(uuid.uuid4()).replace('-', '')
        meta_content = f"""fileFormatVersion: 2
guid: {scene_guid}
DefaultImporter:
  externalObjects: {{}}
  userData: 
  assetBundleName: 
  assetBundleVariant: 
"""
        (scenes_dir / f"{scene_spec.name}.unity.meta").write_text(meta_content)
        
        # Update EditorBuildSettings with the same GUID
        self._update_build_settings(project_dir, scene_spec.name, scene_guid)
        
        # Return the GUID so caller can use it
        return scene_guid
    
    def _euler_to_quaternion(self, euler_x: float, euler_y: float, euler_z: float) -> Dict[str, float]:
        """Convert Euler angles (degrees) to quaternion"""
        import math
        # Convert degrees to radians
        x = math.radians(euler_x)
        y = math.radians(euler_y)
        z = math.radians(euler_z)
        
        # Compute quaternion components (ZYX order, which Unity uses)
        cy = math.cos(z * 0.5)
        sy = math.sin(z * 0.5)
        cp = math.cos(y * 0.5)
        sp = math.sin(y * 0.5)
        cr = math.cos(x * 0.5)
        sr = math.sin(x * 0.5)
        
        qw = cr * cp * cy + sr * sp * sy
        qx = sr * cp * cy - cr * sp * sy
        qy = cr * sp * cy + sr * cp * sy
        qz = cr * cp * sy - sr * sp * cy
        
        return {'x': qx, 'y': qy, 'z': qz, 'w': qw}
    
    def _create_camera_yaml(self, camera_id: int, position: Dict[str, float], rotation: Dict[str, float]) -> str:
        """Create Unity camera YAML"""
        # Convert Euler angles to quaternion
        quat = self._euler_to_quaternion(rotation['x'], rotation['y'], rotation['z'])
        
        return f"""--- !u!1 &{camera_id}
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: {camera_id + 3}}}
  - component: {{fileID: {camera_id + 2}}}
  - component: {{fileID: {camera_id + 1}}}
  m_Layer: 0
  m_Name: Main Camera
  m_TagString: MainCamera
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!81 &{camera_id + 1}
AudioListener:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {camera_id}}}
  m_Enabled: 1
--- !u!20 &{camera_id + 2}
Camera:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {camera_id}}}
  m_Enabled: 1
  serializedVersion: 2
  m_ClearFlags: 1
  m_BackGroundColor: {{r: 0.2, g: 0.3, b: 0.5, a: 1}}
  m_projectionMatrixMode: 1
  m_GateFitMode: 2
  m_FOVAxisMode: 0
  m_SensorSize: {{x: 36, y: 24}}
  m_LensShift: {{x: 0, y: 0}}
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
  m_targetTexture: {{fileID: 0}}
  m_targetDisplay: 0
  m_targetEye: 3
  m_HDR: 1
  m_AllowMSAA: 1
  m_AllowDynamicResolution: 0
  m_ForceIntoRT: 0
  m_OcclusionCulling: 1
  m_StereoConvergence: 10
  m_StereoSeparation: 0.022
--- !u!4 &{camera_id + 3}
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {camera_id}}}
  m_LocalRotation: {{x: {quat['x']}, y: {quat['y']}, z: {quat['z']}, w: {quat['w']}}}
  m_LocalPosition: {{x: {position['x']}, y: {position['y']}, z: {position['z']}}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: 0}}
  m_RootOrder: 0
  m_LocalEulerAnglesHint: {{x: {rotation['x']}, y: {rotation['y']}, z: {rotation['z']}}}"""
    
    def _create_theme_manager_yaml(self, manager_id: int) -> str:
        """Create ThemeManager GameObject YAML"""
        return f"""--- !u!1 &{manager_id}
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: {manager_id + 2}}}
  - component: {{fileID: {manager_id + 1}}}
  m_Layer: 0
  m_Name: ThemeManager
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!114 &{manager_id + 1}
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {manager_id}}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: 66d271533f6d75c49ae9d706f6882fe6, type: 3}}
  m_Name: 
  m_EditorClassIdentifier: 
--- !u!4 &{manager_id + 2}
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {manager_id}}}
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: 0, y: 0, z: 0}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: 0}}
  m_RootOrder: 2
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}"""
    
    def _create_theme_applier_yaml(self, applier_id: int) -> str:
        """Create ThemeApplier GameObject YAML"""
        return f"""--- !u!1 &{applier_id}
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: {applier_id + 2}}}
  - component: {{fileID: {applier_id + 1}}}
  m_Layer: 0
  m_Name: ThemeApplier
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!114 &{applier_id + 1}
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {applier_id}}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: themeapplier-script-guid, type: 3}}
  m_Name: 
  m_EditorClassIdentifier: 
--- !u!4 &{applier_id + 2}
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {applier_id}}}
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: 0, y: 0, z: 0}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: 0}}
  m_RootOrder: 3
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}"""
    
    def _create_gamemanager_yaml(self, manager_id: int) -> str:
        """Create SimpleGameManager GameObject YAML"""
        return f"""--- !u!1 &{manager_id}
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: {manager_id + 2}}}
  - component: {{fileID: {manager_id + 1}}}
  m_Layer: 0
  m_Name: SimpleGameManager
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!114 &{manager_id + 1}
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {manager_id}}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: a1b2c3d4e5f67890a1b2c3d4e5f67890, type: 3}}
  m_Name: 
  m_EditorClassIdentifier: 
--- !u!4 &{manager_id + 2}
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {manager_id}}}
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: 0, y: 0, z: 0}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: 0}}
  m_RootOrder: 4
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}"""
    
    def _create_scene_initializer_yaml(self, initializer_id: int) -> str:
        """Create SceneInitializer GameObject YAML to ensure WebGL initialization completes"""
        # GUID for SceneInitializer.cs: scene1n1t1a11zer0000000000000
        return f"""--- !u!1 &{initializer_id}
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: {initializer_id + 2}}}
  - component: {{fileID: {initializer_id + 1}}}
  m_Layer: 0
  m_Name: SceneInitializer
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!114 &{initializer_id + 1}
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {initializer_id}}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: scene1n1t1a11zer0000000000000, type: 3}}
  m_Name: 
  m_EditorClassIdentifier: 
--- !u!4 &{initializer_id + 2}
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {initializer_id}}}
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: 0, y: 0, z: 0}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: 0}}
  m_RootOrder: 5
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}"""
    
    def _create_light_yaml(self, light_id: int) -> str:
        """Create Unity directional light YAML"""
        return f"""--- !u!1 &{light_id}
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: {light_id + 2}}}
  - component: {{fileID: {light_id + 1}}}
  m_Layer: 0
  m_Name: Directional Light
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!108 &{light_id + 1}
Light:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {light_id}}}
  m_Enabled: 1
  serializedVersion: 10
  m_Type: 1
  m_Shape: 0
  m_Color: {{r: 1, g: 0.95686275, b: 0.8392157, a: 1}}
  m_Intensity: 2
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
  m_Cookie: {{fileID: 0}}
  m_DrawHalo: 0
  m_Flare: {{fileID: 0}}
  m_RenderMode: 0
  m_CullingMask:
    serializedVersion: 2
    m_Bits: 4294967295
  m_RenderingLayerMask: 1
  m_Lightmapping: 1
  m_AreaSize: {{x: 1, y: 1}}
  m_BounceIntensity: 1
  m_ColorTemperature: 6570
  m_UseColorTemperature: 0
  m_ShadowRadius: 0
  m_ShadowAngle: 0
--- !u!4 &{light_id + 2}
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {light_id}}}
  m_LocalRotation: {{x: 0.40821788, y: -0.23456968, z: 0.10938163, w: 0.8754261}}
  m_LocalPosition: {{x: 0, y: 3, z: 0}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: 0}}
  m_RootOrder: 1
  m_LocalEulerAnglesHint: {{x: 50, y: -30, z: 0}}"""
    
    def _create_game_object_yaml(self, obj_id: int, obj_spec: GameObjectSpec) -> str:
        """Create Unity game object YAML"""
        pos = obj_spec.position or {"x": 0, "y": 0, "z": 0}
        rot = obj_spec.rotation or {"x": 0, "y": 0, "z": 0}
        scale = obj_spec.scale or {"x": 1, "y": 1, "z": 1}
        
        # Convert Euler angles to quaternion
        quat = self._euler_to_quaternion(rot['x'], rot['y'], rot['z'])
        
        # Get mesh reference based on type
        mesh_ref = self._get_mesh_reference(obj_spec.type)
        
        # Get material color
        color = obj_spec.material_color or {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0}
        
        # Material ID for this object
        mat_id = obj_id + 5
        
        return f"""--- !u!1 &{obj_id}
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: {obj_id + 4}}}
  - component: {{fileID: {obj_id + 3}}}
  - component: {{fileID: {obj_id + 2}}}
  - component: {{fileID: {obj_id + 1}}}
  m_Layer: 0
  m_Name: {obj_spec.name}
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!65 &{obj_id + 1}
BoxCollider:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {obj_id}}}
  m_Material: {{fileID: 0}}
  m_IsTrigger: 0
  m_Enabled: 1
  serializedVersion: 2
  m_Size: {{x: 1, y: 1, z: 1}}
  m_Center: {{x: 0, y: 0, z: 0}}
--- !u!23 &{obj_id + 2}
MeshRenderer:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {obj_id}}}
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
  - {{fileID: {mat_id}}}
--- !u!21 &{mat_id}
Material:
  serializedVersion: 8
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_Name: {obj_spec.name}Material
  m_Shader: {{fileID: 46, guid: 0000000000000000f000000000000000, type: 0}}
  m_Parent: {{fileID: 0}}
  m_ModifiedSerializedProperties: 0
  m_ValidKeywords: []
  m_InvalidKeywords: []
  m_LightmapFlags: 4
  m_EnableInstancingVariants: 0
  m_DoubleSidedGI: 0
  m_CustomRenderQueue: -1
  stringTagMap: {{}}
  disabledShaderPasses: []
  m_LockedProperties: 
  m_SavedProperties:
    serializedVersion: 3
    m_TexEnvs:
    - _MainTex:
        m_Texture: {{fileID: 0}}
        m_Scale: {{x: 1, y: 1}}
        m_Offset: {{x: 0, y: 0}}
    m_Ints: []
    m_Floats:
    - _Glossiness: 0.5
    - _Metallic: 0
    m_Colors:
    - _Color: {{r: {color['r']}, g: {color['g']}, b: {color['b']}, a: {color['a']}}}
  m_StaticBatchInfo:
    firstSubMesh: 0
    subMeshCount: 0
  m_StaticBatchRoot: {{fileID: 0}}
  m_ProbeAnchor: {{fileID: 0}}
  m_LightProbeVolumeOverride: {{fileID: 0}}
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
  m_LightmapParameters: {{fileID: 0}}
  m_SortingLayerID: 0
  m_SortingLayer: 0
  m_SortingOrder: 0
  m_AdditionalVertexStreams: {{fileID: 0}}
--- !u!33 &{obj_id + 3}
MeshFilter:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {obj_id}}}
  m_Mesh: {{{mesh_ref}}}
--- !u!4 &{obj_id + 4}
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {obj_id}}}
  m_LocalRotation: {{x: {quat['x']}, y: {quat['y']}, z: {quat['z']}, w: {quat['w']}}}
  m_LocalPosition: {{x: {pos['x']}, y: {pos['y']}, z: {pos['z']}}}
  m_LocalScale: {{x: {scale['x']}, y: {scale['y']}, z: {scale['z']}}}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: 0}}
  m_RootOrder: 2
  m_LocalEulerAnglesHint: {{x: {rot['x']}, y: {rot['y']}, z: {rot['z']}}}"""
    
    def _get_mesh_reference(self, obj_type: str) -> str:
        """Get Unity built-in mesh reference"""
        mesh_refs = {
            "Cube": "fileID: 10202, guid: 0000000000000000e000000000000000, type: 0",
            "Sphere": "fileID: 10207, guid: 0000000000000000e000000000000000, type: 0", 
            "Capsule": "fileID: 10208, guid: 0000000000000000e000000000000000, type: 0",
            "Cylinder": "fileID: 10206, guid: 0000000000000000e000000000000000, type: 0",
            "Plane": "fileID: 10209, guid: 0000000000000000e000000000000000, type: 0",
            "Quad": "fileID: 10210, guid: 0000000000000000e000000000000000, type: 0"
        }
        return mesh_refs.get(obj_type, mesh_refs["Cube"])
    
    def _create_game_scripts(self, project_dir: Path, scripts: List[str]):
        """Create game scripts"""
        scripts_dir = project_dir / "Assets" / "Scripts"
        
        for script in scripts:
            # For now, create basic placeholder scripts
            # In production, this would parse script specifications
            script_content = f"""using UnityEngine;

public class {script} : MonoBehaviour
{{
    void Start()
    {{
        Debug.Log("{script} started");
    }}
    
    void Update()
    {{
        // Game logic here
    }}
}}
"""
            (scripts_dir / f"{script}.cs").write_text(script_content)