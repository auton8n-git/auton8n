#!/usr/bin/env python3
"""
Quick test script to verify n8n workflow compatibility
Attempts to validate workflow structure without actually importing
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

class QuickWorkflowTester:
    def __init__(self):
        self.test_results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }
    
    def validate_workflow_structure(self, workflow: Dict, filepath: str) -> Tuple[bool, List[str]]:
        """Quick validation of workflow structure"""
        issues = []
        
        # Check required top-level fields
        if 'nodes' not in workflow:
            issues.append("Missing 'nodes' field")
        if 'connections' not in workflow:
            issues.append("Missing 'connections' field")
        
        if issues:
            return False, issues
        
        # Check nodes structure
        nodes = workflow.get('nodes', [])
        if not isinstance(nodes, list):
            issues.append("'nodes' must be an array")
            return False, issues
        
        if len(nodes) == 0:
            issues.append("Workflow has no nodes")
            return False, issues
        
        # Validate each node
        node_names = set()
        for idx, node in enumerate(nodes):
            if not isinstance(node, dict):
                issues.append(f"Node {idx} is not an object")
                continue
            
            # Check required node fields
            node_type = node.get('type')
            node_name = node.get('name')
            node_position = node.get('position')
            node_params = node.get('parameters')
            
            if not node_type:
                issues.append(f"Node {idx} missing 'type'")
            if not node_name:
                issues.append(f"Node {idx} missing 'name'")
            else:
                if node_name in node_names:
                    issues.append(f"Duplicate node name: {node_name}")
                node_names.add(node_name)
            
            if node_position is None:
                issues.append(f"Node {idx} ({node_name}) missing 'position'")
            if node_params is None:
                issues.append(f"Node {idx} ({node_name}) missing 'parameters'")
        
        # Check connections structure
        connections = workflow.get('connections', {})
        if not isinstance(connections, dict):
            issues.append("'connections' must be an object")
        
        return len(issues) == 0, issues
    
    def check_node_compatibility(self, workflow: Dict) -> List[str]:
        """Check for known compatibility issues"""
        warnings = []
        nodes = workflow.get('nodes', [])
        
        # Check for problematic node types
        problematic_nodes = {
            'n8n-nodes-base.readBinaryFile': 'File system access - may not work in cloud',
            'n8n-nodes-base.writeBinaryFile': 'File system access - may not work in cloud',
            'n8n-nodes-base.readBinaryFiles': 'File system access - may not work in cloud',
            'n8n-nodes-base.executeCommand': 'Security risk - disabled in cloud',
        }
        
        for node in nodes:
            node_type = node.get('type', '')
            node_name = node.get('name', 'unnamed')
            
            if node_type in problematic_nodes:
                warnings.append(
                    f"Node '{node_name}' ({node_type}): {problematic_nodes[node_type]}"
                )
        
        # Check for trigger nodes
        trigger_keywords = ['trigger', 'webhook', 'cron', 'schedule', 'interval', 'imap']
        has_trigger = any(
            any(keyword in node.get('type', '').lower() for keyword in trigger_keywords)
            for node in nodes
        )
        
        if not has_trigger:
            warnings.append("No trigger node found - workflow can only be executed manually")
        
        return warnings
    
    def test_workflow(self, filepath: Path) -> Dict:
        """Test a single workflow file"""
        # Get relative path from workflows directory
        try:
            rel_path = str(filepath.relative_to(Path('workflows')))
        except ValueError:
            rel_path = str(filepath)
        
        result = {
            'file': rel_path,
            'status': 'unknown',
            'issues': [],
            'warnings': []
        }
        
        try:
            # Read and parse JSON
            with open(filepath, 'r', encoding='utf-8') as f:
                workflow = json.load(f)
            
            # Validate structure
            is_valid, issues = self.validate_workflow_structure(workflow, str(filepath))
            
            if not is_valid:
                result['status'] = 'failed'
                result['issues'] = issues
                self.test_results['failed'].append(result)
            else:
                # Check compatibility
                warnings = self.check_node_compatibility(workflow)
                
                result['status'] = 'passed'
                result['warnings'] = warnings
                
                if warnings:
                    self.test_results['warnings'].append(result)
                else:
                    self.test_results['passed'].append(result)
            
        except json.JSONDecodeError as e:
            result['status'] = 'failed'
            result['issues'] = [f"Invalid JSON: {str(e)}"]
            self.test_results['failed'].append(result)
        except Exception as e:
            result['status'] = 'failed'
            result['issues'] = [f"Error: {str(e)}"]
            self.test_results['failed'].append(result)
        
        return result
    
    def test_category(self, category: str, limit: int = 10) -> None:
        """Test workflows from a specific category"""
        list_file = Path('workflow_lists') / f'{category}.txt'
        
        if not list_file.exists():
            print(f"❌ Category file not found: {list_file}")
            return
        
        print(f"\n{'='*80}")
        print(f"🧪 Testing {category.replace('_', ' ').title()} Workflows")
        print(f"{'='*80}\n")
        
        # Read workflow list
        workflows = []
        with open(list_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    workflows.append(Path(line))
        
        # Limit number of tests
        test_workflows = workflows[:limit]
        total = len(workflows)
        
        print(f"Testing {len(test_workflows)} of {total} workflows...\n")
        
        # Test each workflow
        for idx, workflow_path in enumerate(test_workflows, 1):
            if not workflow_path.exists():
                print(f"[{idx}/{len(test_workflows)}] ❌ File not found: {workflow_path}")
                continue
            
            result = self.test_workflow(workflow_path)
            
            # Print result
            status_icon = '✅' if result['status'] == 'passed' else '❌'
            print(f"[{idx}/{len(test_workflows)}] {status_icon} {result['file']}")
            
            if result['issues']:
                for issue in result['issues'][:3]:  # Show first 3 issues
                    print(f"    ⚠️  {issue}")
            
            if result['warnings'] and len(result['warnings']) <= 2:
                for warning in result['warnings']:
                    print(f"    ℹ️  {warning}")
        
        # Print summary
        print(f"\n{'='*80}")
        print(f"Summary for {category}")
        print(f"{'='*80}")
        print(f"✅ Passed: {len([r for r in self.test_results['passed'] if any(category in r['file'] for category in [category])])}")
        print(f"⚠️  With warnings: {len([r for r in self.test_results['warnings'] if any(category in r['file'] for category in [category])])}")
        print(f"❌ Failed: {len([r for r in self.test_results['failed'] if any(category in r['file'] for category in [category])])}")
        print()

def main():
    if len(sys.argv) < 2:
        print("Usage: python quick_test.py [category] [limit]")
        print("\nAvailable categories:")
        print("  - production_ready")
        print("  - needs_trigger")
        print("  - cloud_incompatible")
        print("  - security_risk")
        print("\nExample:")
        print("  python quick_test.py production_ready 20")
        sys.exit(1)
    
    category = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    tester = QuickWorkflowTester()
    tester.test_category(category, limit)
    
    # Overall summary
    print("\n" + "="*80)
    print("📊 OVERALL TEST RESULTS")
    print("="*80)
    
    total_tested = len(tester.test_results['passed']) + len(tester.test_results['warnings']) + len(tester.test_results['failed'])
    
    print(f"\nTotal tested: {total_tested}")
    print(f"✅ Passed (no issues): {len(tester.test_results['passed'])}")
    print(f"⚠️  Passed (with warnings): {len(tester.test_results['warnings'])}")
    print(f"❌ Failed: {len(tester.test_results['failed'])}")
    
    if total_tested > 0:
        success_rate = ((len(tester.test_results['passed']) + len(tester.test_results['warnings'])) / total_tested) * 100
        print(f"\n✔️  Success rate: {success_rate:.1f}%")
    
    print()

if __name__ == '__main__':
    main()
