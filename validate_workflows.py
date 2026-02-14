#!/usr/bin/env python3
"""
Validate n8n workflow JSON files for compatibility and errors
"""
import json
import os
from pathlib import Path
from collections import defaultdict
import sys

class WorkflowValidator:
    def __init__(self, workflows_dir):
        self.workflows_dir = Path(workflows_dir)
        self.results = {
            'valid': [],
            'invalid_json': [],
            'missing_required_fields': [],
            'empty_nodes': [],
            'missing_connections': [],
            'deprecated_nodes': [],
            'warnings': []
        }
        
        # Common deprecated or problematic node types
        self.deprecated_nodes = {
            'n8n-nodes-base.executeCommand': 'Security risk - may not work in cloud',
            'n8n-nodes-base.readBinaryFile': 'File system access - may not work in cloud',
            'n8n-nodes-base.writeBinaryFile': 'File system access - may not work in cloud',
            'n8n-nodes-base.readBinaryFiles': 'File system access - may not work in cloud',
        }
        
    def validate_json(self, file_path):
        """Check if file is valid JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return True, data
        except json.JSONDecodeError as e:
            return False, str(e)
        except Exception as e:
            return False, str(e)
    
    def validate_workflow_structure(self, workflow_data, file_path):
        """Validate required n8n workflow fields"""
        issues = []
        
        # Check required fields
        required_fields = ['nodes', 'connections']
        for field in required_fields:
            if field not in workflow_data:
                issues.append(f"Missing required field: {field}")
        
        # Validate nodes
        if 'nodes' in workflow_data:
            nodes = workflow_data['nodes']
            if not isinstance(nodes, list):
                issues.append("'nodes' must be an array")
            elif len(nodes) == 0:
                issues.append("Workflow has no nodes (empty)")
            else:
                # Check each node
                for idx, node in enumerate(nodes):
                    if not isinstance(node, dict):
                        issues.append(f"Node {idx} is not an object")
                        continue
                    
                    # Check required node fields
                    if 'type' not in node:
                        issues.append(f"Node {idx} missing 'type' field")
                    if 'position' not in node:
                        issues.append(f"Node {idx} missing 'position' field")
                    if 'parameters' not in node:
                        issues.append(f"Node {idx} missing 'parameters' field")
                    
                    # Check for deprecated nodes
                    if 'type' in node:
                        node_type = node.get('type', '')
                        if node_type in self.deprecated_nodes:
                            self.results['deprecated_nodes'].append({
                                'file': str(file_path),
                                'node_type': node_type,
                                'reason': self.deprecated_nodes[node_type],
                                'node_name': node.get('name', 'unnamed')
                            })
        
        # Validate connections
        if 'connections' in workflow_data:
            connections = workflow_data['connections']
            if not isinstance(connections, dict):
                issues.append("'connections' must be an object")
        
        return issues
    
    def check_workflow_completeness(self, workflow_data, file_path):
        """Check if workflow has proper trigger and connections"""
        warnings = []
        
        if 'nodes' not in workflow_data or not workflow_data['nodes']:
            return warnings
        
        nodes = workflow_data['nodes']
        connections = workflow_data.get('connections', {})
        
        # Check for trigger nodes
        trigger_types = [
            'n8n-nodes-base.webhook',
            'n8n-nodes-base.cron',
            'n8n-nodes-base.interval',
            'n8n-nodes-base.trigger',
            'n8n-nodes-base.manualTrigger',
            'n8n-nodes-base.start',
            'n8n-nodes-base.emailReadImap',
            'n8n-nodes-base.scheduleTrigger',
            'n8n-nodes-base.formTrigger'
        ]
        
        has_trigger = any(
            node.get('type', '').lower() in [t.lower() for t in trigger_types] or
            'trigger' in node.get('type', '').lower()
            for node in nodes
        )
        
        if not has_trigger:
            warnings.append({
                'file': str(file_path),
                'type': 'no_trigger',
                'message': 'Workflow has no trigger node - may not execute automatically'
            })
        
        # Check for disconnected nodes
        if len(nodes) > 1 and not connections:
            warnings.append({
                'file': str(file_path),
                'type': 'no_connections',
                'message': 'Workflow has multiple nodes but no connections'
            })
        
        return warnings
    
    def validate_file(self, file_path):
        """Validate a single workflow file"""
        rel_path = file_path.relative_to(self.workflows_dir)
        
        # Check JSON validity
        is_valid_json, data_or_error = self.validate_json(file_path)
        
        if not is_valid_json:
            self.results['invalid_json'].append({
                'file': str(rel_path),
                'error': data_or_error
            })
            return
        
        workflow_data = data_or_error
        
        # Check workflow structure
        structure_issues = self.validate_workflow_structure(workflow_data, rel_path)
        
        if structure_issues:
            self.results['missing_required_fields'].append({
                'file': str(rel_path),
                'issues': structure_issues
            })
            return
        
        # Check for empty workflows
        if not workflow_data.get('nodes') or len(workflow_data['nodes']) == 0:
            self.results['empty_nodes'].append({
                'file': str(rel_path),
                'message': 'Workflow has no nodes'
            })
            return
        
        # Check completeness and add warnings
        warnings = self.check_workflow_completeness(workflow_data, rel_path)
        if warnings:
            self.results['warnings'].extend(warnings)
        
        # If we got here, workflow is valid
        self.results['valid'].append(str(rel_path))
    
    def validate_all(self):
        """Validate all workflow JSON files"""
        json_files = list(self.workflows_dir.rglob('*.json'))
        
        print(f"🔍 Found {len(json_files)} JSON files to validate...\n")
        
        for idx, file_path in enumerate(json_files, 1):
            if idx % 100 == 0:
                print(f"Processing... {idx}/{len(json_files)}")
            self.validate_file(file_path)
        
        return self.results
    
    def print_report(self):
        """Print validation report"""
        print("\n" + "="*80)
        print("📊 N8N WORKFLOW VALIDATION REPORT")
        print("="*80 + "\n")
        
        total = (len(self.results['valid']) + 
                len(self.results['invalid_json']) + 
                len(self.results['missing_required_fields']) + 
                len(self.results['empty_nodes']))
        
        print(f"✅ Valid workflows: {len(self.results['valid'])}")
        print(f"❌ Invalid JSON: {len(self.results['invalid_json'])}")
        print(f"⚠️  Missing required fields: {len(self.results['missing_required_fields'])}")
        print(f"📭 Empty workflows: {len(self.results['empty_nodes'])}")
        print(f"⚡ Warnings: {len(self.results['warnings'])}")
        print(f"🔧 Deprecated nodes found: {len(self.results['deprecated_nodes'])}")
        print(f"\n📈 Total processed: {total}")
        print(f"✔️  Success rate: {(len(self.results['valid'])/total*100):.1f}%\n")
        
        # Print detailed issues
        if self.results['invalid_json']:
            print("\n" + "="*80)
            print("❌ INVALID JSON FILES (Cannot be imported to n8n)")
            print("="*80)
            for item in self.results['invalid_json'][:10]:  # Show first 10
                print(f"\n📄 {item['file']}")
                print(f"   Error: {item['error']}")
            if len(self.results['invalid_json']) > 10:
                print(f"\n... and {len(self.results['invalid_json']) - 10} more")
        
        if self.results['missing_required_fields']:
            print("\n" + "="*80)
            print("⚠️  MISSING REQUIRED FIELDS (May not work in n8n)")
            print("="*80)
            for item in self.results['missing_required_fields'][:10]:
                print(f"\n📄 {item['file']}")
                for issue in item['issues']:
                    print(f"   • {issue}")
            if len(self.results['missing_required_fields']) > 10:
                print(f"\n... and {len(self.results['missing_required_fields']) - 10} more")
        
        if self.results['empty_nodes']:
            print("\n" + "="*80)
            print("📭 EMPTY WORKFLOWS (No nodes defined)")
            print("="*80)
            for item in self.results['empty_nodes'][:10]:
                print(f"   • {item['file']}")
            if len(self.results['empty_nodes']) > 10:
                print(f"\n... and {len(self.results['empty_nodes']) - 10} more")
        
        if self.results['deprecated_nodes']:
            print("\n" + "="*80)
            print("🔧 DEPRECATED/PROBLEMATIC NODES")
            print("="*80)
            node_counts = defaultdict(list)
            for item in self.results['deprecated_nodes']:
                node_counts[item['node_type']].append(item['file'])
            
            for node_type, files in node_counts.items():
                reason = self.deprecated_nodes.get(node_type, 'Unknown issue')
                print(f"\n🔸 {node_type}")
                print(f"   Reason: {reason}")
                print(f"   Found in {len(files)} workflow(s):")
                for f in files[:5]:
                    print(f"   • {f}")
                if len(files) > 5:
                    print(f"   ... and {len(files) - 5} more")
        
        if self.results['warnings']:
            print("\n" + "="*80)
            print("⚡ WARNINGS (Workflows may have issues)")
            print("="*80)
            
            warning_types = defaultdict(list)
            for warning in self.results['warnings']:
                warning_types[warning['type']].append(warning)
            
            for warning_type, warnings in warning_types.items():
                print(f"\n🔸 {warning_type.upper()}: {len(warnings)} workflow(s)")
                print(f"   {warnings[0]['message']}")
                print(f"   Examples:")
                for w in warnings[:5]:
                    print(f"   • {w['file']}")
                if len(warnings) > 5:
                    print(f"   ... and {len(warnings) - 5} more")
        
        print("\n" + "="*80)
        print("✨ VALIDATION COMPLETE")
        print("="*80 + "\n")
        
        # Save detailed report
        self.save_report()
    
    def save_report(self):
        """Save detailed report to JSON file"""
        report_file = Path('workflow_validation_report.json')
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Detailed report saved to: {report_file}")
        
        # Save problematic files list
        if (self.results['invalid_json'] or 
            self.results['missing_required_fields'] or 
            self.results['empty_nodes']):
            
            problematic_file = Path('problematic_workflows.txt')
            with open(problematic_file, 'w', encoding='utf-8') as f:
                f.write("# PROBLEMATIC N8N WORKFLOWS\n")
                f.write("# These workflows cannot be used or may have issues\n\n")
                
                if self.results['invalid_json']:
                    f.write("\n## INVALID JSON (Cannot import):\n")
                    for item in self.results['invalid_json']:
                        f.write(f"{item['file']}\n")
                
                if self.results['missing_required_fields']:
                    f.write("\n## MISSING REQUIRED FIELDS:\n")
                    for item in self.results['missing_required_fields']:
                        f.write(f"{item['file']}\n")
                
                if self.results['empty_nodes']:
                    f.write("\n## EMPTY WORKFLOWS:\n")
                    for item in self.results['empty_nodes']:
                        f.write(f"{item['file']}\n")
            
            print(f"📝 Problematic workflows list saved to: {problematic_file}\n")


def main():
    workflows_dir = Path(__file__).parent / 'workflows'
    
    if not workflows_dir.exists():
        print(f"❌ Error: Workflows directory not found: {workflows_dir}")
        sys.exit(1)
    
    validator = WorkflowValidator(workflows_dir)
    validator.validate_all()
    validator.print_report()
    
    # Return exit code based on results
    if validator.results['invalid_json'] or validator.results['missing_required_fields']:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
