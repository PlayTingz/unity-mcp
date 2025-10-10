#!/usr/bin/env python3
"""
Setup Shared Unity Project
Creates the shared Unity project structure that all builds will use
"""

import os
import sys
import json
import uuid
from pathlib import Path

def create_shared_project():
    """Create the shared Unity project at /opt/unity-mcp/shared-project"""
    
    shared_project_path = Path("/opt/unity-mcp/shared-project")
    
    print(f"Creating shared Unity project at: {shared_project_path}")
    
    # Create directory structure
    directories = [
        "Assets/Scenes",
        "Assets/Scripts",
        "Assets/Materials",
        "Assets/Editor",
        "ProjectSettings",
        "Packages"
    ]
    
    for directory in directories:
        dir_path = shared_project_path / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created {directory}")
    
    # Create Packages/manifest.json
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
    (shared_project_path / "Packages" / "manifest.json").write_text(json.dumps(manifest_content, indent=2))
    print(f"  ✓ Created Packages/manifest.json")
    
    # Create ProjectVersion.txt
    version_content = """m_EditorVersion: 2022.3.45f1
m_EditorVersionWithRevision: 2022.3.45f1 (e5503b4cfcf4)
"""
    (shared_project_path / "ProjectSettings" / "ProjectVersion.txt").write_text(version_content)
    print(f"  ✓ Created ProjectSettings/ProjectVersion.txt")
    
    # Create basic ProjectSettings.asset
    project_guid = str(uuid.uuid4()).replace('-', '')
    settings_content = f"""%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!129 &1
PlayerSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 23
  productGUID: {project_guid}
  companyName: Unity MCP Games
  productName: SharedProject
  defaultCursor: {{fileID: 0}}
  cursorHotspot: {{x: 0, y: 0}}
  m_SplashScreenBackgroundColor: {{r: 0.13725491, g: 0.12156863, b: 0.1254902, a: 1}}
  m_ShowUnitySplashScreen: 0
  m_ShowUnitySplashLogo: 0
  bundleVersion: 1.0.0
  WebGL:
    template: APPLICATION:Default
    useEmbeddedResources: 0
    compressionFormat: 1
    nameFilesAsHashes: 0
    dataCaching: 1
    linkerTarget: 1
    exceptionSupport: 1
    memorySize: 256
"""
    (shared_project_path / "ProjectSettings" / "ProjectSettings.asset").write_text(settings_content)
    print(f"  ✓ Created ProjectSettings/ProjectSettings.asset")
    
    # Create SimpleGameManager.cs script
    simple_gm_content = """using UnityEngine;

public class SimpleGameManager : MonoBehaviour
{
    void Start()
    {
        Debug.Log("=== GAME STARTED ===");
        Debug.Log("SimpleGameManager initialized");
    }
    
    void Update()
    {
        // Keep game loop running
    }
}
"""
    (shared_project_path / "Assets" / "Scripts" / "SimpleGameManager.cs").write_text(simple_gm_content)
    print(f"  ✓ Created Assets/Scripts/SimpleGameManager.cs")
    
    # Create SimpleGameManager.cs.meta with the GUID used in scenes
    meta_content = """fileFormatVersion: 2
guid: a1b2c3d4e5f67890a1b2c3d4e5f67890
MonoImporter:
  externalObjects: {}
  serializedVersion: 2
  defaultReferences: []
  executionOrder: 0
  icon: {instanceID: 0}
  userData: 
  assetBundleName: 
  assetBundleVariant: 
"""
    (shared_project_path / "Assets" / "Scripts" / "SimpleGameManager.cs.meta").write_text(meta_content)
    print(f"  ✓ Created Assets/Scripts/SimpleGameManager.cs.meta")
    
    # Create BuildScript.cs that reads from EditorBuildSettings
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
        return args.Contains(name);
    }
}
"""
    (shared_project_path / "Assets" / "Editor" / "BuildScript.cs").write_text(build_script_content)
    print(f"  ✓ Created Assets/Editor/BuildScript.cs")
    
    # Create BuildScript.cs.meta
    build_script_meta = """fileFormatVersion: 2
guid: b1d5c27f89abcdef0123456789abcdef
MonoImporter:
  externalObjects: {}
  serializedVersion: 2
  defaultReferences: []
  executionOrder: 0
  icon: {instanceID: 0}
  userData: 
  assetBundleName: 
  assetBundleVariant: 
"""
    (shared_project_path / "Assets" / "Editor" / "BuildScript.cs.meta").write_text(build_script_meta)
    print(f"  ✓ Created Assets/Editor/BuildScript.cs.meta")
    
    # Create empty EditorBuildSettings.asset (will be updated per build)
    build_settings_content = """%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!1045 &1
EditorBuildSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 2
  m_Scenes: []
  m_configObjects: {}
"""
    (shared_project_path / "ProjectSettings" / "EditorBuildSettings.asset").write_text(build_settings_content)
    print(f"  ✓ Created ProjectSettings/EditorBuildSettings.asset")
    
    print(f"\n✅ Shared Unity project created successfully at {shared_project_path}")
    print(f"\nNext steps:")
    print(f"  1. Import CityThemePackage if needed")
    print(f"  2. Test a build with the updated code")

if __name__ == "__main__":
    create_shared_project()
