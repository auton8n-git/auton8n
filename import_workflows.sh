#!/bin/bash
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
