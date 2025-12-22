#!/usr/bin/env python3
"""
Namespace Validator Tool
命名空間驗證工具

Validates that all files conform to MachineNativeOps namespace standards.
驗證所有檔案符合 MachineNativeOps 命名空間標準。

Usage:
    python namespace-validator.py --file <file>
    python namespace-validator.py --scan <directory>
    python namespace-validator.py --report

Returns exit code 0 if all validations pass, non-zero otherwise.
"""

import argparse
import json
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


class ValidationResult:
    """Result of a validation check"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.passed = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
    
    def add_error(self, message: str):
        """Add an error (causes validation to fail)"""
        self.errors.append(message)
        self.passed = False
    
    def add_warning(self, message: str):
        """Add a warning (doesn't cause validation to fail)"""
        self.warnings.append(message)
    
    def add_info(self, message: str):
        """Add informational message"""
        self.info.append(message)
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "file": self.file_path,
            "passed": self.passed,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info
        }


class NamespaceValidator:
    """Validates namespace compliance"""
    
    def __init__(self, config_path: str = "mno-namespace.yaml"):
        """Initialize validator with namespace configuration"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.results: List[ValidationResult] = []
        self.stats = {
            "files_checked": 0,
            "files_passed": 0,
            "files_failed": 0,
            "errors": 0,
            "warnings": 0
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
    
    def validate_file(self, file_path: Path) -> ValidationResult:
        """
        Validate a single file
        
        Args:
            file_path: Path to file to validate
        
        Returns:
            ValidationResult object
        """
        result = ValidationResult(str(file_path))
        self.stats["files_checked"] += 1
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Run validation checks
            self._check_legacy_namespaces(content, result)
            self._check_namespace_consistency(content, result)
            self._check_naming_patterns(content, result)
            self._check_registry_urls(content, result)
            self._check_certificate_paths(content, result)
            self._check_cluster_tokens(content, result)
            
            # Update stats
            if result.passed:
                self.stats["files_passed"] += 1
            else:
                self.stats["files_failed"] += 1
            
            self.stats["errors"] += len(result.errors)
            self.stats["warnings"] += len(result.warnings)
            
        except Exception as e:
            result.add_error(f"Validation error: {e}")
            self.stats["files_failed"] += 1
            self.stats["errors"] += 1
        
        self.results.append(result)
        return result
    
    def _check_legacy_namespaces(self, content: str, result: ValidationResult):
        """Check for legacy namespace usage"""
        migration = self.config.get("migration", {})
        legacy_namespaces = migration.get("legacy_namespaces", [])
        
        for legacy_ns in legacy_namespaces:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(legacy_ns) + r'\b'
            if re.search(pattern, content):
                result.add_error(
                    f"Legacy namespace '{legacy_ns}' found - should be migrated to 'machinenativeops'"
                )
    
    def _check_namespace_consistency(self, content: str, result: ValidationResult):
        """Check that namespace usage is consistent"""
        namespace_config = self.config.get("namespace", {})
        primary_ns = namespace_config.get("primary", "")
        variants = namespace_config.get("variants", {})
        
        # Count occurrences of each variant
        variant_counts = {}
        for variant_type, variant_name in variants.items():
            count = len(re.findall(re.escape(variant_name), content))
            if count > 0:
                variant_counts[variant_type] = count
        
        # If multiple variants are used, that might indicate inconsistency
        if len(variant_counts) > 2:  # Allow some flexibility
            result.add_warning(
                f"Multiple namespace variants used: {', '.join(variant_counts.keys())} - "
                "consider using consistent casing"
            )
    
    def _check_naming_patterns(self, content: str, result: ValidationResult):
        """Validate naming pattern compliance"""
        validation_config = self.config.get("validation", {})
        
        # Check namespace pattern
        namespace_pattern = validation_config.get("namespace_pattern", "")
        if namespace_pattern:
            # Find all potential namespace references
            matches = re.findall(r'\bmachinenativeops(?:-[a-z0-9]+)*\b', content, re.IGNORECASE)
            for match in matches:
                if not re.match(namespace_pattern, match.lower()):
                    result.add_error(
                        f"Invalid namespace format '{match}' - must match pattern {namespace_pattern}"
                    )
        
        # Check version pattern if versions are present
        version_pattern = validation_config.get("version_pattern", "")
        if version_pattern:
            version_matches = re.findall(r'\b[vV]?\d+\.\d+\.\d+(?:-[a-z0-9.-]+)?\b', content)
            for version in version_matches:
                if not re.match(version_pattern, version):
                    result.add_warning(
                        f"Version '{version}' may not match standard pattern {version_pattern}"
                    )
    
    def _check_registry_urls(self, content: str, result: ValidationResult):
        """Check registry URL usage"""
        registries = self.config.get("registries", {})
        primary_registry = registries.get("primary", {}).get("url", "")
        
        if not primary_registry:
            return
        
        # Check for correct registry usage
        if primary_registry in content:
            result.add_info(f"Uses primary registry: {primary_registry}")
        
        # Check for incorrect registry patterns
        incorrect_patterns = [
            r'docker\.io/machine-native-ops',
            r'ghcr\.io/machine-native-ops-aaps',
        ]
        
        for pattern in incorrect_patterns:
            if re.search(pattern, content):
                result.add_error(
                    f"Found legacy registry pattern - should use {primary_registry}"
                )
    
    def _check_certificate_paths(self, content: str, result: ValidationResult):
        """Check certificate path compliance"""
        certs = self.config.get("certificates", {})
        correct_base_path = certs.get("base_path", "")
        correct_pkl_path = certs.get("pkl_path", "")
        
        # Check for correct paths
        if correct_pkl_path and correct_pkl_path in content:
            result.add_info(f"Uses correct PKL path: {correct_pkl_path}")
        
        # Check for incorrect certificate paths
        incorrect_paths = [
            r'/etc/machine-native-ops',
            r'/etc/aaps',
        ]
        
        for pattern in incorrect_paths:
            if re.search(pattern, content):
                result.add_error(
                    f"Found legacy certificate path - should use {correct_base_path}"
                )
    
    def _check_cluster_tokens(self, content: str, result: ValidationResult):
        """Check cluster token usage"""
        clusters = self.config.get("clusters", {})
        etcd_config = clusters.get("etcd", {})
        correct_token = etcd_config.get("token", "")
        
        if correct_token and correct_token in content:
            result.add_info(f"Uses correct etcd cluster token")
        
        # Check for legacy cluster tokens
        legacy_tokens = [
            'aaps-etcd-cluster',
            'machine-native-ops-etcd',
        ]
        
        for token in legacy_tokens:
            if token in content:
                result.add_error(
                    f"Found legacy cluster token '{token}' - should use {correct_token}"
                )
    
    def scan_directory(self, directory: Path, patterns: List[str] = None) -> None:
        """
        Scan and validate all files in a directory
        
        Args:
            directory: Directory to scan
            patterns: File patterns to match
        """
        if patterns is None:
            patterns = ['*.yaml', '*.yml', '*.md', '*.json', '*.sh', '*.py', '*.ts', '*.js']
        
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
                
                # Skip certain directories
                skip_dirs = {'node_modules', 'dist', 'build', '.git', '__pycache__', 'vendor'}
                if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
                    continue
                
                self.validate_file(file_path)
    
    def print_report(self, verbose: bool = False):
        """Print validation report"""
        print("\n" + "="*80)
        print("Namespace Validation Report")
        print("="*80)
        
        # Summary statistics
        print(f"\n📊 Summary:")
        print(f"  Files checked:  {self.stats['files_checked']}")
        print(f"  ✅ Passed:      {self.stats['files_passed']}")
        print(f"  ❌ Failed:      {self.stats['files_failed']}")
        print(f"  Errors:         {self.stats['errors']}")
        print(f"  Warnings:       {self.stats['warnings']}")
        
        # Failed files
        failed_results = [r for r in self.results if not r.passed]
        if failed_results:
            print(f"\n❌ Failed Files ({len(failed_results)}):")
            for result in failed_results:
                print(f"\n  {result.file_path}")
                for error in result.errors:
                    print(f"    ❌ {error}")
                if verbose and result.warnings:
                    for warning in result.warnings:
                        print(f"    ⚠️  {warning}")
        
        # Warnings (if verbose)
        if verbose:
            warning_results = [r for r in self.results if r.warnings and r.passed]
            if warning_results:
                print(f"\n⚠️  Files with Warnings ({len(warning_results)}):")
                for result in warning_results:
                    print(f"\n  {result.file_path}")
                    for warning in result.warnings:
                        print(f"    ⚠️  {warning}")
        
        # Overall result
        print("\n" + "="*80)
        if self.stats['files_failed'] == 0:
            print("✅ All validations passed!")
        else:
            print(f"❌ Validation failed: {self.stats['files_failed']} files need attention")
        print("="*80 + "\n")
    
    def generate_json_report(self) -> str:
        """Generate JSON report"""
        report = {
            "summary": self.stats,
            "results": [r.to_dict() for r in self.results]
        }
        return json.dumps(report, indent=2)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Validate namespace compliance with MachineNativeOps standards"
    )
    parser.add_argument(
        "--config",
        default="mno-namespace.yaml",
        help="Path to namespace configuration file"
    )
    parser.add_argument(
        "--file",
        help="Validate a single file"
    )
    parser.add_argument(
        "--scan",
        help="Scan and validate all files in directory"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate detailed report"
    )
    parser.add_argument(
        "--json",
        help="Output JSON report to file"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Initialize validator
    validator = NamespaceValidator(config_path=args.config)
    
    # Execute requested operation
    if args.file:
        result = validator.validate_file(Path(args.file))
        
        print(f"\nValidation result for {result.file_path}:")
        print(f"Status: {'✅ PASSED' if result.passed else '❌ FAILED'}")
        
        if result.errors:
            print("\nErrors:")
            for error in result.errors:
                print(f"  ❌ {error}")
        
        if result.warnings:
            print("\nWarnings:")
            for warning in result.warnings:
                print(f"  ⚠️  {warning}")
        
        if args.verbose and result.info:
            print("\nInfo:")
            for info in result.info:
                print(f"  ℹ️  {info}")
        
        sys.exit(0 if result.passed else 1)
    
    elif args.scan:
        validator.scan_directory(Path(args.scan))
        validator.print_report(verbose=args.verbose)
        
        if args.json:
            with open(args.json, 'w') as f:
                f.write(validator.generate_json_report())
            print(f"JSON report written to {args.json}")
        
        sys.exit(0 if validator.stats['files_failed'] == 0 else 1)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
