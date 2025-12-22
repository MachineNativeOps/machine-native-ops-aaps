#!/usr/bin/env python3
"""
Namespace Converter Tool
命名空間轉換工具

Converts legacy namespaces and naming conventions to the new MachineNativeOps standard.
將舊的命名空間和命名慣例轉換為新的 MachineNativeOps 標準。

Usage:
    python namespace-converter.py --input <file> --output <file>
    python namespace-converter.py --scan <directory>
    python namespace-converter.py --dry-run <file>
"""

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NamespaceConverter:
    """Converts namespaces according to mno-namespace.yaml configuration"""
    
    def __init__(self, config_path: str = "mno-namespace.yaml"):
        """Initialize converter with namespace configuration"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.conversion_rules = self._build_conversion_rules()
        self.stats = {
            "files_scanned": 0,
            "files_converted": 0,
            "replacements_made": 0,
            "errors": 0
        }
    
    def _load_config(self) -> dict:
        """Load namespace configuration from YAML"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded namespace config from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
    
    def _build_conversion_rules(self) -> List[Tuple[str, str, str]]:
        """Build conversion rules from configuration"""
        rules = []
        
        # Get migration mappings
        migration = self.config.get("migration", {})
        mapping = migration.get("mapping", {})
        
        # Primary namespace
        primary_ns = self.config.get("namespace", {}).get("primary", "machinenativeops")
        
        # Add rules for each legacy namespace
        for old_ns, new_ns in mapping.items():
            # Pattern 1: Direct replacement
            rules.append((
                r'\b' + re.escape(old_ns) + r'\b',
                new_ns,
                f"Direct namespace replacement: {old_ns} → {new_ns}"
            ))
            
            # Pattern 2: In URLs
            rules.append((
                re.escape(old_ns) + r'\.io',
                f"{new_ns}.io",
                f"Domain replacement: {old_ns}.io → {new_ns}.io"
            ))
            
            # Pattern 3: In paths
            rules.append((
                r'/' + re.escape(old_ns) + r'/',
                f"/{new_ns}/",
                f"Path replacement: /{old_ns}/ → /{new_ns}/"
            ))
        
        # Registry conversions
        registries = self.config.get("registries", {})
        if "primary" in registries:
            primary_registry = registries["primary"].get("url", "")
            if primary_registry:
                # Convert docker.io/machine-native-ops to registry.machinenativeops.io
                rules.append((
                    r'docker\.io/machine-native-ops',
                    f"{primary_registry}/machinenativeops",
                    f"Registry conversion to {primary_registry}"
                ))
        
        logger.info(f"Built {len(rules)} conversion rules")
        return rules
    
    def convert_content(self, content: str) -> Tuple[str, int]:
        """
        Convert content using defined rules
        
        Returns:
            Tuple of (converted_content, number_of_replacements)
        """
        replacements = 0
        result = content
        
        for pattern, replacement, description in self.conversion_rules:
            new_result, count = re.subn(pattern, replacement, result)
            if count > 0:
                logger.debug(f"{description}: {count} replacements")
                replacements += count
                result = new_result
        
        return result, replacements
    
    def convert_file(self, input_path: Path, output_path: Path = None, dry_run: bool = False) -> bool:
        """
        Convert a single file
        
        Args:
            input_path: Path to input file
            output_path: Path to output file (None = overwrite)
            dry_run: If True, don't write changes
        
        Returns:
            True if changes were made
        """
        self.stats["files_scanned"] += 1
        
        try:
            # Read file
            with open(input_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Convert
            converted_content, replacements = self.convert_content(original_content)
            
            # Check if changes were made
            if replacements == 0:
                logger.debug(f"No changes needed for {input_path}")
                return False
            
            self.stats["replacements_made"] += replacements
            
            # Report changes
            logger.info(f"{'[DRY RUN] ' if dry_run else ''}Converting {input_path}: {replacements} replacements")
            
            if not dry_run:
                # Write output
                output_path = output_path or input_path
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(converted_content)
                logger.info(f"Wrote converted file to {output_path}")
                self.stats["files_converted"] += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Error converting {input_path}: {e}")
            self.stats["errors"] += 1
            return False
    
    def scan_directory(self, directory: Path, patterns: List[str] = None, dry_run: bool = False) -> None:
        """
        Scan and convert all files in a directory
        
        Args:
            directory: Directory to scan
            patterns: File patterns to match (default: ['*.yaml', '*.yml', '*.md'])
            dry_run: If True, don't write changes
        """
        if patterns is None:
            patterns = ['*.yaml', '*.yml', '*.md', '*.json', '*.sh', '*.py']
        
        directory = Path(directory)
        if not directory.is_dir():
            logger.error(f"Not a directory: {directory}")
            return
        
        logger.info(f"Scanning directory: {directory}")
        
        for pattern in patterns:
            for file_path in directory.rglob(pattern):
                # Skip hidden files and directories
                if any(part.startswith('.') for part in file_path.parts):
                    continue
                    
                # Skip node_modules, dist, etc.
                skip_dirs = {'node_modules', 'dist', 'build', '.git', '__pycache__'}
                if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
                    continue
                
                self.convert_file(file_path, dry_run=dry_run)
        
        self.print_stats()
    
    def print_stats(self) -> None:
        """Print conversion statistics"""
        print("\n" + "="*60)
        print("Namespace Conversion Statistics")
        print("="*60)
        print(f"Files scanned:      {self.stats['files_scanned']}")
        print(f"Files converted:    {self.stats['files_converted']}")
        print(f"Replacements made:  {self.stats['replacements_made']}")
        print(f"Errors:             {self.stats['errors']}")
        print("="*60 + "\n")
    
    def validate_conversion(self, file_path: Path) -> Dict[str, any]:
        """
        Validate a converted file
        
        Returns:
            Dictionary with validation results
        """
        results = {
            "file": str(file_path),
            "valid": True,
            "issues": [],
            "warnings": []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for legacy namespaces
            migration = self.config.get("migration", {})
            legacy_namespaces = migration.get("legacy_namespaces", [])
            
            for legacy_ns in legacy_namespaces:
                if legacy_ns in content:
                    results["issues"].append(f"Legacy namespace '{legacy_ns}' still present")
                    results["valid"] = False
            
            # Check for correct primary namespace
            primary_ns = self.config.get("namespace", {}).get("primary", "")
            if primary_ns and primary_ns not in content:
                # This is just a warning, not an error
                results["warnings"].append(f"Primary namespace '{primary_ns}' not found")
            
        except Exception as e:
            results["valid"] = False
            results["issues"].append(f"Validation error: {e}")
        
        return results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Convert namespaces to MachineNativeOps standard"
    )
    parser.add_argument(
        "--config",
        default="mno-namespace.yaml",
        help="Path to namespace configuration file"
    )
    parser.add_argument(
        "--input",
        help="Input file to convert"
    )
    parser.add_argument(
        "--output",
        help="Output file (default: overwrite input)"
    )
    parser.add_argument(
        "--scan",
        help="Scan and convert all files in directory"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without writing"
    )
    parser.add_argument(
        "--validate",
        help="Validate a converted file"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Initialize converter
    converter = NamespaceConverter(config_path=args.config)
    
    # Execute requested operation
    if args.validate:
        results = converter.validate_conversion(Path(args.validate))
        print(f"\nValidation results for {results['file']}:")
        print(f"Valid: {results['valid']}")
        if results['issues']:
            print("\nIssues:")
            for issue in results['issues']:
                print(f"  - {issue}")
        if results['warnings']:
            print("\nWarnings:")
            for warning in results['warnings']:
                print(f"  - {warning}")
        sys.exit(0 if results['valid'] else 1)
    
    elif args.scan:
        converter.scan_directory(Path(args.scan), dry_run=args.dry_run)
    
    elif args.input:
        input_path = Path(args.input)
        output_path = Path(args.output) if args.output else None
        
        if converter.convert_file(input_path, output_path, dry_run=args.dry_run):
            print(f"\n✅ Conversion complete!")
            if args.dry_run:
                print("(Dry run - no files were modified)")
        else:
            print("\nℹ️  No changes needed")
        
        converter.print_stats()
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
