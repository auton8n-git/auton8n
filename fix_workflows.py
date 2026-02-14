#!/usr/bin/env python3
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
    
    print(f"Found {len(lines)} problematic workflows\n")
    
    for file_rel_path in lines:
        file_path = Path('workflows') / file_rel_path
        if file_path.exists():
            fix_workflow(file_path)
