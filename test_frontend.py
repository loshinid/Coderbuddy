#!/usr/bin/env python3
"""
Test script to verify frontend serving and API functionality
"""

import requests
import json
import time

def test_frontend_serving():
    """Test that the frontend HTML is served correctly."""
    try:
        response = requests.get("http://localhost:8000/")
        print(f"Frontend test: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            # Check if it's HTML content
            if '<!DOCTYPE html>' in content and 'CoderBuddy' in content:
                print("✓ Frontend HTML served correctly")
                return True
            else:
                print("✗ Response is not HTML frontend")
                print(f"Content preview: {content[:200]}...")
                return False
        else:
            print(f"✗ Failed to serve frontend: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Frontend test failed: {e}")
        return False

def test_static_files():
    """Test that static CSS and JS files are accessible."""
    files_to_test = [
        "/static/styles.css",
        "/static/script.js"
    ]
    
    results = {}
    for file_path in files_to_test:
        try:
            response = requests.get(f"http://localhost:8000{file_path}")
            results[file_path] = response.status_code == 200
            print(f"{file_path}: {response.status_code} {'✓' if response.status_code == 200 else '✗'}")
        except Exception as e:
            results[file_path] = False
            print(f"{file_path}: ✗ Error - {e}")
    
    return all(results.values())

def test_api_endpoints():
    """Test API endpoints."""
    endpoints = [
        "/health",
        "/api/info"
    ]
    
    results = {}
    for endpoint in endpoints:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}")
            results[endpoint] = response.status_code == 200
            print(f"API {endpoint}: {response.status_code} {'✓' if response.status_code == 200 else '✗'}")
            if response.status_code == 200:
                print(f"  Response: {response.json()}")
        except Exception as e:
            results[endpoint] = False
            print(f"API {endpoint}: ✗ Error - {e}")
    
    return all(results.values())

def test_website_generation():
    """Test website generation functionality."""
    try:
        payload = {
            "prompt": "Create a simple landing page with a hero section",
            "model": "llama-3.3-70b-versatile"
        }
        
        print("Testing website generation...")
        response = requests.post(
            "http://localhost:8000/generate",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Generation API: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('success')}")
            if result.get('success'):
                print(f"Project: {result.get('project_name')}")
                print(f"Files: {result.get('total_files')}")
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

def test_generated_preview():
    """Test that generated websites can be previewed."""
    try:
        response = requests.get("http://localhost:8000/generated/index.html")
        print(f"Generated preview: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            if '<html' in content.lower():
                print("✓ Generated website preview works")
                return True
            else:
                print("✗ Generated preview is not HTML")
                return False
        else:
            print("✗ No generated website to preview (expected if no generation yet)")
            return False
    except Exception as e:
        print(f"Generated preview test: {e}")
        return False

def main():
    """Run all frontend tests."""
    print("=== CoderBuddy Frontend & API Test ===\n")
    
    tests = [
        ("Frontend Serving", test_frontend_serving),
        ("Static Files", test_static_files),
        ("API Endpoints", test_api_endpoints),
        ("Website Generation", test_website_generation),
        ("Generated Preview", test_generated_preview)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        results[test_name] = test_func()
    
    # Summary
    print("\n=== Test Summary ===")
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All tests passed! Frontend is working correctly.")
        print("\n📍 Access the application at: http://localhost:8000")
        print("📍 API docs at: http://localhost:8000/docs")
    else:
        print("\n❌ Some tests failed. Check the logs above.")
    
    return all_passed

if __name__ == "__main__":
    main()
