#!/usr/bin/env python3
"""
End-to-End API Tests for Unity MCP Build Service
Tests all API endpoints with real requests
"""

import requests
import time
import sys
import json
from typing import Dict, Any, Optional

class UnityMCPAPITester:
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.test_results = []
        
    def log_result(self, test_name: str, passed: bool, message: str = ""):
        result = "✅ PASS" if passed else "❌ FAIL"
        print(f"{result}: {test_name}")
        if message:
            print(f"        {message}")
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "message": message
        })
        
    def test_root_endpoint(self) -> bool:
        print("\n--- Test 1: Root Endpoint (/) ---")
        try:
            response = requests.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                self.log_result("Root endpoint", True, f"Service: {data.get('service')}")
                return True
            else:
                self.log_result("Root endpoint", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Root endpoint", False, str(e))
            return False
            
    def test_health_endpoint(self) -> bool:
        print("\n--- Test 2: Health Check (/health) ---")
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                self.log_result("Health check", True, f"Status: {data.get('status')}")
                return True
            else:
                self.log_result("Health check", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Health check", False, str(e))
            return False
            
    def test_themes_endpoint(self) -> bool:
        print("\n--- Test 3: List Themes (/themes) ---")
        try:
            response = requests.get(f"{self.base_url}/themes")
            if response.status_code == 200:
                data = response.json()
                themes = data.get('themes', [])
                theme_names = [str(t.get('id', '')) if isinstance(t, dict) else str(t) for t in themes]
                self.log_result("List themes", True, f"Found {len(themes)} themes: {', '.join(theme_names)}")
                return True
            else:
                self.log_result("List themes", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("List themes", False, str(e))
            return False
            
    def test_status_endpoint_with_auth(self) -> bool:
        print("\n--- Test 4: Service Status with Auth (/status) ---")
        try:
            response = requests.get(f"{self.base_url}/status", headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                self.log_result("Service status (authenticated)", True, 
                              f"Builds: {data.get('total_builds', 'N/A')}")
                return True
            else:
                self.log_result("Service status (authenticated)", False, 
                              f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Service status (authenticated)", False, str(e))
            return False
            
    def test_status_endpoint_without_auth(self) -> bool:
        print("\n--- Test 5: Service Status without Auth (should fail) ---")
        try:
            response = requests.get(f"{self.base_url}/status")
            if response.status_code == 401 or response.status_code == 403:
                self.log_result("Auth required for /status", True, 
                              "Correctly rejected unauthenticated request")
                return True
            else:
                self.log_result("Auth required for /status", False, 
                              f"Expected 401/403, got {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Auth required for /status", False, str(e))
            return False
            
    def test_build_creation_invalid_auth(self) -> bool:
        print("\n--- Test 6: Build Creation with Invalid Auth (should fail) ---")
        try:
            invalid_headers = {
                "Authorization": "Bearer invalid-key-12345",
                "Content-Type": "application/json"
            }
            build_data = {
                "user_id": "test-user",
                "game_id": "test-game",
                "game_name": "Test Game"
            }
            response = requests.post(
                f"{self.base_url}/build",
                headers=invalid_headers,
                json=build_data
            )
            if response.status_code == 401 or response.status_code == 403:
                self.log_result("Invalid auth rejected", True, 
                              "Correctly rejected invalid API key")
                return True
            else:
                self.log_result("Invalid auth rejected", False, 
                              f"Expected 401/403, got {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Invalid auth rejected", False, str(e))
            return False
            
    def test_build_creation_missing_fields(self) -> bool:
        print("\n--- Test 7: Build Creation with Missing Required Fields ---")
        try:
            build_data = {
                "game_name": "Test Game"
            }
            response = requests.post(
                f"{self.base_url}/build",
                headers=self.headers,
                json=build_data
            )
            if response.status_code == 422:
                self.log_result("Missing fields validation", True, 
                              "Correctly rejected incomplete request")
                return True
            else:
                self.log_result("Missing fields validation", False, 
                              f"Expected 422, got {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Missing fields validation", False, str(e))
            return False
            
    def test_build_creation_and_status(self) -> Optional[str]:
        print("\n--- Test 8: Build Creation and Status Check ---")
        try:
            build_data = {
                "user_id": "e2e-test-user",
                "game_id": f"e2e-test-{int(time.time())}",
                "game_name": "E2E Test Game",
                "theme": "city",
                "game_type": "platformer"
            }
            
            response = requests.post(
                f"{self.base_url}/build",
                headers=self.headers,
                json=build_data
            )
            
            if response.status_code == 200:
                data = response.json()
                build_id = data.get('build_id')
                
                if not build_id:
                    self.log_result("Build creation", False, "No build_id in response")
                    return None
                    
                self.log_result("Build creation", True, f"Build ID: {build_id}")
                
                time.sleep(2)
                
                status_response = requests.get(
                    f"{self.base_url}/build/{build_id}/status",
                    headers=self.headers
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    self.log_result("Build status check", True, 
                                  f"Status: {status_data.get('status')}, Progress: {status_data.get('progress')}%")
                    return build_id
                else:
                    self.log_result("Build status check", False, 
                                  f"Status: {status_response.status_code}")
                    return build_id
            else:
                error_detail = response.json().get('detail', 'Unknown error')
                self.log_result("Build creation", False, 
                              f"Status: {response.status_code}, Detail: {error_detail}")
                return None
                
        except Exception as e:
            self.log_result("Build creation", False, str(e))
            return None
            
    def test_build_status_not_found(self) -> bool:
        print("\n--- Test 9: Build Status for Non-existent Build ---")
        try:
            fake_build_id = "00000000-0000-0000-0000-000000000000"
            response = requests.get(
                f"{self.base_url}/build/{fake_build_id}/status",
                headers=self.headers
            )
            
            if response.status_code == 404:
                self.log_result("Build not found handling", True, 
                              "Correctly returned 404 for non-existent build")
                return True
            else:
                self.log_result("Build not found handling", False, 
                              f"Expected 404, got {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Build not found handling", False, str(e))
            return False
            
    def test_build_stop(self, build_id: Optional[str]) -> bool:
        print("\n--- Test 10: Build Stop ---")
        if not build_id:
            self.log_result("Build stop", False, "No build_id available to test")
            return False
            
        try:
            response = requests.put(
                f"{self.base_url}/build/{build_id}/stop",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Build stop", True, 
                              f"Status: {data.get('status', 'stopped')}")
                return True
            else:
                self.log_result("Build stop", False, 
                              f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Build stop", False, str(e))
            return False
            
    def test_theme_variations(self) -> bool:
        print("\n--- Test 11: Build Creation with Different Themes ---")
        themes = ["city", "farm", "space"]
        all_passed = True
        
        for theme in themes:
            try:
                build_data = {
                    "user_id": "e2e-theme-test",
                    "game_id": f"theme-test-{theme}-{int(time.time())}",
                    "game_name": f"Theme Test {theme}",
                    "theme": theme
                }
                
                response = requests.post(
                    f"{self.base_url}/build",
                    headers=self.headers,
                    json=build_data
                )
                
                if response.status_code == 200:
                    data = response.json()
                    build_id = data.get('build_id')
                    self.log_result(f"Theme '{theme}' build", True, f"Build ID: {build_id}")
                    
                    requests.put(
                        f"{self.base_url}/build/{build_id}/stop",
                        headers=self.headers
                    )
                else:
                    self.log_result(f"Theme '{theme}' build", False, 
                                  f"Status: {response.status_code}")
                    all_passed = False
                    
                time.sleep(1)
                
            except Exception as e:
                self.log_result(f"Theme '{theme}' build", False, str(e))
                all_passed = False
                
        return all_passed
        
    def test_build_with_interactive_objects(self) -> bool:
        print("\n--- Test 12: Build with Interactive Objects ---")
        try:
            build_data = {
                "user_id": "e2e-objects-test",
                "game_id": f"objects-test-{int(time.time())}",
                "game_name": "Interactive Objects Test",
                "theme": "city",
                "interactive_objects": [
                    {
                        "name": "TestCube",
                        "shape": "cube",
                        "position": {"x": 0, "y": 1, "z": 0},
                        "scale": {"x": 1, "y": 1, "z": 1},
                        "color": "#FF5733"
                    },
                    {
                        "name": "TestSphere",
                        "shape": "sphere",
                        "position": {"x": 2, "y": 1, "z": 0},
                        "scale": {"x": 0.5, "y": 0.5, "z": 0.5},
                        "color": "#33FF57"
                    }
                ]
            }
            
            response = requests.post(
                f"{self.base_url}/build",
                headers=self.headers,
                json=build_data
            )
            
            if response.status_code == 200:
                data = response.json()
                build_id = data.get('build_id')
                self.log_result("Build with interactive objects", True, 
                              f"Build ID: {build_id}")
                
                requests.put(
                    f"{self.base_url}/build/{build_id}/stop",
                    headers=self.headers
                )
                return True
            else:
                self.log_result("Build with interactive objects", False, 
                              f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Build with interactive objects", False, str(e))
            return False
            
    def run_all_tests(self):
        print("\n" + "=" * 60)
        print("Unity MCP Build Service - End-to-End API Tests")
        print("=" * 60)
        print(f"Base URL: {self.base_url}")
        print(f"API Key: {self.api_key[:10]}...")
        print("=" * 60)
        
        self.test_root_endpoint()
        self.test_health_endpoint()
        self.test_themes_endpoint()
        self.test_status_endpoint_with_auth()
        self.test_status_endpoint_without_auth()
        self.test_build_creation_invalid_auth()
        self.test_build_creation_missing_fields()
        
        build_id = self.test_build_creation_and_status()
        
        self.test_build_status_not_found()
        
        if build_id:
            time.sleep(3)
            self.test_build_stop(build_id)
            
        self.test_theme_variations()
        self.test_build_with_interactive_objects()
        
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        
        passed = sum(1 for r in self.test_results if r['passed'])
        failed = sum(1 for r in self.test_results if not r['passed'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        if failed > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("=" * 60)
        
        return failed == 0

def main():
    if len(sys.argv) < 3:
        print("Usage: python test_api_e2e.py <base_url> <api_key>")
        print("Example: python test_api_e2e.py http://35.226.93.88 013e283d...")
        sys.exit(1)
        
    base_url = sys.argv[1]
    api_key = sys.argv[2]
    
    tester = UnityMCPAPITester(base_url, api_key)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
