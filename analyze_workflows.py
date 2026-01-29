#!/usr/bin/env python3
"""
Workflow Analyzer & Description Generator
Reads, categorizes, groups, and generates descriptions for all workflows
"""

import json
import os
import glob
from pathlib import Path
from typing import Dict, List, Any, Tuple
import re
from collections import defaultdict
from datetime import datetime

class WorkflowAnalyzer:
    """Analyze and process n8n workflows."""
    
    # Mapping of integrations to categories
    CATEGORIES = {
        "Communication & Messaging": [
            "discord", "slack", "telegram", "twilio", "gmail", "emailsend", "emailreadimap",
            "vonage", "whatsapp", "teams", "outlook", "mailchimp", "sendgrid", "mailgun",
            "hubspot", "intercom", "zendesk", "customerio", "getresponse"
        ],
        "CRM & Sales": [
            "salesforce", "hubspot", "pipedrive", "copper", "activecampaign", "zoho",
            "freshsales", "agile", "affinity", "dynamics", "sugarcrm"
        ],
        "Data Processing & Analysis": [
            "airtable", "googlesheets", "excel", "elasticsearch", "postgresql", "mysql",
            "mongodb", "supabase", "firebase", "spreadsheet", "csv", "json", "comparedatasets",
            "aggregate", "groupby", "splitinbatches", "extractfromfile", "readbinaryfile"
        ],
        "Cloud Storage & File Management": [
            "googledrive", "dropbox", "onedrive", "awss3", "box", "sharepoint",
            "googlecloud", "azure", "converttofile", "writebinaryfile", "localfile"
        ],
        "E-Commerce & Retail": [
            "shopify", "woocommerce", "magento", "stripe", "paypal", "square",
            "bigcommerce", "opencart", "prestashop"
        ],
        "Project Management & Collaboration": [
            "asana", "monday", "jira", "clickup", "trello", "basecamp", "notion",
            "confluence", "github", "gitlab", "bitbucket"
        ],
        "Marketing & Advertising": [
            "mailchimp", "klaviyo", "hubspot", "marketo", "activeadvisor", "lemlist",
            "outreach", "salesloft", "convertkit", "beehiiv", "facebook", "instagram",
            "google", "linkedin", "twitter", "tiktok"
        ],
        "AI & Machine Learning": [
            "openai", "anthropic", "cohere", "gemini", "langchain", "chatgpt", "gpt",
            "llm", "ai", "geminiai", "llmchat", "chatwrapper", "deepseek", "cortex"
        ],
        "Web Scraping & API Integration": [
            "http", "webhook", "api", "rest", "graphql", "websocket", "rssfeed",
            "respondtowebhook", "waitwebhook"
        ],
        "Social Media Management": [
            "facebook", "instagram", "twitter", "tiktok", "linkedin", "youtube",
            "pinterest", "snapchat", "discord", "telegram", "facebookleadads"
        ],
        "Scheduling & Automation": [
            "cron", "schedule", "scheduler", "timer", "interval", "wait", "delay",
            "trigger", "eventbased"
        ],
        "Code & Development": [
            "code", "function", "javascript", "python", "nodejs", "bash",
            "executecommand", "git", "npm", "cli"
        ],
        "Document Management": [
            "googledocs", "googlesheets", "pdf", "office", "word", "excel",
            "docx", "pptx", "readpdf", "mindee"
        ],
        "Financial & Accounting": [
            "stripe", "paypal", "square", "quickbooks", "xero", "freshbooks",
            "wave", "chargebee", "chargify", "recurly"
        ],
        "Image & Design": [
            "editimage", "imagemagick", "imageprocessing", "bannerbear",
            "figma", "canva", "adobe", "photoshop"
        ],
        "Utilities & Tools": [
            "noop", "filter", "splitout", "limit", "aggregate", "merge",
            "transform", "parse", "extract", "convert", "compression"
        ],
        "Monitoring & Analytics": [
            "analytics", "monitoring", "logging", "metric", "prometheus",
            "grafana", "datadog", "newrelic", "splunk"
        ]
    }
    
    # Reverse mapping: integration -> category
    INTEGRATION_TO_CATEGORY = {}
    
    def __init__(self, workflows_dir: str = "workflows"):
        self.workflows_dir = Path(workflows_dir)
        self.workflows: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.stats = {
            "total": 0,
            "processed": 0,
            "errors": 0,
            "by_category": defaultdict(int),
            "by_integration": defaultdict(int)
        }
        self._build_integration_map()
    
    def _build_integration_map(self):
        """Build reverse mapping of integration -> category."""
        for category, integrations in self.CATEGORIES.items():
            for integration in integrations:
                self.INTEGRATION_TO_CATEGORY[integration.lower()] = category
    
    def analyze_workflow_json(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from workflow JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                workflow = json.load(f)
            
            # Extract nodes and integrations
            nodes = workflow.get('nodes', [])
            integrations = set()
            triggers = []
            node_count = len(nodes)
            
            for node in nodes:
                node_type = node.get('type', '')
                node_name = node.get('name', '')
                
                # Extract integration from node type
                integration = self._extract_integration(node_type, node_name)
                if integration:
                    integrations.add(integration)
                
                # Identify triggers
                if 'trigger' in node_type.lower() or 'webhook' in node_type.lower():
                    triggers.append(node_type)
            
            # Determine trigger type
            trigger_type = self._determine_trigger_type(triggers, node_types=[n.get('type', '') for n in nodes])
            
            # Determine complexity
            complexity = self._determine_complexity(node_count, len(integrations))
            
            return {
                'filename': file_path.name,
                'path': str(file_path),
                'node_count': node_count,
                'integrations': list(integrations),
                'triggers': triggers,
                'trigger_type': trigger_type,
                'complexity': complexity,
                'has_credentials': any('credentials' in node for node in nodes)
            }
        except Exception as e:
            print(f"❌ Error reading {file_path.name}: {e}")
            return None
    
    def _extract_integration(self, node_type: str, node_name: str) -> str:
        """Extract integration name from node type or name."""
        combined = f"{node_type} {node_name}".lower()
        
        # Check for known integrations
        for integration_name in self.INTEGRATION_TO_CATEGORY.keys():
            if integration_name in combined:
                return integration_name.title()
        
        # Try parsing from node_type (e.g., "n8n-nodes-base.gmail" -> "Gmail")
        if 'n8n-nodes' in node_type:
            parts = node_type.split('.')
            if len(parts) > 1:
                integration = parts[-1].title()
                if len(integration) > 2:
                    return integration
        
        return None
    
    def _determine_trigger_type(self, triggers: List[str], node_types: List[str]) -> str:
        """Determine the primary trigger type."""
        all_types = ' '.join(triggers + node_types).lower()
        
        if 'webhook' in all_types:
            return 'Webhook'
        elif 'cron' in all_types or 'schedule' in all_types:
            return 'Scheduled'
        elif 'manual' in all_types or 'trigger' in all_types:
            return 'Manual'
        else:
            return 'Manual'
    
    def _determine_complexity(self, node_count: int, integration_count: int) -> str:
        """Determine complexity based on node and integration count."""
        score = (node_count * 0.6) + (integration_count * 0.4)
        
        if score < 5:
            return 'Low'
        elif score < 15:
            return 'Medium'
        else:
            return 'High'
    
    def categorize_workflow(self, integrations: List[str], filename: str) -> str:
        """Categorize workflow based on integrations and filename."""
        # First try to find category from integrations
        for integration in integrations:
            integration_lower = integration.lower()
            for int_name, category in self.INTEGRATION_TO_CATEGORY.items():
                if int_name in integration_lower:
                    return category
        
        # Fallback: try filename-based categorization
        filename_lower = filename.lower()
        for int_name, category in self.INTEGRATION_TO_CATEGORY.items():
            if int_name in filename_lower:
                return category
        
        # Default category
        return "Utilities & Tools"
    
    def generate_description(self, metadata: Dict[str, Any]) -> str:
        """Generate a meaningful description for the workflow."""
        filename = metadata['filename']
        integrations = metadata['integrations']
        trigger_type = metadata['trigger_type']
        complexity = metadata['complexity']
        node_count = metadata['node_count']
        
        # Parse filename for clues
        name_parts = filename.replace('.json', '').split('_')
        
        # Build description
        if integrations:
            integration_str = ' and '.join(integrations)
            desc = f"Workflow using {integration_str}"
        else:
            desc = f"N8n automation workflow"
        
        desc += f" with {node_count} nodes"
        
        if trigger_type != 'Manual':
            desc += f", triggered via {trigger_type}"
        
        desc += f". Complexity: {complexity}"
        
        return desc
    
    def process_all_workflows(self) -> Dict[str, Any]:
        """Process all workflow files."""
        print(f"\n📊 Processing workflows from: {self.workflows_dir}")
        
        # Find all JSON files
        workflow_files = sorted(glob.glob(str(self.workflows_dir / "**/*.json"), recursive=True))
        self.stats['total'] = len(workflow_files)
        
        for file_path_str in workflow_files:
            file_path = Path(file_path_str)
            
            # Analyze workflow
            metadata = self.analyze_workflow_json(file_path)
            if metadata is None:
                self.stats['errors'] += 1
                continue
            
            # Categorize
            category = self.categorize_workflow(
                metadata['integrations'],
                metadata['filename']
            )
            metadata['category'] = category
            
            # Generate description
            description = self.generate_description(metadata)
            metadata['description'] = description
            
            # Store by category
            self.workflows[category].append(metadata)
            self.stats['by_category'][category] += 1
            
            for integration in metadata['integrations']:
                self.stats['by_integration'][integration] += 1
            
            self.stats['processed'] += 1
            
            # Progress indicator
            if self.stats['processed'] % 100 == 0:
                print(f"  ✓ Processed {self.stats['processed']}/{self.stats['total']} workflows")
        
        print(f"\n✅ Processing complete: {self.stats['processed']}/{self.stats['total']} workflows")
        return self.workflows
    
    def generate_report(self) -> str:
        """Generate a comprehensive report."""
        report = []
        report.append("=" * 80)
        report.append("N8N WORKFLOW ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"\n📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Statistics
        report.append(f"\n📊 STATISTICS")
        report.append("-" * 40)
        report.append(f"Total Workflows: {self.stats['total']}")
        report.append(f"Processed: {self.stats['processed']}")
        report.append(f"Errors: {self.stats['errors']}")
        
        # By Category
        report.append(f"\n📂 BREAKDOWN BY CATEGORY")
        report.append("-" * 40)
        sorted_categories = sorted(
            self.stats['by_category'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        for category, count in sorted_categories:
            report.append(f"{category:.<40} {count:>4} workflows")
        
        # By Integration (top 30)
        report.append(f"\n🔌 TOP 30 INTEGRATIONS")
        report.append("-" * 40)
        sorted_integrations = sorted(
            self.stats['by_integration'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:30]
        for integration, count in sorted_integrations:
            report.append(f"{integration:.<40} {count:>4} workflows")
        
        # Grouped workflows
        report.append(f"\n📋 WORKFLOWS BY CATEGORY")
        report.append("=" * 80)
        
        for category in sorted(self.workflows.keys()):
            workflows_in_cat = self.workflows[category]
            report.append(f"\n{category.upper()}")
            report.append(f"({len(workflows_in_cat)} workflows)")
            report.append("-" * 40)
            
            for workflow in sorted(workflows_in_cat, key=lambda w: w['filename']):
                report.append(f"\n  📄 {workflow['filename']}")
                report.append(f"     📝 {workflow['description']}")
                report.append(f"     📊 Nodes: {workflow['node_count']}, Complexity: {workflow['complexity']}")
                if workflow['integrations']:
                    report.append(f"     🔌 Integrations: {', '.join(workflow['integrations'])}")
        
        return "\n".join(report)
    
    def export_to_json(self, output_file: str = "workflow_analysis.json"):
        """Export analysis results to JSON."""
        export_data = {
            'generated_at': datetime.now().isoformat(),
            'statistics': {
                'total': self.stats['total'],
                'processed': self.stats['processed'],
                'errors': self.stats['errors'],
                'by_category': dict(self.stats['by_category']),
                'by_integration': dict(self.stats['by_integration'])
            },
            'workflows': {}
        }
        
        for category, workflows in self.workflows.items():
            export_data['workflows'][category] = [
                {
                    'filename': w['filename'],
                    'description': w['description'],
                    'node_count': w['node_count'],
                    'integrations': w['integrations'],
                    'trigger_type': w['trigger_type'],
                    'complexity': w['complexity']
                }
                for w in workflows
            ]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return output_file
    
    def update_workflow_descriptions(self, save_backup: bool = True):
        """Update workflow JSON files with new descriptions."""
        updated_count = 0
        
        for category, workflows_list in self.workflows.items():
            for workflow_meta in workflows_list:
                file_path = Path(workflow_meta['path'])
                
                try:
                    # Read original workflow
                    with open(file_path, 'r', encoding='utf-8') as f:
                        workflow = json.load(f)
                    
                    # Save backup if requested
                    if save_backup:
                        backup_path = file_path.with_suffix('.json.bak')
                        if not backup_path.exists():
                            with open(backup_path, 'w', encoding='utf-8') as f:
                                json.dump(workflow, f, indent=2)
                    
                    # Update metadata section
                    if 'meta' not in workflow:
                        workflow['meta'] = {}
                    
                    workflow['meta']['description'] = workflow_meta['description']
                    workflow['meta']['category'] = workflow_meta['category']
                    workflow['meta']['complexity'] = workflow_meta['complexity']
                    workflow['meta']['integrations'] = workflow_meta['integrations']
                    workflow['meta']['analyzed_at'] = datetime.now().isoformat()
                    
                    # Write updated workflow
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(workflow, f, indent=2)
                    
                    updated_count += 1
                    
                    if updated_count % 100 == 0:
                        print(f"  ✓ Updated {updated_count} workflow files")
                
                except Exception as e:
                    print(f"❌ Error updating {file_path.name}: {e}")
        
        return updated_count


def main():
    """Main entry point."""
    analyzer = WorkflowAnalyzer("workflows")
    
    print("\n🔍 ANALYZING ALL WORKFLOWS")
    print("=" * 80)
    
    # Process all workflows
    analyzer.process_all_workflows()
    
    # Generate and display report
    print("\n")
    report = analyzer.generate_report()
    print(report)
    
    # Save report
    report_file = "workflow_analysis_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n✅ Report saved to: {report_file}")
    
    # Export to JSON
    json_file = analyzer.export_to_json("workflow_analysis.json")
    print(f"✅ Data exported to: {json_file}")
    
    # Update workflow descriptions
    print(f"\n📝 UPDATING WORKFLOW DESCRIPTIONS")
    print("=" * 80)
    updated = analyzer.update_workflow_descriptions(save_backup=True)
    print(f"\n✅ Updated {updated} workflow files with new descriptions and metadata")
    print(f"   Backups created with .json.bak extension")


if __name__ == "__main__":
    main()
