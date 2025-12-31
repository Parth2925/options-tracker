#!/usr/bin/env python3
"""
Quick script to test if the backend is accessible
"""
import sys

try:
    import requests
    response = requests.get('http://localhost:5000/api/health', timeout=5)
    if response.status_code == 200:
        print("✓ Backend is running and accessible!")
        print(f"  Response: {response.json()}")
        sys.exit(0)
    else:
        print(f"✗ Backend returned status code: {response.status_code}")
        sys.exit(1)
except requests.exceptions.ConnectionError:
    print("✗ Backend is NOT running or not accessible on http://localhost:5000")
    print("  Please start the backend server first:")
    print("  cd backend && python app.py")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error checking backend: {e}")
    sys.exit(1)

