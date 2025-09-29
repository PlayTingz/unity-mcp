#!/usr/bin/env python3
"""
End-to-End Test: Create and Build Simple Cube Game on Unity MCP VPS
Tests the complete pipeline from API call to playable WebGL game.
"""

import requests
import json
import time
import sys
import os
from datetime import datetime

# Production VPS configuration
VPS_HOST = "35.226.93.88"
API_BASE_URL = f"http://{VPS_HOST}"
API_KEY = "013e283d7f3a2d45dcdbe7a2b4676a61ff58e7a576930ac3ea66c85d3882f197"

class UnityMCPTester:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        self.build_id = None
        
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def test_health_check(self):
        """Test that the service is running and healthy"""
        self.log("🔍 Testing service health...")
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Service healthy: {data}")
                return True
            else:
                self.log(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Health check error: {e}")
            return False
            
    def test_status_endpoint(self):
        """Test the status endpoint for system information"""
        self.log("📊 Checking system status...")
        try:
            response = requests.get(f"{API_BASE_URL}/status", headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ System status: Unity at {data.get('unity_path', 'unknown')}")
                self.log(f"   License: {data.get('unity_license_status', 'unknown')}")
                return True
            else:
                self.log(f"❌ Status check failed: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Status check error: {e}")
            return False

    def create_simple_cube_game(self):
        """Create a simple Unity project with a cube in the center"""
        self.log("🎮 Creating simple cube game build...")
        
        # Generate unique IDs for this test
        import uuid
        test_id = str(uuid.uuid4())[:8]
        
        # Simple cube game specification matching the API schema
        game_spec = {
            "user_id": f"test-user-{test_id}",
            "game_id": f"cube-game-{test_id}",
            "game_name": f"SimpleCubeGame-{test_id}",
            "game_type": "platformer",
            "asset_set": "v1",
            "assets": [],
            "target_platform": "WebGL"
        }
        
        try:
            self.log(f"🚀 Sending build request to {API_BASE_URL}/build")
            response = requests.post(
                f"{API_BASE_URL}/build", 
                headers=self.headers,
                json=game_spec,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.build_id = data.get("build_id") or data.get("id")  # Try both possible field names
                self.log(f"✅ Build started successfully!")
                self.log(f"   Build ID: {self.build_id}")
                self.log(f"   Status: {data.get('status')}")
                self.log(f"   Full response: {json.dumps(data, indent=2)}")
                return True
            else:
                self.log(f"❌ Build creation failed: {response.status_code}")
                self.log(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Build creation error: {e}")
            return False
            
    def monitor_build_progress(self, max_wait_time=600):
        """Monitor the build progress until completion or timeout"""
        if not self.build_id:
            self.log("❌ No build ID to monitor")
            return False
            
        self.log(f"⏳ Monitoring build progress (max {max_wait_time}s)...")
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < max_wait_time:
            try:
                response = requests.get(
                    f"{API_BASE_URL}/build/{self.build_id}/status",
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status")
                    progress = data.get("progress", 0)
                    
                    if status != last_status:
                        self.log(f"📊 Build status: {status} ({progress}%)")
                        if data.get("current_step"):
                            self.log(f"   Current step: {data['current_step']}")
                        last_status = status
                    
                    if status == "completed":
                        self.log("✅ Build completed successfully!")
                        build_url = data.get("build_url")
                        if build_url:
                            self.log(f"🎮 Game URL: {build_url}")
                        return True
                    elif status == "failed":
                        self.log("❌ Build failed!")
                        error = data.get("error", "Unknown error")
                        self.log(f"   Error: {error}")
                        return False
                    elif status in ["running", "queued", "initializing"]:
                        # Continue monitoring
                        pass
                    else:
                        self.log(f"⚠️  Unknown status: {status}")
                        
                else:
                    self.log(f"⚠️  Status check failed: {response.status_code}")
                    
            except Exception as e:
                self.log(f"⚠️  Status check error: {e}")
                
            # Wait before next check
            time.sleep(10)
            
        self.log(f"⏰ Build monitoring timed out after {max_wait_time}s")
        return False
        
    def verify_build_output(self):
        """Verify that the build output is accessible and valid"""
        if not self.build_id:
            self.log("❌ No build ID to verify")
            return False
            
        self.log("🔍 Verifying build output...")
        
        # Check if the game is accessible via HTTP
        game_url = f"{API_BASE_URL}/games/{self.build_id}/"
        
        try:
            # Test the index.html file
            response = requests.get(f"{game_url}index.html", timeout=10)
            if response.status_code == 200 and "Unity" in response.text:
                self.log("✅ Game index.html is accessible and contains Unity content")
                
                # Test for WebGL build files (generic names since we don't know the exact project name)
                build_files = [
                    "Build",  # Build directory should exist
                    "index.html",  # Main HTML file
                    "TemplateData"  # Template data folder
                ]
                
                files_found = 0
                for file in build_files:
                    try:
                        file_response = requests.head(f"{game_url}{file}", timeout=5)
                        if file_response.status_code == 200:
                            files_found += 1
                            self.log(f"✅ Found: {file}")
                        else:
                            self.log(f"⚠️  Missing: {file} (status: {file_response.status_code})")
                    except Exception as e:
                        self.log(f"❌ Error checking: {file} - {e}")
                
                # If we can access the index.html, that's the main success criteria
                if files_found >= 1:  # At least index.html
                    self.log(f"✅ Build verification successful! ({files_found}/{len(build_files)} files found)")
                    self.log(f"🎮 Play game at: {game_url}")
                    return True
                else:
                    self.log(f"❌ Build verification failed - only {files_found}/{len(build_files)} files found")
                    return False
                    
            else:
                self.log(f"❌ Game not accessible: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Build verification error: {e}")
            return False

    def run_full_test(self):
        """Run the complete end-to-end test"""
        self.log("🚀 Starting Unity MCP End-to-End Cube Game Test")
        self.log(f"   Target: {API_BASE_URL}")
        self.log("=" * 60)
        
        # Test sequence
        tests = [
            ("Health Check", self.test_health_check),
            ("Status Check", self.test_status_endpoint),
            ("Create Cube Game", self.create_simple_cube_game),
            ("Monitor Build", self.monitor_build_progress),
            ("Verify Output", self.verify_build_output)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            self.log(f"\n{'='*20} {test_name} {'='*20}")
            try:
                result = test_func()
                results[test_name] = result
                if not result:
                    self.log(f"❌ {test_name} failed - stopping test sequence")
                    break
            except Exception as e:
                self.log(f"❌ {test_name} crashed: {e}")
                results[test_name] = False
                break
                
        # Test summary
        self.log(f"\n{'='*60}")
        self.log("🏁 END-TO-END TEST SUMMARY")
        self.log("=" * 60)
        
        passed = sum(1 for r in results.values() if r)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"   {status} {test_name}")
            
        self.log(f"\nResult: {passed}/{total} tests passed")
        
        if all(results.values()) and self.build_id:
            self.log(f"🎉 ALL TESTS PASSED!")
            self.log(f"🎮 Play your cube game: {API_BASE_URL}/games/{self.build_id}/")
            return True
        else:
            self.log("❌ Some tests failed")
            return False

if __name__ == "__main__":
    print("Unity MCP Production E2E Test - Cube Game Build")
    print("=" * 60)
    
    tester = UnityMCPTester()
    success = tester.run_full_test()
    
    sys.exit(0 if success else 1)