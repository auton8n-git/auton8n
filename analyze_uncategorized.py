#!/usr/bin/env python3
import json
import glob
from pathlib import Path

# Load def categories
with open('context/def_categories.json') as f:
    defs = json.load(f)

defined_services = {entry['integration'].lower() for entry in defs}
print(f"Defined services: {len(defined_services)}")

# Scan uncategorized workflows
uncategorized_with_services = {}
uncategorized_without_services = {}

for json_file in glob.glob("workflows/**/*.json", recursive=True):
    try:
        with open(json_file) as f:
            workflow = json.load(f)
        
        meta = workflow.get('meta', {})
        if meta.get('category') == 'Uncategorized':
            integrations = meta.get('integrations', [])
            
            matching = [i for i in integrations if i.lower() in defined_services]
            
            if matching:
                key = tuple(matching)
                if key not in uncategorized_with_services:
                    uncategorized_with_services[key] = []
                uncategorized_with_services[key].append(Path(json_file).name)
            else:
                key = tuple(integrations) if integrations else ('no-integrations',)
                if key not in uncategorized_without_services:
                    uncategorized_without_services[key] = 0
                uncategorized_without_services[key] += 1
    except:
        pass

print(f"\nUncategorized workflows WITH defined services: {sum(len(v) for v in uncategorized_with_services.values())}")
print(f"Uncategorized workflows WITHOUT defined services: {sum(uncategorized_without_services.values())}")

print("\n\nTOP uncategorized WITH defined services:")
for integ_tuple, files in sorted(uncategorized_with_services.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
    print(f"  {integ_tuple[0]}: {len(files)} workflows")

print("\n\nTOP uncategorized WITHOUT defined services (missing integrations):")
for integ_tuple, count in sorted(uncategorized_without_services.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"  {integ_tuple}: {count} workflows")
