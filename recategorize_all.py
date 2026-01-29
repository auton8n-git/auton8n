#!/usr/bin/env python3
"""
Force recategorize ALL workflows using official categories from def_categories.json
Uses the FIRST matching real service integration (not internal n8n nodes)
"""

import json
import glob
from pathlib import Path
from datetime import datetime

print("🔄 FORCE RECATEGORIZATION OF ALL WORKFLOWS")
print("=" * 80)

# Load official categories
with open('context/def_categories.json') as f:
    def_categories = json.load(f)

# Build mappings (case-insensitive)
service_to_category = {}
for entry in def_categories:
    service_name = entry['integration'].lower()
    service_to_category[service_name] = entry['category']

print(f"✅ Loaded {len(service_to_category)} service-to-category mappings")

# Internal n8n nodes that shouldn't be used for categorization
internal_nodes = {
    'set', 'trigger', 'merge', 'switch', 'split', 'splitout', 'splitinbatches',
    'code', 'if', 'loop', 'wait', 'schedule', 'webhooktrigger', 'scheduletrigger',
    'stickynote', 'noop', 'function', 'respondtowebhook', 'httpbin', 'form', 'aggregate',
    'datetime', 'n8n', 'executecommand', 'executecommandtool', 'executeworkflow',
    'debug', 'debughelper', 'error', 'throw', 'flatten', 'groupby', 'join',
    'manualtrigger', 'cronrigger', 'mcp', 'summarize', 'custom', 'createhtml',
    'readpdf', 'editimage', 'converttofile', 'extractfromfile', 'compression',
    'deep', 'request', 'http', 'get', 'post', 'put', 'delete', 'patch', 'send',
    'create', 'update', 'delete', 'filter', 'export', 'import', 'search',
    'quote', '\'', 'hub'
}

# Force update ALL workflow files
updated = 0
failed = 0
uncategorized = 0
categorized = 0

for json_file in sorted(glob.glob("workflows/**/*.json", recursive=True)):
    try:
        with open(json_file, encoding='utf-8') as f:
            workflow = json.load(f)
        
        # Get integrations from meta
        meta = workflow.get('meta', {})
        integrations = meta.get('integrations', [])
        
        # Find FIRST matching real service (skip internal nodes)
        found_category = None
        for integration in integrations:
            norm = integration.lower().strip()
            
            # Skip internal nodes
            if norm in internal_nodes:
                continue
            
            # Try to match service
            if norm in service_to_category:
                found_category = service_to_category[norm]
                break
        
        if not found_category:
            found_category = "Uncategorized"
            uncategorized += 1
        else:
            categorized += 1
        
        # Update workflow meta
        if 'meta' not in workflow:
            workflow['meta'] = {}
        
        workflow['meta']['category'] = found_category
        
        # Write back to file
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, indent=2)
        
        updated += 1
        if updated % 100 == 0:
            print(f"  ✓ Updated {updated} files...")
            
    except Exception as e:
        print(f"❌ Error processing {Path(json_file).name}: {e}")
        failed += 1

print(f"\n✅ COMPLETE!")
print(f"  Updated: {updated} files")
print(f"  Failed: {failed} files")
print(f"  Categorized: {categorized} files")
print(f"  Uncategorized: {uncategorized} files")

# Show distribution
print("\n📊 CATEGORY DISTRIBUTION:")
categories = {}
for json_file in glob.glob("workflows/**/*.json", recursive=True):
    try:
        with open(json_file) as f:
            meta = json.load(f).get('meta', {})
            cat = meta.get('category', 'Uncategorized')
            categories[cat] = categories.get(cat, 0) + 1
    except:
        pass

for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
    pct = (count / updated) * 100 if updated > 0 else 0
    print(f"  {cat:.<50} {count:>4} ({pct:>5.1f}%)")

ai_count = categories.get('AI Agent Development', 0)
print(f"\n🤖 AI Agent Development: {ai_count} workflows")

