#!/usr/bin/env python3
"""
Fix database to include category column and populate from workflow files
"""

import sqlite3
import json
import os
from pathlib import Path
from glob import glob

# 1. Add category column if it doesn't exist
print("🔧 Adding category column to database...")
conn = sqlite3.connect('database/workflows.db')
cursor = conn.cursor()

# Check if column exists
cursor.execute("PRAGMA table_info(workflows)")
columns = [row[1] for row in cursor.fetchall()]

if 'category' not in columns:
    try:
        cursor.execute("ALTER TABLE workflows ADD COLUMN category TEXT DEFAULT 'Uncategorized'")
        conn.commit()
        print("✅ Added category column")
    except Exception as e:
        print(f"⚠️  Column might already exist: {e}")
else:
    print("✅ Category column already exists")

conn.close()

# 2. Load all workflow files and update database with category from meta
print("\n📝 Loading categories from workflow files...")

workflows_path = Path('workflows')
json_files = list(workflows_path.rglob("*.json"))
updated_count = 0
missing_meta = 0

conn = sqlite3.connect('database/workflows.db')
cursor = conn.cursor()

for json_file in json_files:
    try:
        with open(json_file) as f:
            data = json.load(f)
        
        filename = json_file.name
        meta = data.get('meta', {})
        category = meta.get('category', 'Uncategorized')
        
        # Update database
        cursor.execute(
            "UPDATE workflows SET category = ? WHERE filename = ?",
            (category, filename)
        )
        updated_count += 1
        
        if updated_count % 100 == 0:
            print(f"  Updated {updated_count} workflows...")
            
        if not meta:
            missing_meta += 1
            
    except Exception as e:
        print(f"⚠️  Error processing {json_file.name}: {e}")

conn.commit()
conn.close()

print(f"\n✅ Updated {updated_count} workflows with categories from meta")
print(f"⚠️  {missing_meta} workflows had no meta section")

# 3. Show category distribution
print("\n📊 Category distribution:")
conn = sqlite3.connect('database/workflows.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT category, COUNT(*) as count 
    FROM workflows 
    WHERE category IS NOT NULL
    GROUP BY category 
    ORDER BY count DESC
""")

for category, count in cursor.fetchall():
    pct = (count / 2056) * 100
    print(f"  {category:.<50} {count:>4} ({pct:>5.1f}%)")

# Check AI Agent Development specifically
cursor.execute("SELECT COUNT(*) FROM workflows WHERE category = 'AI Agent Development'")
ai_count = cursor.fetchone()[0]
print(f"\n🤖 AI Agent Development: {ai_count} workflows")

conn.close()

print("\n✨ Database fix complete!")
