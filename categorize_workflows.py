#!/usr/bin/env python3
"""
Generate lists of workflows categorized by usability
"""
import json
from pathlib import Path
from collections import defaultdict

def categorize_workflows():
    """Categorize workflows by their usability status"""
    
    # Load validation report
    with open('workflow_validation_report.json', 'r') as f:
        report = json.load(f)
    
    categories = {
        'production_ready': {
            'description': 'Workflows hoàn toàn sẵn sàng để dùng trong production',
            'workflows': []
        },
        'needs_trigger': {
            'description': 'Workflows hợp lệ nhưng cần thêm trigger để tự động hóa',
            'workflows': []
        },
        'cloud_incompatible': {
            'description': 'Workflows dùng file system - chỉ hoạt động trên self-hosted',
            'workflows': []
        },
        'security_risk': {
            'description': 'Workflows dùng executeCommand - không khuyến khích',
            'workflows': []
        },
        'corrupted': {
            'description': 'Workflows bị lỗi JSON - KHÔNG THỂ DÙNG',
            'workflows': []
        }
    }
    
    # Get workflows with warnings
    warning_workflows = set()
    for warning in report['warnings']:
        if warning['type'] == 'no_trigger':
            warning_workflows.add(warning['file'])
    
    # Get workflows with deprecated nodes
    file_system_workflows = set()
    execute_command_workflows = set()
    
    for node_info in report['deprecated_nodes']:
        node_type = node_info['node_type']
        workflow = node_info['file']
        
        if 'Binary' in node_type:
            file_system_workflows.add(workflow)
        elif 'executeCommand' in node_type:
            execute_command_workflows.add(workflow)
    
    # Get corrupted workflows
    corrupted_workflows = set()
    for item in report['missing_required_fields']:
        corrupted_workflows.add(item['file'])
    
    # Categorize valid workflows
    for workflow in report['valid']:
        if workflow in corrupted_workflows:
            categories['corrupted']['workflows'].append(workflow)
        elif workflow in execute_command_workflows:
            categories['security_risk']['workflows'].append(workflow)
        elif workflow in file_system_workflows:
            categories['cloud_incompatible']['workflows'].append(workflow)
        elif workflow in warning_workflows:
            categories['needs_trigger']['workflows'].append(workflow)
        else:
            categories['production_ready']['workflows'].append(workflow)
    
    return categories

def save_categorized_lists(categories):
    """Save categorized workflow lists"""
    
    # Create directory for lists
    lists_dir = Path('workflow_lists')
    lists_dir.mkdir(exist_ok=True)
    
    # Save each category
    for category_name, category_data in categories.items():
        file_path = lists_dir / f'{category_name}.txt'
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# {category_data['description']}\n")
            f.write(f"# Total: {len(category_data['workflows'])} workflows\n\n")
            
            for workflow in sorted(category_data['workflows']):
                f.write(f"workflows/{workflow}\n")
        
        print(f"✅ Saved {len(category_data['workflows'])} workflows to {file_path}")
    
    # Create summary
    summary_path = lists_dir / 'README.md'
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("# Workflow Categories\n\n")
        
        for category_name, category_data in categories.items():
            count = len(category_data['workflows'])
            f.write(f"## {category_name.replace('_', ' ').title()}\n\n")
            f.write(f"{category_data['description']}\n\n")
            f.write(f"**Count:** {count} workflows\n\n")
            f.write(f"**File:** `{category_name}.txt`\n\n")
            
            # Add usage recommendation
            if category_name == 'production_ready':
                f.write("✅ **Recommendation:** Import trực tiếp vào n8n\n\n")
            elif category_name == 'needs_trigger':
                f.write("⚠️ **Recommendation:** Thêm trigger node trước khi deploy\n\n")
            elif category_name == 'cloud_incompatible':
                f.write("☁️ **Recommendation:** Refactor để tương thích cloud hoặc dùng self-hosted\n\n")
            elif category_name == 'security_risk':
                f.write("🔒 **Recommendation:** Refactor thành Code node hoặc API calls\n\n")
            elif category_name == 'corrupted':
                f.write("❌ **Recommendation:** Xóa bỏ hoặc re-export từ n8n gốc\n\n")
            
            f.write("---\n\n")
    
    print(f"\n✅ Summary saved to {summary_path}")

def generate_import_script():
    """Generate a script to batch import workflows"""
    
    script = """#!/bin/bash
# Batch import n8n workflows
# Usage: ./import_workflows.sh [category]

CATEGORY=${1:-production_ready}
WORKFLOW_LIST="workflow_lists/${CATEGORY}.txt"

if [ ! -f "$WORKFLOW_LIST" ]; then
    echo "❌ Category not found: $CATEGORY"
    echo "Available categories:"
    ls workflow_lists/*.txt | xargs -n1 basename | sed 's/.txt//'
    exit 1
fi

echo "📦 Importing workflows from category: $CATEGORY"
echo ""

# Check if n8n is installed
if ! command -v n8n &> /dev/null; then
    echo "❌ n8n is not installed"
    echo "Install with: npm install -g n8n"
    exit 1
fi

# Count workflows
TOTAL=$(grep -v '^#' "$WORKFLOW_LIST" | grep -v '^$' | wc -l)
echo "Found $TOTAL workflows to import"
echo ""

# Import each workflow
COUNT=0
SUCCESS=0
FAILED=0

while IFS= read -r workflow; do
    # Skip comments and empty lines
    [[ "$workflow" =~ ^#.*$ ]] && continue
    [[ -z "$workflow" ]] && continue
    
    COUNT=$((COUNT + 1))
    echo "[$COUNT/$TOTAL] Importing: $workflow"
    
    if [ -f "$workflow" ]; then
        if n8n import:workflow --input="$workflow" 2>/dev/null; then
            SUCCESS=$((SUCCESS + 1))
            echo "  ✅ Success"
        else
            FAILED=$((FAILED + 1))
            echo "  ❌ Failed"
        fi
    else
        FAILED=$((FAILED + 1))
        echo "  ❌ File not found"
    fi
    echo ""
done < "$WORKFLOW_LIST"

echo "=================================="
echo "Import Complete"
echo "=================================="
echo "Total:   $TOTAL"
echo "Success: $SUCCESS"
echo "Failed:  $FAILED"
"""
    
    with open('import_workflows.sh', 'w') as f:
        f.write(script)
    
    Path('import_workflows.sh').chmod(0o755)
    print(f"✅ Created import_workflows.sh script")

def print_summary(categories):
    """Print summary of categorization"""
    print("\n" + "="*80)
    print("📊 WORKFLOW CATEGORIZATION SUMMARY")
    print("="*80 + "\n")
    
    total = sum(len(cat['workflows']) for cat in categories.values())
    
    print(f"Total workflows analyzed: {total}\n")
    
    for category_name, category_data in categories.items():
        count = len(category_data['workflows'])
        percentage = (count / total * 100) if total > 0 else 0
        
        # Emoji based on category
        emoji_map = {
            'production_ready': '✅',
            'needs_trigger': '⚠️',
            'cloud_incompatible': '☁️',
            'security_risk': '🔒',
            'corrupted': '❌'
        }
        emoji = emoji_map.get(category_name, '📄')
        
        print(f"{emoji} {category_name.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
        print(f"   {category_data['description']}")
        print()

def main():
    print("🔍 Categorizing workflows...\n")
    
    # Categorize workflows
    categories = categorize_workflows()
    
    # Print summary
    print_summary(categories)
    
    # Save lists
    print("\n📝 Saving categorized lists...\n")
    save_categorized_lists(categories)
    
    # Generate import script
    print("\n🔧 Generating helper scripts...\n")
    generate_import_script()
    
    print("\n" + "="*80)
    print("✨ CATEGORIZATION COMPLETE")
    print("="*80)
    print("\nFiles created:")
    print("  📁 workflow_lists/ - Contains categorized workflow lists")
    print("  📜 workflow_lists/README.md - Category descriptions")
    print("  🚀 import_workflows.sh - Batch import script")
    print("\nUsage:")
    print("  ./import_workflows.sh production_ready")
    print("  ./import_workflows.sh needs_trigger")
    print()

if __name__ == '__main__':
    main()
