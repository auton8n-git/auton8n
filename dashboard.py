#!/usr/bin/env python3
"""
Quick Dashboard - View Workflow Analysis Statistics
"""

import json
from pathlib import Path
from collections import defaultdict

def display_dashboard():
    """Display analysis dashboard."""
    
    # Load analysis data
    try:
        with open('workflow_analysis.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ workflow_analysis.json not found. Run analyze_workflows.py first.")
        return
    
    stats = data['statistics']
    workflows = data['workflows']
    
    print("\n" + "="*80)
    print("📊 N8N WORKFLOW ANALYSIS DASHBOARD")
    print("="*80)
    
    # Overall Statistics
    print(f"\n📈 OVERALL STATISTICS")
    print("-" * 80)
    print(f"  Total Workflows:        {stats['total']:,}")
    print(f"  Processed:              {stats['processed']:,}")
    print(f"  Processing Errors:      {stats['errors']}")
    print(f"  Unique Integrations:    {len(stats['by_integration'])}")
    print(f"  Unique Categories:      {len(stats['by_category'])}")
    
    # Top Categories
    print(f"\n📂 TOP 10 CATEGORIES")
    print("-" * 80)
    sorted_cats = sorted(stats['by_category'].items(), key=lambda x: x[1], reverse=True)
    for i, (cat, count) in enumerate(sorted_cats[:10], 1):
        pct = (count / stats['total']) * 100
        bar = "█" * int(pct / 2)
        print(f"  {i:2d}. {cat:.<40} {count:>4} ({pct:>5.1f}%) {bar}")
    
    # Top Integrations
    print(f"\n🔌 TOP 15 INTEGRATIONS")
    print("-" * 80)
    sorted_ints = sorted(stats['by_integration'].items(), key=lambda x: x[1], reverse=True)
    for i, (integ, count) in enumerate(sorted_ints[:15], 1):
        pct = (count / stats['total']) * 100
        bar = "▓" * int(pct / 5)
        print(f"  {i:2d}. {integ:.<35} {count:>4} ({pct:>5.1f}%) {bar}")
    
    # Category Details
    print(f"\n📋 WORKFLOWS PER CATEGORY")
    print("-" * 80)
    for cat in sorted(workflows.keys()):
        count = len(workflows[cat])
        print(f"  {cat:.<40} {count:>4} workflows")
    
    # Complexity Distribution
    print(f"\n📊 COMPLEXITY DISTRIBUTION")
    print("-" * 80)
    complexity_counts = defaultdict(int)
    for cat, wfs in workflows.items():
        for wf in wfs:
            complexity_counts[wf['complexity']] += 1
    
    total_wfs = sum(complexity_counts.values())
    for level in ['Low', 'Medium', 'High']:
        count = complexity_counts.get(level, 0)
        pct = (count / total_wfs * 100) if total_wfs > 0 else 0
        bar = "▰" * int(pct / 5)
        print(f"  {level:.<20} {count:>4} ({pct:>5.1f}%) {bar}")
    
    # Most Used Integration Pairs
    print(f"\n🔗 MOST COMMON INTEGRATION PAIRS")
    print("-" * 80)
    pair_counts = defaultdict(int)
    for cat, wfs in workflows.items():
        for wf in wfs:
            integ_list = sorted(wf['integrations'])
            if len(integ_list) >= 2:
                for i in range(len(integ_list) - 1):
                    pair = f"{integ_list[i]} + {integ_list[i+1]}"
                    pair_counts[pair] += 1
    
    sorted_pairs = sorted(pair_counts.items(), key=lambda x: x[1], reverse=True)
    for i, (pair, count) in enumerate(sorted_pairs[:10], 1):
        print(f"  {i:2d}. {pair:.<50} {count:>3} occurrences")
    
    # Trigger Type Distribution
    print(f"\n⚡ TRIGGER TYPE DISTRIBUTION")
    print("-" * 80)
    trigger_counts = defaultdict(int)
    for cat, wfs in workflows.items():
        for wf in wfs:
            trigger_counts[wf['trigger_type']] += 1
    
    for trigger, count in sorted(trigger_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total_wfs * 100) if total_wfs > 0 else 0
        bar = "◼" * int(pct / 5)
        print(f"  {trigger:.<30} {count:>4} ({pct:>5.1f}%) {bar}")
    
    # Node Count Statistics
    print(f"\n📌 NODE COUNT STATISTICS")
    print("-" * 80)
    node_counts = []
    for cat, wfs in workflows.items():
        for wf in wfs:
            node_counts.append(wf['node_count'])
    
    if node_counts:
        print(f"  Minimum:     {min(node_counts)} nodes")
        print(f"  Maximum:     {max(node_counts)} nodes")
        print(f"  Average:     {sum(node_counts) / len(node_counts):.1f} nodes")
        print(f"  Median:      {sorted(node_counts)[len(node_counts)//2]} nodes")
    
    # File Information
    print(f"\n💾 GENERATED FILES")
    print("-" * 80)
    files = [
        ("workflow_analysis.json", "Machine-readable analysis data"),
        ("workflow_analysis_report.txt", "Human-readable analysis report"),
        ("analyze_workflows.py", "Analysis script"),
        ("WORKFLOW_ANALYSIS_SUMMARY.md", "Comprehensive summary"),
    ]
    
    for fname, desc in files:
        fpath = Path(fname)
        if fpath.exists():
            size = fpath.stat().st_size
            if size > 1024*1024:
                size_str = f"{size/(1024*1024):.1f}MB"
            elif size > 1024:
                size_str = f"{size/1024:.1f}KB"
            else:
                size_str = f"{size}B"
            print(f"  ✓ {fname:.<40} {size_str:>10} - {desc}")
    
    print(f"\n{'='*80}\n")
    print("✅ Dashboard generated successfully!")
    print("📖 For detailed information, see:")
    print("   - WORKFLOW_ANALYSIS_SUMMARY.md")
    print("   - workflow_analysis_report.txt")
    print(f"   - workflow_analysis.json\n")


if __name__ == "__main__":
    display_dashboard()
