#!/usr/bin/env python3
"""
FHS Directory Manager - Complete FHS Structure Health Management Tool

This tool provides comprehensive FHS directory structure management including:
- Directory health checking
- Permission validation
- Storage monitoring
- Automated cleanup
- Structure repair
"""

import os
import sys
import stat
import shutil
import json
import yaml
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

class FHSDirectoryManager:
    """FHS Directory Structure Management System"""
    
    def __init__(self, config_file: str = "etc/machinenativeops/fhs-structure-config.yaml"):
        self.config_file = Path(config_file)
        self.config = self.load_config()
        self.fhs_directories = self.config.get('fhs_structure', {})
        self.health_status = {}
        
    def load_config(self) -> Dict:
        """Load FHS configuration from YAML file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    return yaml.safe_load(f)
            else:
                # Default configuration
                return {
                    'fhs_structure': {
                        'bin': {'description': '基本用戶命令二進制檔案', 'permissions': '755'},
                        'sbin': {'description': '系統管理二進制檔案', 'permissions': '755'},
                        'etc': {'description': '系統配置檔案', 'permissions': '755', 'subdirs': ['machinenativeops', 'sysconfig', 'default', 'init.d']},
                        'lib': {'description': '共享函式庫', 'permissions': '755', 'subdirs': ['modules', 'firmware']},
                        'var': {'description': '變動資料', 'permissions': '755', 'subdirs': ['log', 'cache', 'lib', 'tmp', 'spool', 'run']},
                        'usr': {'description': '用戶程式', 'permissions': '755', 'subdirs': ['bin', 'sbin', 'lib', 'share', 'local']},
                        'home': {'description': '用戶主目錄', 'permissions': '755'},
                        'tmp': {'description': '臨時檔案', 'permissions': '1777'},
                        'opt': {'description': '可選應用程式', 'permissions': '755'},
                        'srv': {'description': '服務資料', 'permissions': '755', 'subdirs': ['http', 'ftp', 'www']},
                        'init.d': {'description': '初始化腳本', 'permissions': '755'}
                    },
                    'health_checks': {
                        'max_age_days': 30,
                        'max_size_mb': 1000,
                        'min_free_space_mb': 100
                    }
                }
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            sys.exit(1)
    
    def check_directory_health(self, directory: str) -> Dict:
        """Check health of a specific FHS directory"""
        dir_path = Path(directory)
        health = {
            'directory': directory,
            'exists': dir_path.exists(),
            'is_directory': dir_path.is_dir() if dir_path.exists() else False,
            'permissions': None,
            'permissions_valid': False,
            'size_mb': 0,
            'file_count': 0,
            'oldest_file': None,
            'newest_file': None,
            'issues': [],
            'warnings': []
        }
        
        if not dir_path.exists():
            health['issues'].append(f"Directory {directory} does not exist")
            return health
        
        if not dir_path.is_dir():
            health['issues'].append(f"Path {directory} exists but is not a directory")
            return health
        
        # Check permissions
        try:
            stat_info = dir_path.stat()
            health['permissions'] = oct(stat_info.st_mode)[-3:]
            expected_perms = self.fhs_directories.get(directory, {}).get('permissions', '755')
            health['permissions_valid'] = health['permissions'] == expected_perms
            
            if not health['permissions_valid']:
                health['issues'].append(f"Invalid permissions: {health['permissions']} (expected {expected_perms})")
        except Exception as e:
            health['issues'].append(f"Permission check failed: {e}")
        
        # Check directory contents
        try:
            total_size = 0
            file_count = 0
            oldest_time = None
            newest_time = None
            oldest_file = None
            newest_file = None
            
            for item in dir_path.rglob('*'):
                if item.is_file():
                    file_count += 1
                    size = item.stat().st_size
                    total_size += size
                    mtime = item.stat().st_mtime
                    
                    if oldest_time is None or mtime < oldest_time:
                        oldest_time = mtime
                        oldest_file = str(item)
                    
                    if newest_time is None or mtime > newest_time:
                        newest_time = mtime
                        newest_file = str(item)
            
            health['size_mb'] = round(total_size / (1024 * 1024), 2)
            health['file_count'] = file_count
            health['oldest_file'] = oldest_file
            health['newest_file'] = newest_file
            
            # Check for size warnings
            max_size = self.config.get('health_checks', {}).get('max_size_mb', 1000)
            if health['size_mb'] > max_size:
                health['warnings'].append(f"Directory size {health['size_mb']}MB exceeds limit {max_size}MB")
            
            # Check for old files
            max_age = self.config.get('health_checks', {}).get('max_age_days', 30)
            if oldest_time:
                age_days = (datetime.now().timestamp() - oldest_time) / (24 * 3600)
                if age_days > max_age:
                    health['warnings'].append(f"Files older than {max_age} days found")
                    
        except Exception as e:
            health['issues'].append(f"Content analysis failed: {e}")
        
        return health
    
    def run_health_check(self) -> Dict:
        """Run comprehensive health check on all FHS directories"""
        print("🏥 Running FHS Directory Health Check...")
        print("=" * 60)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'total_directories': len(self.fhs_directories),
            'healthy_directories': 0,
            'directories_with_issues': 0,
            'directories_with_warnings': 0,
            'directory_status': {},
            'summary': {}
        }
        
        total_size = 0
        total_files = 0
        all_issues = []
        all_warnings = []
        
        for directory in self.fhs_directories.keys():
            print(f"🔍 Checking: {directory}")
            health = self.check_directory_health(directory)
            results['directory_status'][directory] = health
            
            if health['exists'] and health['is_directory'] and not health['issues']:
                results['healthy_directories'] += 1
                print(f"   ✅ Healthy")
            else:
                results['directories_with_issues'] += 1
                print(f"   ❌ Issues found: {len(health['issues'])}")
                for issue in health['issues']:
                    print(f"      - {issue}")
                    all_issues.append(f"{directory}: {issue}")
            
            if health['warnings']:
                results['directories_with_warnings'] += 1
                print(f"   ⚠️  Warnings: {len(health['warnings'])}")
                for warning in health['warnings']:
                    print(f"      - {warning}")
                    all_warnings.append(f"{directory}: {warning}")
            
            total_size += health['size_mb']
            total_files += health['file_count']
        
        # Generate summary
        results['summary'] = {
            'total_size_mb': round(total_size, 2),
            'total_files': total_files,
            'health_percentage': round((results['healthy_directories'] / results['total_directories']) * 100, 1),
            'total_issues': len(all_issues),
            'total_warnings': len(all_warnings)
        }
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 HEALTH CHECK SUMMARY")
        print(f"   Total Directories: {results['total_directories']}")
        print(f"   Healthy: {results['healthy_directories']}")
        print(f"   With Issues: {results['directories_with_issues']}")
        print(f"   With Warnings: {results['directories_with_warnings']}")
        print(f"   Health Score: {results['summary']['health_percentage']}%")
        print(f"   Total Size: {results['summary']['total_size_mb']} MB")
        print(f"   Total Files: {results['summary']['total_files']}")
        
        if all_issues:
            print(f"\n🚨 ISSUES ({len(all_issues)}):")
            for issue in all_issues:
                print(f"   - {issue}")
        
        if all_warnings:
            print(f"\n⚠️  WARNINGS ({len(all_warnings)}):")
            for warning in all_warnings:
                print(f"   - {warning}")
        
        return results
    
    def repair_directory(self, directory: str) -> bool:
        """Repair a specific FHS directory"""
        print(f"🔧 Repairing directory: {directory}")
        
        dir_path = Path(directory)
        config = self.fhs_directories.get(directory, {})
        expected_perms = config.get('permissions', '755')
        
        success = True
        
        try:
            # Create directory if it doesn't exist
            if not dir_path.exists():
                print(f"   📁 Creating directory: {directory}")
                dir_path.mkdir(parents=True, exist_ok=True)
            
            # Ensure it's a directory
            if dir_path.exists() and not dir_path.is_dir():
                print(f"   ❌ Path exists but is not a directory: {directory}")
                return False
            
            # Fix permissions
            current_perms = oct(dir_path.stat().st_mode)[-3:]
            if current_perms != expected_perms:
                print(f"   🔐 Fixing permissions: {current_perms} -> {expected_perms}")
                dir_path.chmod(int(expected_perms, 8))
            
            # Create required subdirectories
            subdirs = config.get('subdirs', [])
            for subdir in subdirs:
                subdir_path = dir_path / subdir
                if not subdir_path.exists():
                    print(f"   📁 Creating subdirectory: {subdir}")
                    subdir_path.mkdir(parents=True, exist_ok=True)
                    subdir_path.chmod(int(expected_perms, 8))
            
            print(f"   ✅ Directory {directory} repaired successfully")
            
        except Exception as e:
            print(f"   ❌ Failed to repair {directory}: {e}")
            success = False
        
        return success
    
    def repair_all_directories(self) -> Dict:
        """Repair all FHS directories"""
        print("🔧 Repairing All FHS Directories...")
        print("=" * 60)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'total_directories': len(self.fhs_directories),
            'repaired_directories': 0,
            'failed_repairs': 0,
            'repair_details': {}
        }
        
        for directory in self.fhs_directories.keys():
            success = self.repair_directory(directory)
            results['repair_details'][directory] = {
                'success': success,
                'timestamp': datetime.now().isoformat()
            }
            
            if success:
                results['repaired_directories'] += 1
            else:
                results['failed_repairs'] += 1
        
        print("\n" + "=" * 60)
        print("📊 REPAIR SUMMARY")
        print(f"   Total Directories: {results['total_directories']}")
        print(f"   Repaired: {results['repaired_directories']}")
        print(f"   Failed: {results['failed_repairs']}")
        print(f"   Success Rate: {round((results['repaired_directories'] / results['total_directories']) * 100, 1)}%")
        
        return results
    
    def cleanup_temp_files(self, max_age_days: int = 7) -> Dict:
        """Clean up temporary files in FHS directories"""
        print(f"🧹 Cleaning up temporary files (older than {max_age_days} days)...")
        print("=" * 60)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'max_age_days': max_age_days,
            'files_deleted': 0,
            'space_freed_mb': 0,
            'cleanup_details': {}
        }
        
        # Focus on /tmp and /var/tmp directories
        temp_dirs = ['/tmp', 'var/tmp']
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        
        for temp_dir in temp_dirs:
            temp_path = Path(temp_dir)
            if not temp_path.exists():
                continue
            
            print(f"🔍 Cleaning: {temp_dir}")
            dir_results = {
                'files_scanned': 0,
                'files_deleted': 0,
                'space_freed_mb': 0
            }
            
            try:
                for item in temp_path.rglob('*'):
                    if item.is_file():
                        dir_results['files_scanned'] += 1
                        mtime = datetime.fromtimestamp(item.stat().st_mtime)
                        
                        if mtime < cutoff_time:
                            size_mb = item.stat().st_size / (1024 * 1024)
                            try:
                                item.unlink()
                                dir_results['files_deleted'] += 1
                                dir_results['space_freed_mb'] += size_mb
                                results['files_deleted'] += 1
                                results['space_freed_mb'] += size_mb
                            except Exception as e:
                                print(f"   ❌ Failed to delete {item}: {e}")
                
                results['cleanup_details'][temp_dir] = dir_results
                print(f"   📁 Scanned: {dir_results['files_scanned']} files")
                print(f"   🗑️  Deleted: {dir_results['files_deleted']} files")
                print(f"   💾 Freed: {round(dir_results['space_freed_mb'], 2)} MB")
                
            except Exception as e:
                print(f"   ❌ Cleanup failed for {temp_dir}: {e}")
                results['cleanup_details'][temp_dir] = {'error': str(e)}
        
        print("\n" + "=" * 60)
        print("📊 CLEANUP SUMMARY")
        print(f"   Files Deleted: {results['files_deleted']}")
        print(f"   Space Freed: {round(results['space_freed_mb'], 2)} MB")
        
        return results
    
    def generate_report(self, output_file: str = None) -> str:
        """Generate comprehensive FHS management report"""
        print("📋 Generating FHS Management Report...")
        
        # Run health check
        health_results = self.run_health_check()
        
        # Create report
        report = {
            'report_type': 'FHS Directory Management Report',
            'generated_at': datetime.now().isoformat(),
            'config_file': str(self.config_file),
            'health_check': health_results,
            'recommendations': self.generate_recommendations(health_results)
        }
        
        # Save report
        if output_file:
            report_path = Path(output_file)
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"📄 Report saved to: {report_path}")
        
        return json.dumps(report, indent=2, default=str)
    
    def generate_recommendations(self, health_results: Dict) -> List[str]:
        """Generate recommendations based on health check results"""
        recommendations = []
        
        # Check overall health
        health_pct = health_results['summary']['health_percentage']
        if health_pct < 100:
            recommendations.append(f"Overall health is {health_pct}% - run repair to fix {health_results['directories_with_issues']} directories with issues")
        
        # Check for specific issues
        for directory, status in health_results['directory_status'].items():
            if status['issues']:
                recommendations.append(f"Fix issues in {directory}: {', '.join(status['issues'])}")
            
            if status['warnings']:
                for warning in status['warnings']:
                    if 'size' in warning.lower():
                        recommendations.append(f"Consider cleanup for {directory} - {warning}")
                    elif 'older than' in warning.lower():
                        recommendations.append(f"Review old files in {directory} - {warning}")
        
        # General recommendations
        if health_results['summary']['total_size_mb'] > 1000:
            recommendations.append("Consider implementing regular cleanup schedules for large directories")
        
        if health_results['summary']['total_files'] > 10000:
            recommendations.append("Consider file organization strategies for directories with many files")
        
        return recommendations

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='FHS Directory Manager')
    parser.add_argument('--config', default='etc/machinenativeops/fhs-structure-config.yaml',
                       help='Path to FHS configuration file')
    parser.add_argument('--check', action='store_true',
                       help='Run health check on all FHS directories')
    parser.add_argument('--repair', action='store_true',
                       help='Repair all FHS directories')
    parser.add_argument('--cleanup', action='store_true',
                       help='Clean up temporary files')
    parser.add_argument('--cleanup-age', type=int, default=7,
                       help='Maximum age for cleanup (days)')
    parser.add_argument('--report', help='Generate report to file')
    parser.add_argument('--directory', help='Check specific directory')
    
    args = parser.parse_args()
    
    if not any([args.check, args.repair, args.cleanup, args.report, args.directory]):
        parser.print_help()
        return
    
    # Initialize manager
    manager = FHSDirectoryManager(args.config)
    
    # Execute commands
    if args.directory:
        health = manager.check_directory_health(args.directory)
        print(f"\n📊 Directory Health Report for {args.directory}:")
        print(json.dumps(health, indent=2, default=str))
    
    if args.check:
        manager.run_health_check()
    
    if args.repair:
        manager.repair_all_directories()
    
    if args.cleanup:
        manager.cleanup_temp_files(args.cleanup_age)
    
    if args.report:
        manager.generate_report(args.report)

if __name__ == "__main__":
    main()