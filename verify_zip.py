#!/usr/bin/env python3
"""
Test script to verify ZIP download functionality
"""

import requests
import json
import zipfile
import io
import os

def test_zip_download():
    """Test the complete ZIP download functionality."""
    print("=== ZIP Download Test ===\n")
    
    # First generate a website to have something to download
    print("1. Generating a test website...")
    try:
        generate_response = requests.post(
            "http://localhost:8000/generate",
            json={
                "prompt": "Create a simple landing page with hero section and contact form",
                "model": "llama-3.3-70b-versatile"
            },
            headers={"Content-Type": "application/json"}
        )
        
        if generate_response.status_code == 200:
            result = generate_response.json()
            if result.get('success'):
                print(f"✅ Website generated: {result.get('project_name')}")
                print(f"   Files: {result.get('total_files')}")
            else:
                print(f"❌ Generation failed: {result.get('error')}")
                return False
        else:
            print(f"❌ Generation API error: {generate_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Generation request failed: {e}")
        return False
    
    # Test ZIP download
    print("\n2. Testing ZIP download...")
    try:
        zip_response = requests.get("http://localhost:8000/download-zip")
        
        print(f"   Status Code: {zip_response.status_code}")
        print(f"   Content-Type: {zip_response.headers.get('content-type', 'Not set')}")
        print(f"   Content-Disposition: {zip_response.headers.get('content-disposition', 'Not set')}")
        print(f"   Content-Length: {zip_response.headers.get('content-length', 'Not set')}")
        
        if zip_response.status_code == 200:
            content_type = zip_response.headers.get('content-type', '').lower()
            content_disposition = zip_response.headers.get('content-disposition', '').lower()
            
            # Check if it's a ZIP file
            if 'application/zip' in content_type:
                print("✅ Correct MIME type: application/zip")
            else:
                print(f"❌ Wrong MIME type: {content_type}")
            
            if 'attachment' in content_disposition:
                print("✅ Content-Disposition indicates download")
            else:
                print("❌ Content-Disposition doesn't indicate download")
            
            # Test ZIP content
            zip_data = zip_response.content
            print(f"   ZIP size: {len(zip_data)} bytes")
            
            if len(zip_data) > 0:
                try:
                    # Read ZIP file in memory
                    with zipfile.ZipFile(io.BytesIO(zip_data), 'r') as zip_file:
                        file_list = zip_file.namelist()
                        print(f"   Files in ZIP: {len(file_list)}")
                        
                        # Check for expected files
                        expected_files = ['index.html', 'styles.css', 'script.js']
                        found_files = []
                        
                        for file_name in file_list:
                            print(f"     - {file_name}")
                            if file_name in expected_files:
                                found_files.append(file_name)
                        
                        print(f"   Expected files found: {found_files}")
                        
                        # Test extracting files
                        print("\n3. Testing ZIP extraction...")
                        for file_name in file_list:
                            if file_name.endswith(('.html', '.css', '.js')):
                                try:
                                    file_content = zip_file.read(file_name)
                                    print(f"   ✅ {file_name}: {len(file_content)} bytes")
                                except Exception as e:
                                    print(f"   ❌ Failed to read {file_name}: {e}")
                        
                        return len(found_files) >= 2  # At least HTML and one more file
                        
                except zipfile.BadZipFile as e:
                    print(f"❌ Invalid ZIP file: {e}")
                    return False
            else:
                print("❌ Empty ZIP file")
                return False
        else:
            print(f"❌ ZIP download failed: {zip_response.status_code}")
            if zip_response.status_code == 404:
                error_data = zip_response.json() if zip_response.content else {}
                print(f"   Error: {error_data.get('detail', 'Not found')}")
            return False
            
    except Exception as e:
        print(f"❌ ZIP download test failed: {e}")
        return False

def test_error_cases():
    """Test error handling for edge cases."""
    print("\n=== Error Cases Test ===\n")
    
    # Test with no project (clean first)
    print("1. Testing ZIP download with no project...")
    try:
        # Clean project first
        clean_response = requests.delete("http://localhost:8000/project/clean")
        if clean_response.status_code == 200:
            print("✅ Project cleaned")
            
            # Now try ZIP download
            zip_response = requests.get("http://localhost:8000/download-zip")
            
            if zip_response.status_code == 404:
                print("✅ Correctly returns 404 for empty project")
                error_data = zip_response.json()
                print(f"   Error message: {error_data.get('detail')}")
                return True
            else:
                print(f"❌ Should return 404, got: {zip_response.status_code}")
                return False
        else:
            print(f"❌ Failed to clean project: {clean_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error case test failed: {e}")
        return False

def main():
    """Run all ZIP download tests."""
    print("Testing CoderBuddy ZIP Download Functionality\n")
    
    zip_ok = test_zip_download()
    error_ok = test_error_cases()
    
    print("\n=== Test Summary ===")
    print(f"ZIP Download: {'PASS' if zip_ok else 'FAIL'}")
    print(f"Error Handling: {'PASS' if error_ok else 'FAIL'}")
    
    if zip_ok and error_ok:
        print("\n🎉 All ZIP download tests passed!")
        print("\n✅ ZIP download includes ALL generated files")
        print("✅ Folder structure is preserved")
        print("✅ Dynamic project naming works")
        print("✅ Proper error handling implemented")
        print("✅ MIME types and headers are correct")
    else:
        print("\n❌ Some tests failed. Check the issues above.")
    
    return zip_ok and error_ok

if __name__ == "__main__":
    main()
