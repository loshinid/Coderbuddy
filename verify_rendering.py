#!/usr/bin/env python3
"""
Test script to verify HTML rendering vs download behavior
"""

import requests
import json

def test_html_rendering():
    """Test that HTML is rendered properly, not downloaded."""
    try:
        response = requests.get("http://localhost:8000/")
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'Not set')}")
        print(f"Content-Disposition: {response.headers.get('content-disposition', 'Not set')}")
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '').lower()
            content_disposition = response.headers.get('content-disposition', '').lower()
            
            # Check if content is HTML
            if 'text/html' in content_type:
                print("✅ Content-Type is correct: text/html")
            else:
                print(f"❌ Wrong Content-Type: {content_type}")
            
            # Check if browser should download instead of render
            if 'attachment' in content_disposition:
                print("❌ Content-Disposition indicates download, not render")
                return False
            else:
                print("✅ No attachment in Content-Disposition")
            
            # Check content
            content = response.text
            if '<!DOCTYPE html>' in content and 'CoderBuddy' in content:
                print("✅ HTML content is correct")
                print(f"Content length: {len(content)} characters")
                return True
            else:
                print("❌ Content is not valid HTML")
                print(f"Content preview: {content[:200]}...")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_static_files():
    """Test that static files are accessible."""
    static_files = [
        "/static/styles.css",
        "/static/script.js"
    ]
    
    results = []
    for file_path in static_files:
        try:
            response = requests.get(f"http://localhost:8000{file_path}")
            print(f"\n--- Testing {file_path} ---")
            print(f"Status: {response.status_code}")
            print(f"Content-Type: {response.headers.get('content-type', 'Not set')}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                
                if file_path.endswith('.css') and 'text/css' in content_type:
                    print("✅ CSS file served correctly")
                    results.append(True)
                elif file_path.endswith('.js') and 'application/javascript' in content_type:
                    print("✅ JS file served correctly")
                    results.append(True)
                else:
                    print(f"❌ Wrong Content-Type for {file_path}: {content_type}")
                    results.append(False)
            else:
                print(f"❌ Failed to serve {file_path}")
                results.append(False)
                
        except Exception as e:
            print(f"❌ Error testing {file_path}: {e}")
            results.append(False)
    
    return all(results)

def main():
    """Run all rendering tests."""
    print("=== HTML Rendering Test ===\n")
    
    # Test main HTML rendering
    html_ok = test_html_rendering()
    
    print("\n=== Static Files Test ===")
    static_ok = test_static_files()
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"HTML Rendering: {'PASS' if html_ok else 'FAIL'}")
    print(f"Static Files: {'PASS' if static_ok else 'FAIL'}")
    
    if html_ok and static_ok:
        print("\n🎉 All tests passed! Frontend is rendering correctly.")
        print("\n📍 Open http://localhost:8000 in your browser")
    else:
        print("\n❌ Some tests failed. Check the issues above.")
    
    return html_ok and static_ok

if __name__ == "__main__":
    main()
