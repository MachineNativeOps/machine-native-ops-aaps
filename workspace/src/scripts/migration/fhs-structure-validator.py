#!/usr/bin/env python3
"""
MachineNativeOps FHS 目錄結構驗證工具
驗證標準 FHS 目錄結構的完整性和合规性
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Set

class FHSStructureValidator:
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.fhs_directories = {
            "bin": {"description": "基本用戶命令二進制檔案", "required": True},
            "sbin": {"description": "系統管理二進制檔案", "required": True},
            "etc": {"description": "系統配置檔案", "required": True, "subdirs": ["network", "sysconfig", "cron.d"]},
            "lib": {"description": "共享函式庫", "required": True, "subdirs": ["modules", "firmware"]},
            "var": {"description": "變動資料", "required": True, "subdirs": ["log", "tmp", "cache", "lib", "spool", "run"]},
            "usr": {"description": "用戶程式", "required": True, "subdirs": ["bin", "sbin", "lib", "share", "local"]},
            "home": {"description": "用戶主目錄", "required": True},
            "tmp": {"description": "臨時檔案", "required": True},
            "opt": {"description": "可選應用程式", "required": True},
            "srv": {"description": "服務資料", "required": True, "subdirs": ["www", "ftp", "git"]},
            "init.d": {"description": "初始化腳本", "required": True}
        }
        
    def validate_directory_structure(self) -> Dict:
        """驗證目錄結構"""
        results = {
            "fhs_directories": {"valid": [], "missing": [], "invalid_subdirs": []},
            "summary": {"total_fhs": 0, "valid_fhs": 0}
        }
        
        for dir_name, dir_config in self.fhs_directories.items():
            dir_path = self.base_path / dir_name
            results["summary"]["total_fhs"] += 1
            
            if dir_path.exists() and dir_path.is_dir():
                results["fhs_directories"]["valid"].append({
                    "name": dir_name,
                    "description": dir_config["description"]
                })
                results["summary"]["valid_fhs"] += 1
                
                if "subdirs" in dir_config:
                    for subdir in dir_config["subdirs"]:
                        subdir_path = dir_path / subdir
                        if not (subdir_path.exists() and subdir_path.is_dir()):
                            results["fhs_directories"]["invalid_subdirs"].append({
                                "parent": dir_name,
                                "missing_subdir": subdir
                            })
            else:
                results["fhs_directories"]["missing"].append({
                    "name": dir_name,
                    "description": dir_config["description"]
                })
        
        return results
    
    def generate_report(self) -> str:
        """生成驗證報告"""
        structure_results = self.validate_directory_structure()
        
        report_lines = [
            "MachineNativeOps FHS 目錄結構驗證報告",
            "=" * 60,
            "",
            "## FHS 標準目錄",
            ""
        ]
        
        fhs_summary = structure_results["summary"]
        report_lines.extend([
            f"總計: {fhs_summary['total_fhs']} | 有效: {fhs_summary['valid_fhs']} | "
            f"完成率: {fhs_summary['valid_fhs']/fhs_summary['total_fhs']*100:.1f}%",
            ""
        ])
        
        if structure_results["fhs_directories"]["valid"]:
            report_lines.append("✅ 有效目錄:")
            for item in structure_results["fhs_directories"]["valid"]:
                report_lines.append(f"  - {item['name']}: {item['description']}")
        
        compliance_score = (fhs_summary["valid_fhs"] / fhs_summary["total_fhs"]) * 100
        report_lines.extend([
            "",
            f"## 合規性分數: {compliance_score:.1f}/100"
        ])
        
        return "\n".join(report_lines)

def main():
    validator = FHSStructureValidator()
    report = validator.generate_report()
    print(report)
    
    structure_results = validator.validate_directory_structure()
    compliance_score = (structure_results["summary"]["valid_fhs"] / structure_results["summary"]["total_fhs"]) * 100
    
    if compliance_score >= 90:
        sys.exit(0)
    elif compliance_score >= 70:
        sys.exit(1)
    else:
        sys.exit(2)

if __name__ == "__main__":
    main()
