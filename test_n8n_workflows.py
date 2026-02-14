#!/usr/bin/env python3
"""
Test n8n workflows by attempting to import them using n8n CLI or API
"""
import json
import os
from pathlib import Path
import subprocess
import sys

def check_n8n_installation():
    """Check if n8n is installed"""
    try:
        result = subprocess.run(['n8n', '--version'], 
                              capture_output=True, 
                              text=True,
                              timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ n8n is installed: {version}\n")
            return True
        else:
            print("❌ n8n is not installed or not in PATH")
            return False
    except FileNotFoundError:
        print("❌ n8n command not found")
        return False
    except Exception as e:
        print(f"❌ Error checking n8n: {e}")
        return False

def check_n8n_running():
    """Check if n8n is running"""
    try:
        import requests
        response = requests.get('http://localhost:5678', timeout=2)
        print(f"✅ n8n is running on http://localhost:5678\n")
        return True
    except:
        print("⚠️  n8n is not running on http://localhost:5678")
        print("   You can start n8n with: n8n start\n")
        return False

def test_workflow_import(workflow_file):
    """Test if a workflow can be imported to n8n"""
    try:
        with open(workflow_file, 'r', encoding='utf-8') as f:
            workflow_data = json.load(f)
        
        # Basic validation
        if 'nodes' not in workflow_data or 'connections' not in workflow_data:
            return False, "Missing required fields"
        
        # Check if nodes is empty
        if not workflow_data['nodes']:
            return False, "No nodes defined"
        
        return True, "Valid structure"
    except Exception as e:
        return False, str(e)

def analyze_problematic_workflows():
    """Analyze the problematic workflows in detail"""
    problematic_file = Path('problematic_workflows.txt')
    
    if not problematic_file.exists():
        print("❌ Run validate_workflows.py first to generate problematic_workflows.txt")
        return
    
    print("="*80)
    print("🔍 DETAILED ANALYSIS OF PROBLEMATIC WORKFLOWS")
    print("="*80 + "\n")
    
    with open(problematic_file, 'r') as f:
        content = f.read()
    
    # Parse the file
    lines = [l.strip() for l in content.split('\n') if l.strip() and not l.startswith('#')]
    
    categories = {}
    current_category = None
    
    for line in content.split('\n'):
        if line.startswith('## '):
            current_category = line[3:].strip().rstrip(':')
            categories[current_category] = []
        elif line.strip() and not line.startswith('#') and current_category:
            categories[current_category].append(line.strip())
    
    # Analyze each category
    for category, files in categories.items():
        print(f"\n{'='*80}")
        print(f"📁 {category}")
        print(f"{'='*80}")
        print(f"Total files: {len(files)}\n")
        
        for idx, file_path in enumerate(files[:5], 1):  # Show first 5
            full_path = Path('workflows') / file_path
            if full_path.exists():
                print(f"{idx}. {file_path}")
                
                # Try to read and show first few lines
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read(500)  # First 500 chars
                    
                    # Check if it's valid JSON
                    try:
                        json.loads(content)
                        print("   ✓ Starts with valid JSON")
                    except:
                        print("   ✗ Invalid JSON format")
                        print(f"   First 200 chars: {content[:200]}")
                except Exception as e:
                    print(f"   Error reading: {e}")
                print()
        
        if len(files) > 5:
            print(f"... and {len(files) - 5} more files\n")

def suggest_fixes():
    """Suggest how to fix the problematic workflows"""
    print("\n" + "="*80)
    print("💡 SUGGESTED FIXES")
    print("="*80 + "\n")
    
    print("1. MISSING REQUIRED FIELDS:")
    print("   These workflows are corrupted or improperly formatted.")
    print("   They appear to have JSON syntax errors with escaped quotes.")
    print("   → Solution: These files need to be re-exported from n8n or manually fixed\n")
    
    print("2. DEPRECATED NODES:")
    print("   - readBinaryFile/writeBinaryFile/readBinaryFiles:")
    print("     → Use HTTP Request node or cloud storage (S3, Google Drive, etc.)")
    print("   - executeCommand:")
    print("     → Use Code node (Python/JavaScript) or specific service integrations")
    print("     → For cloud deployment, these nodes are disabled for security\n")
    
    print("3. NO TRIGGER NODES:")
    print("   Workflows without triggers can only be called manually or by other workflows")
    print("   → Add a trigger node if you want automatic execution:")
    print("     • Webhook - for HTTP triggers")
    print("     • Schedule/Cron - for time-based triggers")
    print("     • Email Trigger - for email-based triggers")
    print("     • Form Trigger - for form submissions\n")
    
    print("4. TESTING WITH N8N:")
    print("   To test these workflows:")
    print("   • Start n8n: n8n start")
    print("   • Import workflow via UI: Settings → Import from File")
    print("   • Or use n8n CLI: n8n import:workflow --input=<file>\n")

def create_fix_script():
    """Create a script to attempt automatic fixes"""
    fix_script = """#!/usr/bin/env python3
import json
import sys
from pathlib import Path

def fix_workflow(file_path):
    '''Attempt to fix common workflow issues'''
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to parse as-is
        try:
            data = json.loads(content)
            print(f"✓ {file_path} - Already valid JSON")
            return True
        except json.JSONDecodeError:
            # Attempt to fix escaped JSON
            # This is a corrupted format where the entire JSON is escaped
            print(f"✗ {file_path} - Attempting to fix...")
            
            # Create backup
            backup_path = file_path.with_suffix('.json.backup')
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"  Backup created: {backup_path}")
            print(f"  This file cannot be automatically fixed.")
            print(f"  It needs to be re-exported from n8n.")
            return False
            
    except Exception as e:
        print(f"✗ {file_path} - Error: {e}")
        return False

if __name__ == '__main__':
    problematic_file = Path('problematic_workflows.txt')
    
    if not problematic_file.exists():
        print("Run validate_workflows.py first")
        sys.exit(1)
    
    # Read problematic files
    with open(problematic_file, 'r') as f:
        lines = [l.strip() for l in f if l.strip() and not l.startswith('#') and not l.startswith('##')]
    
    print(f"Found {len(lines)} problematic workflows\\n")
    
    for file_rel_path in lines:
        file_path = Path('workflows') / file_rel_path
        if file_path.exists():
            fix_workflow(file_path)
"""
    
    with open('fix_workflows.py', 'w') as f:
        f.write(fix_script)
    
    os.chmod('fix_workflows.py', 0o755)
    print(f"💾 Created fix_workflows.py script\n")

def main():
    print("\n" + "="*80)
    print("🧪 N8N WORKFLOW TESTING UTILITY")
    print("="*80 + "\n")
    
    # Check n8n installation
    n8n_installed = check_n8n_installation()
    n8n_running = check_n8n_running()
    
    # Analyze problematic workflows
    analyze_problematic_workflows()
    
    # Suggest fixes
    suggest_fixes()
    
    # Create fix script
    create_fix_script()
    
    print("\n" + "="*80)
    print("✨ ANALYSIS COMPLETE")
    print("="*80 + "\n")
    
    if n8n_installed and n8n_running:
        print("✅ You can now test workflows by importing them into n8n")
        print("   Navigate to: http://localhost:5678")
    else:
        print("ℹ️  Install n8n to test workflows:")
        print("   npm install -g n8n")
        print("   n8n start")
    print()

if __name__ == '__main__':
    main()
