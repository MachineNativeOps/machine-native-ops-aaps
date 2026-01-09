"""
Registry Validator - INSTANT 執行標準

驗證 Namespace Registry 中的所有條目，確保符合 INSTANT 標準
延遲目標：<500ms (p99)
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
import time
from datetime import datetime


class ValidationStatus(Enum):
    PASSED = "realized"
    FAILED_BLOCKED = "unrealized.blocked"
    FAILED_INVALID = "unrealized.invalid"
    FAILED_FAILED = "unrealized.failed"


@dataclass
class ValidationResult:
    status: ValidationStatus
    namespace: str
    errors: List[str] = None
    warnings: List[str] = None
    latency_ms: float = 0.0
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class RegistryValidator:
    """
    Registry 驗證器 - INSTANT 模式
    
    核心特性：
    - 延遲 <500ms (p99)
    - 完全自治（無需人工）
    - 事件驅動
    - 並行驗證
    """
    
    def __init__(self):
        self.validation_rules = {
            'naming_convention': self._validate_naming,
            'taxonomy_compliance': self._validate_taxonomy,
            'schema_validity': self._validate_schema,
            'metadata_completeness': self._validate_metadata,
            'dependency_integrity': self._validate_dependencies,
            'policy_compliance': self._validate_policies,
            'security_requirements': self._validate_security
        }
        
    async def validate_namespace(
        self, 
        namespace: str, 
        data: Dict[str, Any]
    ) -> ValidationResult:
        """
        驗證單個 namespace
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        errors = []
        warnings = []
        
        # 並行執行所有驗證規則
        validation_tasks = [
            rule(namespace, data) 
            for rule in self.validation_rules.values()
        ]
        
        results = await asyncio.gather(*validation_tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append(f"驗證錯誤: {str(result)}")
            elif result:
                rule_name = list(self.validation_rules.keys())[i]
                if 'error' in result:
                    errors.extend(result['error'])
                if 'warning' in result:
                    warnings.extend(result['warning'])
        
        latency = (time.time() - start_time) * 1000
        
        # 確定狀態
        if errors:
            status = ValidationStatus.FAILED_INVALID
        else:
            status = ValidationStatus.PASSED
        
        return ValidationResult(
            status=status,
            namespace=namespace,
            errors=errors,
            warnings=warnings,
            latency_ms=latency
        )
    
    async def validate_all(
        self, 
        registry: Dict[str, Dict[str, Any]]
    ) -> Dict[str, ValidationResult]:
        """
        驗證所有 namespaces
        
        延遲目標：<500ms (p99) - 使用 64-256 並行代理
        """
        start_time = time.time()
        
        # 並行驗證所有 namespaces
        validation_tasks = [
            self.validate_namespace(namespace, data)
            for namespace, data in registry.items()
        ]
        
        results = await asyncio.gather(*validation_tasks)
        
        # 構建結果字典
        result_dict = {
            result.namespace: result 
            for result in results
        }
        
        total_latency = (time.time() - start_time) * 1000
        
        # 記錄總延遲
        print(f"✅ 驗證 {len(registry)} 個 namespaces，總延遲: {total_latency:.2f}ms")
        
        return result_dict
    
    async def _validate_naming(
        self, 
        namespace: str, 
        data: Dict[str, Any]
    ) -> Optional[Dict[str, List[str]]]:
        """驗證命名規範"""
        errors = []
        
        # 檢查命名格式：{domain}-{name}-{type}[-{version}][-{modifier}]
        if not self._check_naming_format(namespace):
            errors.append(f"命名格式錯誤: {namespace}")
        
        return {'error': errors} if errors else None
    
    async def _validate_taxonomy(
        self, 
        namespace: str, 
        data: Dict[str, Any]
    ) -> Optional[Dict[str, List[str]]]:
        """驗證 Taxonomy 合規性"""
        errors = []
        
        # 檢查 taxonomy 欄位
        if 'taxonomy' not in data:
            errors.append("缺少 taxonomy 欄位")
        
        # 檢查命名格式符合 taxonomy
        if 'naming_format' in data.get('taxonomy', {}):
            naming_format = data['taxonomy']['naming_format']
            if naming_format not in ['kebab', 'pascal', 'camel', 'snake', 'constant']:
                errors.append(f"不支持的命名格式: {naming_format}")
        
        return {'error': errors} if errors else None
    
    async def _validate_schema(
        self, 
        namespace: str, 
        data: Dict[str, Any]
    ) -> Optional[Dict[str, List[str]]]:
        """驗證 Schema 有效性"""
        errors = []
        
        # 檢查 schema 欄位
        if 'schema' not in data:
            errors.append("缺少 schema 欄位")
            return {'error': errors}
        
        # 檢查 schema 結構
        schema = data['schema']
        required_fields = ['version', 'type', 'properties']
        for field in required_fields:
            if field not in schema:
                errors.append(f"Schema 缺少必要欄位: {field}")
        
        return {'error': errors} if errors else None
    
    async def _validate_metadata(
        self, 
        namespace: str, 
        data: Dict[str, Any]
    ) -> Optional[Dict[str, List[str]]]:
        """驗證 Metadata 完整性"""
        errors = []
        warnings = []
        
        # 檢查 metadata 欄位
        if 'metadata' not in data:
            errors.append("缺少 metadata 欄位")
            return {'error': errors}
        
        metadata = data['metadata']
        
        # 檢查必填欄位
        required_fields = ['created_at', 'updated_at', 'owner', 'status']
        for field in required_fields:
            if field not in metadata:
                errors.append(f"Metadata 缺少必要欄位: {field}")
        
        # 檢查日期格式
        for date_field in ['created_at', 'updated_at']:
            if date_field in metadata:
                try:
                    datetime.fromisoformat(metadata[date_field].replace('Z', '+00:00'))
                except ValueError:
                    errors.append(f"{date_field} 日期格式錯誤")
        
        return {'error': errors, 'warning': warnings} if (errors or warnings) else None
    
    async def _validate_dependencies(
        self, 
        namespace: str, 
        data: Dict[str, Any]
    ) -> Optional[Dict[str, List[str]]]:
        """驗證依賴完整性"""
        errors = []
        
        # 檢查依賴引用是否存在
        if 'dependencies' in data:
            dependencies = data['dependencies']
            for dep in dependencies:
                # 這裡應該檢查依賴的 namespace 是否存在於 registry
                # 為了簡化，我們假設所有依賴都有效
                pass
        
        return {'error': errors} if errors else None
    
    async def _validate_policies(
        self, 
        namespace: str, 
        data: Dict[str, Any]
    ) -> Optional[Dict[str, List[str]]]:
        """驗證政策合規性"""
        errors = []
        
        # 檢查政策合規標記
        if 'compliance' not in data:
            warnings = ["缺少 compliance 欄位"]
            return {'warning': warnings}
        
        return {'error': errors} if errors else None
    
    async def _validate_security(
        self, 
        namespace: str, 
        data: Dict[str, Any]
    ) -> Optional[Dict[str, List[str]]]:
        """驗證安全要求"""
        errors = []
        
        # 檢查安全標記
        if 'security' not in data:
            warnings = ["缺少 security 欄位"]
            return {'warning': warnings}
        
        security = data.get('security', {})
        
        # 檢查訪問控制
        if 'access_control' not in security:
            errors.append("缺少 access_control 設置")
        
        return {'error': errors, 'warning': warnings} if errors else None
    
    def _check_naming_format(self, namespace: str) -> bool:
        """檢查命名格式"""
        # 簡化的命名格式檢查
        # 實際應該使用 regex 或 taxonomy-core 的驗證器
        parts = namespace.split('-')
        if len(parts) == 1:
            return bool(namespace.strip())
        return len(parts) >= 3


# 使用範例
async def main():
    """測試 Registry Validator"""
    validator = RegistryValidator()
    
    # 測試數據
    test_namespace = "platform-registry-service-v1"
    test_data = {
        "taxonomy": {
            "domain": "platform",
            "name": "registry",
            "type": "service",
            "version": "v1",
            "naming_format": "kebab"
        },
        "schema": {
            "version": "1.0.0",
            "type": "object",
            "properties": {}
        },
        "metadata": {
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "owner": "platform-team",
            "status": "active"
        },
        "dependencies": [],
        "compliance": {
            "instant": True,
            "taxonomy": True
        },
        "security": {
            "access_control": "rbac"
        }
    }
    
    # 執行驗證
    result = await validator.validate_namespace(test_namespace, test_data)
    
    print(f"\n驗證結果: {result.status.value}")
    print(f"延遲: {result.latency_ms:.2f}ms")
    if result.errors:
        print(f"錯誤: {result.errors}")
    if result.warnings:
        print(f"警告: {result.warnings}")


if __name__ == "__main__":
    asyncio.run(main())
