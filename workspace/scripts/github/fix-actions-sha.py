#!/usr/bin/env python3
"""
Fix GitHub Actions Security Policy - Pin Actions to Full SHAs
"""

import subprocess
import json
import re
from pathlib import Path

def get_latest_sha(action_name, version):
    """Get the latest commit SHA for a specific action version"""
    try:
        # Get the git ref for the version tag
        result = subprocess.run(
            ['git', 'ls-remote', f'https://github.com/{action_name}.git', version],
            capture_output=True,
            text=True,
            check=True
        )
        # Extract SHA from the output (first column)
        sha = result.stdout.strip().split('\t')[0]
        return sha
    except subprocess.CalledProcessError as e:
        print(f"Error getting SHA for {action_name}@{version}: {e}")
        return None

def get_action_mappings():
    """Get common action mappings with their latest SHAs"""
    # Known stable SHAs for common actions (as of recent versions)
    mappings = {
        'actions/checkout@v4': '0ad4b8f3a27c304e21892351cbf9860471245599',
        'actions/setup-python@v5': '82c7e631bb3cdc910f68e0081d534527d238d7a7',
        'actions/upload-artifact@v4': '65462800fd760344b1a7b4382951275a0abb4808',
        'actions/download-artifact@v4': '6b208ae046db98c579e8a328f74b955651f427c0',
        'actions/cache@v4': '0c45773b623bea8c8e75f6c82b208c3cf94ea4f9',
        'actions/labeler@v5': 'ce1b1cbcc02a699deffc8cedc9d05fab32256110',
        'actions/github-script@v7': '60a0d83039c74a4aee543508d2ffcb1c3799cdea',
        'actions/setup-node@v4': '1e60f620b9541d16bece96c5465dc8ee9832be0b',
        'actions/setup-java@v4': '99b8673ff64fbf99d8d325eba52e81358a9ae38f',
        'actions/setup-go@v5': 'd0c586a7fac1e018f3b070f5f9a331b37633aacd',
        'actions/setup-dotnet@v4': '97aa09494e6e811457c0a977a5a85a8b89159775',
        'actions/setup-ruby@v1': '1d8385deb1ec4e3cdb153fb59e7e86cd54862a54',
        'actions/setup-java@v3': '7a6d8a82381af951951b7477d3db30c0363a9f3a',
        'actions/configure-pages@v5': '1f0c5cde4bc74bb7780920c4b2b7dcba3462806a',
        'actions/upload-pages-artifact@v3': '56afc609e1f0a8fd0569726e2506e2e7a1eaaf9e',
        'actions/deploy-pages@v4': '0fd5c5a5a915415c4a12839799d68320e305ee5f',
    }
    return mappings

def fix_workflow_file(file_path, mappings):
    """Fix SHA pinning in a single workflow file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Replace each action version with its SHA
        for version_tag, full_sha in mappings.items():
            # Pattern to match uses: action@version
            pattern = rf'(uses:\s+{re.escape(version_tag)})'
            replacement = f'uses: {full_sha}'
            content = re.sub(pattern, replacement, content)
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            return True
        return False
        
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

def main():
    """Main function to fix all workflow files"""
    print("🔧 Fixing GitHub Actions Security Policy - SHA Pinning")
    print("=" * 60)
    
    # Get action mappings
    mappings = get_action_mappings()
    print(f"📋 Action mappings loaded: {len(mappings)} actions")
    
    for version_tag, sha in mappings.items():
        print(f"   {version_tag} -> {sha}")
    
    print("\n🔍 Scanning workflow files...")
    
    # Find all workflow files
    workflow_dir = Path('.github/workflows')
    workflow_files = list(workflow_dir.glob('*.yml')) + list(workflow_dir.glob('*.yaml'))
    
    print(f"📁 Found {len(workflow_files)} workflow files")
    
    fixed_files = []
    total_violations = 0
    
    for workflow_file in workflow_files:
        print(f"\n🔧 Processing: {workflow_file}")
        
        # Count violations before fixing
        with open(workflow_file, 'r') as f:
            content = f.read()
        
        violations = 0
        for version_tag in mappings.keys():
            violations += content.count(version_tag)
        
        if violations > 0:
            print(f"   🚨 Found {violations} violations")
            
            # Fix the file
            if fix_workflow_file(workflow_file, mappings):
                fixed_files.append(workflow_file)
                total_violations += violations
                print(f"   ✅ Fixed {violations} violations")
            else:
                print(f"   ❌ Failed to fix violations")
        else:
            print(f"   ✅ No violations found")
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print(f"   Total workflow files: {len(workflow_files)}")
    print(f"   Files fixed: {len(fixed_files)}")
    print(f"   Total violations fixed: {total_violations}")
    
    if fixed_files:
        print(f"\n✅ Fixed files:")
        for file in fixed_files:
            print(f"   - {file}")
    
    print(f"\n🎉 GitHub Actions Security Policy fix completed!")
    return len(fixed_files), total_violations

if __name__ == "__main__":
    main()