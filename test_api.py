#!/usr/bin/env python3
"""Test API category filtering"""
import time
import subprocess
import requests
import sys

# Start API server
print("🚀 Starting API server...")
proc = subprocess.Popen(
    ["python3", "api_server.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd="/Applications/Soft/n8n-workflows-main"
)

# Wait for server to start
print("⏳ Waiting for server to start...")
time.sleep(5)

try:
    # Test stats endpoint
    print("\n📊 Testing /api/stats endpoint...")
    resp = requests.get('http://127.0.0.1:8000/api/stats', timeout=5)
    stats = resp.json()
    print(f"✅ Total workflows: {stats['total']}")
    
    # Test category filter
    print("\n🔍 Testing category filter for 'AI Agent Development'...")
    resp = requests.get(
        'http://127.0.0.1:8000/api/workflows',
        params={'category': 'AI Agent Development', 'per_page': 2},
        timeout=5
    )
    
    if resp.status_code != 200:
        print(f"❌ Error: {resp.status_code}")
        print(f"Response: {resp.text}")
    else:
        data = resp.json()
        print(f"✅ Found {data.get('total', 0)} AI Agent Development workflows")
        
        # Show first couple
        workflows = data.get('workflows', [])
        print(f"   First workflow: {workflows[0]['name'] if workflows else 'None'}")
        
    # Test other categories
    print("\n🔍 Testing other category filters...")
    categories = [
        'Web Scraping & Data Extraction',
        'Data Processing & Analysis',
        'Communication & Messaging',
        'Uncategorized'
    ]
    
    for cat in categories:
        resp = requests.get(
            'http://127.0.0.1:8000/api/workflows',
            params={'category': cat, 'per_page': 1},
            timeout=5
        )
        data = resp.json()
        count = data.get('total', 0)
        print(f"   {cat}: {count} workflows")
        
    print("\n✨ All tests completed!")
    
finally:
    # Kill server
    print("\n🛑 Stopping API server...")
    proc.terminate()
    proc.wait(timeout=5)
    print("✅ Server stopped")
