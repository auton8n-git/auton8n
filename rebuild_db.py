#!/usr/bin/env python3
"""Rebuild database with category column"""

import sqlite3
import json
import glob
from pathlib import Path

print("🔄 REBUILDING DATABASE FROM WORKFLOW FILES")
print("=" * 80)

# Remove old database
import os
if os.path.exists('database/workflows.db'):
    os.remove('database/workflows.db')

# Create database
conn = sqlite3.connect('database/workflows.db')
cursor = conn.cursor()

# Create workflows table WITH category column
cursor.execute("""
    CREATE TABLE IF NOT EXISTS workflows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT UNIQUE NOT NULL,
        name TEXT,
        workflow_id TEXT,
        active BOOLEAN DEFAULT 0,
        description TEXT,
        trigger_type TEXT DEFAULT 'Manual',
        complexity TEXT DEFAULT 'low',
        node_count INTEGER DEFAULT 0,
        integrations TEXT DEFAULT '[]',
        tags TEXT DEFAULT '[]',
        category TEXT DEFAULT 'Uncategorized',
        created_at TEXT,
        updated_at TEXT,
        file_hash TEXT UNIQUE,
        file_size INTEGER,
        analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

print("✅ Created workflows table with category column")

# Create FTS table
cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS workflows_fts USING fts5(
        filename, name, description, integrations, tags,
        content=workflows,
        content_rowid=id
    )
""")

# Create indexes
cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON workflows(category)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_trigger_type ON workflows(trigger_type)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_complexity ON workflows(complexity)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_active ON workflows(active)")

conn.commit()

# Load workflows from files
print("\n📝 Loading workflows from files...")
count = 0

for json_file in sorted(glob.glob("workflows/**/*.json", recursive=True)):
    try:
        with open(json_file, encoding='utf-8') as f:
            workflow = json.load(f)
        
        filename = Path(json_file).name
        meta = workflow.get('meta', {})
        
        # Extract data
        cursor.execute("""
            INSERT OR REPLACE INTO workflows (
                filename, name, workflow_id, active, description, trigger_type,
                complexity, node_count, integrations, tags, category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            filename,
            workflow.get('name', filename),
            workflow.get('id', ''),
            1 if workflow.get('active', False) else 0,
            meta.get('description', ''),
            meta.get('trigger_type', 'Manual'),
            meta.get('complexity', 'low'),
            len(workflow.get('nodes', [])),
            json.dumps(meta.get('integrations', [])),
            json.dumps(workflow.get('tags', [])),
            meta.get('category', 'Uncategorized')
        ))
        
        count += 1
        if count % 100 == 0:
            print(f"  ✓ Loaded {count} workflows...")
    except Exception as e:
        print(f"❌ Error loading {filename}: {e}")

conn.commit()
conn.close()

print(f"\n✅ Database rebuilt with {count} workflows")
