"""
Schema Versioning - INSTANT 執行標準

Schema 版本管理系統
延遲目標：<100ms (p99) 版本操作
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
import time
from datetime import datetime
from packaging import version


class VersionChangeType(Enum):
    """版本變更類型"""
    MAJOR = "major"  # 破壞性變更
    MINOR = "minor"  # 新功能
    PATCH = "patch"  # 修補
    PRERELEASE = "prerelease"  # 預發布


@dataclass
class VersionChange:
    """版本變更"""
    from_version: str
    to_version: str
    change_type: VersionChangeType
    changes: List[str]
    timestamp: datetime
    author: str


class SchemaVersioning:
    """
    Schema Versioning - INSTANT 模式
    
    核心特性：
    - 延遲 <100ms (p99)
    - 語義化版本控制 (SemVer)
    - 自動版本推斷
    - 向後兼容性檢查
    - 完全自治
    """
    
    def __init__(self):
        # 版本歷史
        self.version_history: Dict[str, List[VersionChange]] = {}
        
        # 版本鎖（防止並發修改）
        self.version_locks: Dict[str, asyncio.Lock] = {}
        
        # 統計
        self.stats = {
            'total_versions': 0,
            'major_changes': 0,
            'minor_changes': 0,
            'patch_changes': 0,
            'incompatibilities': 0
        }
    
    async def create_version(
        self,
        schema_id: str,
        current_version: str,
        changes: List[str],
        author: str = "system"
    ) -> str:
        """
        創建新版本
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        
        # 1. 分析變更類型
        change_type = await self._analyze_change_type(changes)
        
        # 2. 計算新版本號
        last_to_version = None
        if schema_id in self.version_history and self.version_history[schema_id]:
            last_to_version = self.version_history[schema_id][-1].to_version

        if last_to_version:
            try:
                current_parsed = version.parse(current_version)
                last_parsed = version.parse(last_to_version)
                if current_parsed > last_parsed:
                    new_version = current_version
                else:
                    new_version = await self._calculate_next_version(
                        current_version,
                        change_type
                    )
            except Exception:
                new_version = await self._calculate_next_version(
                    current_version,
                    change_type
                )
        else:
            new_version = await self._calculate_next_version(
                current_version,
                change_type
            )
        
        # 3. 記錄變更
        version_change = VersionChange(
            from_version=current_version,
            to_version=new_version,
            change_type=change_type,
            changes=changes,
            timestamp=datetime.now(),
            author=author
        )
        
        # 4. 存儲版本歷史
        if schema_id not in self.version_history:
            self.version_history[schema_id] = []
        
        self.version_history[schema_id].append(version_change)
        
        # 5. 更新統計
        self.stats['total_versions'] += 1
        if change_type == VersionChangeType.MAJOR:
            self.stats['major_changes'] += 1
        elif change_type == VersionChangeType.MINOR:
            self.stats['minor_changes'] += 1
        elif change_type == VersionChangeType.PATCH:
            self.stats['patch_changes'] += 1
        
        latency = (time.time() - start_time) * 1000
        print(f"✅ 創建版本: {current_version} → {new_version} ({change_type.value})，延遲: {latency:.2f}ms")
        
        return new_version
    
    async def check_compatibility(
        self,
        schema_id: str,
        from_version: str,
        to_version: str
    ) -> bool:
        """
        檢查版本兼容性
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        
        # 解析版本號
        try:
            v1 = version.parse(from_version)
            v2 = version.parse(to_version)
        except Exception:
            print(f"❌ 無效的版本號: {from_version} 或 {to_version}")
            return False
        
        # 檢查主版本號
        if v1.major != v2.major:
            self.stats['incompatibilities'] += 1
            latency = (time.time() - start_time) * 1000
            print(f"❌ 不兼容: {from_version} → {to_version} (主版本號不同)，延遲: {latency:.2f}ms")
            return False
        
        latency = (time.time() - start_time) * 1000
        print(f"✅ 兼容: {from_version} → {to_version}，延遲: {latency:.2f}ms")
        
        return True
    
    async def get_version_history(
        self,
        schema_id: str,
        limit: int = 10
    ) -> List[VersionChange]:
        """
        獲取版本歷史
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        
        if schema_id not in self.version_history:
            return []
        
        history = self.version_history[schema_id]
        
        # 返回最近的 N 條記錄
        recent = history[-limit:] if limit else history
        
        latency = (time.time() - start_time) * 1000
        print(f"✅ 獲取版本歷史: {len(recent)} 條記錄，延遲: {latency:.2f}ms")
        
        return recent
    
    async def get_latest_version(self, schema_id: str) -> Optional[str]:
        """
        獲取最新版本
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        
        if schema_id not in self.version_history:
            return None
        
        history = self.version_history[schema_id]
        
        if not history:
            return None
        
        latest = history[-1].to_version
        
        latency = (time.time() - start_time) * 1000
        print(f"✅ 最新版本: {latest}，延遲: {latency:.2f}ms")
        
        return latest
    
    async def compare_versions(
        self,
        version1: str,
        version2: str
    ) -> str:
        """
        比較兩個版本
        
        延遲目標：<100ms (p99)
        
        返回: ">", "<", 或 "="
        """
        start_time = time.time()
        
        try:
            v1 = version.parse(version1)
            v2 = version.parse(version2)
            
            if v1 > v2:
                result = ">"
            elif v1 < v2:
                result = "<"
            else:
                result = "="
            
            latency = (time.time() - start_time) * 1000
            print(f"✅ 版本比較: {version1} {result} {version2}，延遲: {latency:.2f}ms")
            
            return result
            
        except Exception as e:
            print(f"❌ 版本比較錯誤: {e}")
            return "error"
    
    async def suggest_next_version(
        self,
        schema_id: str,
        current_version: str,
        changes: List[str]
    ) -> str:
        """
        建議下一個版本號
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        
        # 分析變更類型
        change_type = await self._analyze_change_type(changes)
        
        # 計算下一版本
        next_version = await self._calculate_next_version(
            current_version,
            change_type
        )
        
        latency = (time.time() - start_time) * 1000
        print(f"✅ 建議版本: {current_version} → {next_version} ({change_type.value})，延遲: {latency:.2f}ms")
        
        return next_version
    
    async def _analyze_change_type(
        self,
        changes: List[str]
    ) -> VersionChangeType:
        """分析變更類型"""
        # 破壞性變更關鍵詞
        breaking_keywords = [
            'break', 'remove', 'delete', 'deprecate',
            'breaking', 'incompatible', 'major'
        ]
        
        # 新功能關鍵詞
        feature_keywords = [
            'add', 'new', 'feature', 'enhance',
            'extend', 'implement', 'minor'
        ]
        
        # 修補關鍵詞
        patch_keywords = [
            'fix', 'bug', 'patch', 'update',
            'correct', 'improve'
        ]
        
        # 分析變更描述
        has_breaking = any(
            any(keyword in change.lower() for keyword in breaking_keywords)
            for change in changes
        )
        
        has_feature = any(
            any(keyword in change.lower() for keyword in feature_keywords)
            for change in changes
        )
        
        has_patch = any(
            any(keyword in change.lower() for keyword in patch_keywords)
            for change in changes
        )
        
        # 確定變更類型
        if has_breaking:
            return VersionChangeType.MAJOR
        elif has_feature:
            return VersionChangeType.MINOR
        elif has_patch:
            return VersionChangeType.PATCH
        else:
            return VersionChangeType.PATCH  # 默認為 patch
    
    async def _calculate_next_version(
        self,
        current_version: str,
        change_type: VersionChangeType
    ) -> str:
        """計算下一個版本號"""
        try:
            v = version.parse(current_version)
            
            if change_type == VersionChangeType.MAJOR:
                next_version = f"{v.major + 1}.0.0"
            elif change_type == VersionChangeType.MINOR:
                next_version = f"{v.major}.{v.minor + 1}.0"
            elif change_type == VersionChangeType.PATCH:
                next_version = f"{v.major}.{v.minor}.{v.micro + 1}"
            else:  # PRERELEASE
                next_version = f"{v.major}.{v.minor}.{v.micro}.dev0"
            
            return next_version
            
        except Exception:
            # 無法解析版本，返回默認值
            return "1.0.0"
    
    async def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return self.stats.copy()


# 使用範例
async def main():
    """測試 Schema Versioning"""
    versioning = SchemaVersioning()
    
    print("\n=== 測試 Schema Versioning ===\n")
    
    schema_id = "namespace-schema"
    
    # 1. 創建初始版本
    v1 = await versioning.create_version(
        schema_id,
        "0.0.0",
        ["Initial version"],
        "system"
    )
    
    # 2. 創建補丁版本
    v2 = await versioning.create_version(
        schema_id,
        v1,
        ["Fix validation bug"],
        "developer1"
    )
    
    # 3. 創建次版本
    v3 = await versioning.create_version(
        schema_id,
        v2,
        ["Add new field: description"],
        "developer2"
    )
    
    # 4. 創建主版本
    v4 = await versioning.create_version(
        schema_id,
        v3,
        ["Break change: Remove deprecated field"],
        "architect"
    )
    
    # 5. 檢查兼容性
    compatible = await versioning.check_compatibility(schema_id, v1, v2)
    print(f"\n✅ v1 → v2 兼容: {compatible}")
    
    compatible = await versioning.check_compatibility(schema_id, v1, v4)
    print(f"✅ v1 → v4 兼容: {compatible}")
    
    # 6. 獲取版本歷史
    history = await versioning.get_version_history(schema_id)
    print(f"\n📜 版本歷史:")
    for change in history:
        print(f"  {change.from_version} → {change.to_version} ({change.change_type.value})")
    
    # 7. 獲取最新版本
    latest = await versioning.get_latest_version(schema_id)
    print(f"\n📌 最新版本: {latest}")
    
    # 8. 比較版本
    comparison = await versioning.compare_versions("1.0.0", "2.0.0")
    print(f"\n🔍 1.0.0 vs 2.0.0: {comparison}")
    
    # 9. 建議下一版本
    suggested = await versioning.suggest_next_version(
        schema_id,
        latest,
        ["Add new feature"]
    )
    print(f"\n💡 建議下一版本: {suggested}")
    
    # 10. 獲取統計
    stats = await versioning.get_stats()
    print(f"\n📊 統計信息:")
    print(f"  總版本數: {stats['total_versions']}")
    print(f"  主版本變更: {stats['major_changes']}")
    print(f"  次版本變更: {stats['minor_changes']}")
    print(f"  補丁變更: {stats['patch_changes']}")


if __name__ == "__main__":
    asyncio.run(main())
