#!/usr/bin/env python3
"""
Simple test script to verify CoderBuddy API functionality
"""

import requests
import json
import time

def test_health():
    """Test the health endpoint"""
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"Health check: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_generation():
    """Test the website generation endpoint"""
    try:
        payload = {
            "prompt": "Create a simple portfolio website with a dark theme",
            "model": "llama-3.3-70b-versatile"
        }
        
        print("Starting generation test...")
        start_time = time.time()
        
        response = requests.post(
            "http://localhost:8000/generate",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        generation_time = time.time() - start_time
        print(f"Generation completed in {generation_time:.2f}s")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('success')}")
            if result.get('success'):
                print(f"Project: {result.get('project_name')}")
                print(f"Files: {result.get('total_files')}")
                print(f"Generation time: {result.get('generation_time'):.2f}s")
                return True
            else:
                print(f"Error: {result.get('error')}")
                return False
        else:
            print(f"HTTP Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Generation test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=== CoderBuddy API Test ===\n")
    
    # Test health endpoint
    print("1. Testing health endpoint...")
    health_ok = test_health()
    print(f"Health check: {'✓' if health_ok else '✗'}\n")
    
    if not health_ok:
        print("Server not responding. Is the app running?")
        return
    
    # Test generation endpoint
    print("2. Testing generation endpoint...")
    generation_ok = test_generation()
    print(f"Generation test: {'✓' if generation_ok else '✗'}\n")
    
    # Summary
    print("=== Test Summary ===")
    print(f"Health Check: {'PASS' if health_ok else 'FAIL'}")
    print(f"Generation: {'PASS' if generation_ok else 'FAIL'}")
    
    if health_ok and generation_ok:
        print("\n🎉 All tests passed! The API is working correctly.")
    else:
        print("\n❌ Some tests failed. Check the logs above.")

if __name__ == "__main__":
    main()
