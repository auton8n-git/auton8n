#!/usr/bin/env python3
"""
Smart mapping of uncategorized workflows using fuzzy matching and keyword analysis
"""

import json
import glob
from pathlib import Path
from difflib import SequenceMatcher
from collections import defaultdict

print("🔍 MAPPING UNCATEGORIZED WORKFLOWS")
print("=" * 80)

# Load official categories
with open('context/def_categories.json') as f:
    def_categories = json.load(f)

# Build service maps (case-insensitive)
service_to_category = {}
all_services = []
for entry in def_categories:
    service_name = entry['integration'].lower()
    service_to_category[service_name] = entry['category']
    all_services.append((entry['integration'], entry['category']))

print(f"✅ Loaded {len(service_to_category)} official services")

# Custom mappings for common integrations not in def_categories
custom_mappings = {
    # AI/ML related
    'openai': 'AI Agent Development',
    'langchain': 'AI Agent Development', 
    'lmchatopenai': 'AI Agent Development',
    'ai': 'AI Agent Development',
    'summarize': 'AI Agent Development',
    'basicllmchain': 'AI Agent Development',
    'memorywindow': 'AI Agent Development',
    'memorybufferwindow': 'AI Agent Development',
    
    # Data/Processing
    'json': 'Data Processing & Analysis',
    'csv': 'Data Processing & Analysis',
    'xml': 'Data Processing & Analysis',
    'yaml': 'Data Processing & Analysis',
    'flatten': 'Data Processing & Analysis',
    'groupby': 'Data Processing & Analysis',
    'aggregate': 'Data Processing & Analysis',
    
    # Web/HTTP
    'http': 'Web Scraping & Data Extraction',
    'request': 'Web Scraping & Data Extraction',
    'webhook': 'Web Scraping & Data Extraction',
    'html': 'Web Scraping & Data Extraction',
    'extractfromfile': 'Data Processing & Analysis',
    
    # Communication
    'email': 'Communication & Messaging',
    'emailsend': 'Communication & Messaging',
    'emailreadimap': 'Communication & Messaging',
    'sms': 'Communication & Messaging',
    'twilio': 'Communication & Messaging',
    'telegram': 'Communication & Messaging',
    'discord': 'Communication & Messaging',
    'slack': 'Communication & Messaging',
    'mailchimp': 'Marketing & Advertising Automation',
    
    # File/Storage
    'file': 'Cloud Storage & File Management',
    'dropbox': 'Cloud Storage & File Management',
    'googledrive': 'Cloud Storage & File Management',
    'onedrive': 'Cloud Storage & File Management',
    'googlesheets': 'Data Processing & Analysis',
    'airtable': 'Data Processing & Analysis',
    'notion': 'Data Processing & Analysis',
    
    # Business
    'crm': 'CRM & Sales',
    'salesforce': 'CRM & Sales',
    'hubspot': 'CRM & Sales',
    'pipedrive': 'CRM & Sales',
    'shopify': 'E-commerce & Retail',
    'woocommerce': 'E-commerce & Retail',
    'stripe': 'Financial & Accounting',
    'paypal': 'Financial & Accounting',
    'quickbooks': 'Financial & Accounting',
    
    # Project Management
    'jira': 'Project Management',
    'monday': 'Project Management',
    'asana': 'Project Management',
    'clickup': 'Project Management',
    'trello': 'Project Management',
    
    # Social Media
    'twitter': 'Social Media Management',
    'facebook': 'Social Media Management',
    'instagram': 'Social Media Management',
    'youtube': 'Creative Content & Video Automation',
    'linkedin': 'Social Media Management',
    
    # Design/Creative
    'figma': 'Creative Design Automation',
    'canva': 'Creative Design Automation',
    'imagemagick': 'Creative Design Automation',
    'editimage': 'Creative Design Automation',
    
    # DevOps/Infrastructure
    'aws': 'Technical Infrastructure & DevOps',
    'azure': 'Technical Infrastructure & DevOps',
    'gcp': 'Technical Infrastructure & DevOps',
    'docker': 'Technical Infrastructure & DevOps',
    'kubernetes': 'Technical Infrastructure & DevOps',
    'github': 'Technical Infrastructure & DevOps',
    'gitlab': 'Technical Infrastructure & DevOps',
    'ssh': 'Technical Infrastructure & DevOps',
}

# Internal n8n nodes to skip
internal_nodes = {
    'set', 'trigger', 'merge', 'switch', 'split', 'splitout', 'splitinbatches',
    'code', 'if', 'loop', 'wait', 'schedule', 'webhooktrigger', 'scheduletrigger',
    'stickynote', 'noop', 'function', 'respondtowebhook', 'httpbin', 'form', 
    'datetime', 'n8n', 'executecommand', 'executecommandtool', 'executeworkflow',
    'debug', 'debughelper', 'error', 'throw', 'join', 'sort', 'limit', 'offset',
    'manualtrigger', 'croncron', 'cronirigger', 'mcp', 'custom', 'createhtml',
    'readpdf', 'readbinaryfiles', 'conversion', 'converttofile', 'compression',
    'deep', 'cron', 'get', 'post', 'put', 'delete', 'patch', 'send', 'create',
    'update', 'quote', '\'', '"', 'hub', 'filter', 'export', 'import', 'search',
}

def similarity(a, b):
    """Calculate similarity between two strings (0-1)"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def find_best_match(integration):
    """Find best category match for an integration"""
    norm = integration.lower().strip()
    
    # Skip internal nodes
    if norm in internal_nodes:
        return None
    
    # Check custom mappings first
    for custom_key, category in custom_mappings.items():
        if custom_key in norm:
            return category
    
    # Check official services (exact match first)
    if norm in service_to_category:
        return service_to_category[norm]
    
    # Try fuzzy matching with official services
    best_match = None
    best_score = 0.7  # Threshold
    for service in all_services:
        score = similarity(norm, service[0].lower())
        if score > best_score:
            best_score = score
            best_match = service[1]
    
    return best_match

# Scan uncategorized workflows
uncategorized = []
for json_file in glob.glob("workflows/**/*.json", recursive=True):
    try:
        with open(json_file) as f:
            workflow = json.load(f)
        meta = workflow.get('meta', {})
        if meta.get('category') == 'Uncategorized':
            integrations = meta.get('integrations', [])
            uncategorized.append((json_file, integrations))
    except:
        pass

print(f"Found {len(uncategorized)} uncategorized workflows\n")

# Map each workflow
mapped = 0
still_uncategorized = 0

for json_file, integrations in uncategorized:
    found_category = None
    
    # Try to find a category from integrations
    for integration in integrations:
        category = find_best_match(integration)
        if category:
            found_category = category
            break
    
    if not found_category:
        still_uncategorized += 1
        continue
    
    # Update the file
    try:
        with open(json_file) as f:
            workflow = json.load(f)
        
        if 'meta' not in workflow:
            workflow['meta'] = {}
        
        workflow['meta']['category'] = found_category
        
        with open(json_file, 'w') as f:
            json.dump(workflow, f, indent=2)
        
        mapped += 1
        if mapped % 100 == 0:
            print(f"  ✓ Mapped {mapped} workflows...")
    except Exception as e:
        print(f"Error updating {Path(json_file).name}: {e}")

print(f"\n✅ MAPPING COMPLETE")
print(f"  Successfully mapped: {mapped} workflows")
print(f"  Still uncategorized: {still_uncategorized} workflows")
print(f"  Total processed: {mapped + still_uncategorized}")

# Show new distribution
print("\n📊 NEW CATEGORY DISTRIBUTION:")
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
    pct = (count / 2056) * 100
    print(f"  {cat:.<50} {count:>4} ({pct:>5.1f}%)")

print(f"\n🎯 Summary:")
print(f"  Categorized: {2056 - categories.get('Uncategorized', 0)} / 2056")
print(f"  Uncategorized: {categories.get('Uncategorized', 0)} / 2056")
