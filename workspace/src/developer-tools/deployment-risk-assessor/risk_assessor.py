# ==============================================================================
# 部署風險評估系統 - 高階開發者工具
# Deployment Risk Assessment System - Advanced Developer Tool
# ==============================================================================

import os
import re
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import requests
import logging
from collections import defaultdict

import yaml
import git
from github import Github
import prometheus_client
from prometheus_client import CollectorRegistry, Gauge, Counter


class RiskLevel(Enum):
    """風險等級"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DeploymentType(Enum):
    """部署類型"""
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    ROLLING = "rolling"
    RECREATE = "recreate"


@dataclass
class RiskFactor:
    """風險因子"""
    name: str
    description: str
    weight: float
    value: float
    impact: str
    recommendations: List[str]


@dataclass
class RiskAssessment:
    """風險評估結果"""
    deployment_id: str
    timestamp: datetime
    environment: str
    deployment_type: DeploymentType
    overall_risk_level: RiskLevel
    risk_score: float
    risk_factors: List[RiskFactor]
    mitigation_strategies: List[str]
    approval_required: bool
    estimated_rollback_time: int
    deployment_impact: Dict[str, Any]


@dataclass
class ChangeImpact:
    """變更影響分析"""
    commit_count: int
    files_changed: int
    lines_added: int
    lines_removed: int
    hotfixes: int
    breaking_changes: int
    database_migrations: int
    config_changes: int
    test_coverage_impact: float


class DeploymentRiskAssessor:
    """部署風險評估器核心類"""
    
    def __init__(self, config_path: str = "config/risk-assessor-config.yaml"):
        self.config = self._load_config(config_path)
        self.github_client = self._init_github_client()
        self.logger = self._setup_logger()
        self.metrics_registry = CollectorRegistry()
        self._setup_metrics()
        self.assessment_history = []
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """載入配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # 默認配置
            return {
                'github': {
                    'token': os.getenv('GITHUB_TOKEN'),
                    'repo': os.getenv('GITHUB_REPO', 'MachineNativeOps/MachineNativeOps')
                },
                'risk_thresholds': {
                    'low': 30,
                    'medium': 60,
                    'high': 80,
                    'critical': 90
                },
                'risk_factors': {
                    'code_change_impact': 0.25,
                    'test_coverage': 0.20,
                    'security_vulnerabilities': 0.20,
                    'performance_impact': 0.15,
                    'deployment_complexity': 0.10,
                    'environment_stability': 0.10
                },
                'monitoring': {
                    'prometheus_url': os.getenv('PROMETHEUS_URL'),
                    'grafana_url': os.getenv('GRAFANA_URL'),
                    'metrics_lookback_hours': 24
                },
                'approval_workflow': {
                    'require_approval_for_high_risk': True,
                    'approvers': ['tech-lead', 'devops-lead'],
                    'auto_approval_threshold': 30
                }
            }
    
    def _init_github_client(self) -> Github:
        """初始化 GitHub 客戶端"""
        token = self.config['github']['token']
        if token:
            return Github(token)
        return Github()
    
    def _setup_logger(self) -> logging.Logger:
        """設置日誌記錄器"""
        logger = logging.getLogger('DeploymentRiskAssessor')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _setup_metrics(self):
        """設置 Prometheus 指標"""
        self.risk_score_gauge = Gauge(
            'deployment_risk_score',
            'Current deployment risk score',
            ['environment', 'deployment_type'],
            registry=self.metrics_registry
        )
        
        self.assessment_counter = Counter(
            'risk_assessments_total',
            'Total number of risk assessments performed',
            ['risk_level'],
            registry=self.metrics_registry
        )
    
    def assess_deployment_risk(
        self,
        commit_sha: str,
        target_environment: str,
        deployment_type: DeploymentType = DeploymentType.ROLLING
    ) -> RiskAssessment:
        """評估部署風險"""
        self.logger.info(f"開始評估部署風險 - Commit: {commit_sha}, Environment: {target_environment}")
        
        deployment_id = self._generate_deployment_id(commit_sha, target_environment)
        
        # 分析代碼變更
        change_impact = self._analyze_code_changes(commit_sha)
        
        # 評估各種風險因子
        risk_factors = []
        
        # 代碼變更影響風險
        code_change_risk = self._assess_code_change_risk(change_impact)
        risk_factors.append(code_change_risk)
        
        # 測試覆蓋率風險
        coverage_risk = self._assess_test_coverage_risk(commit_sha)
        risk_factors.append(coverage_risk)
        
        # 安全漏洞風險
        security_risk = self._assess_security_risk(commit_sha)
        risk_factors.append(security_risk)
        
        # 性能影響風險
        performance_risk = self._assess_performance_risk(commit_sha)
        risk_factors.append(performance_risk)
        
        # 部署複雜度風險
        complexity_risk = self._assess_deployment_complexity_risk(deployment_type)
        risk_factors.append(complexity_risk)
        
        # 環境穩定性風險
        stability_risk = self._assess_environment_stability_risk(target_environment)
        risk_factors.append(stability_risk)
        
        # 計算總體風險分數
        overall_risk_score = self._calculate_overall_risk_score(risk_factors)
        risk_level = self._determine_risk_level(overall_risk_score)
        
        # 生成緩解策略
        mitigation_strategies = self._generate_mitigation_strategies(risk_factors)
        
        # 評估回滾時間
        rollback_time = self._estimate_rollback_time(deployment_type, change_impact)
        
        # 分析部署影響
        deployment_impact = self._analyze_deployment_impact(change_impact, deployment_type)
        
        # 確定是否需要審批
        approval_required = self._requires_approval(risk_level, overall_risk_score)
        
        # 創建評估結果
        assessment = RiskAssessment(
            deployment_id=deployment_id,
            timestamp=datetime.now(),
            environment=target_environment,
            deployment_type=deployment_type,
            overall_risk_level=risk_level,
            risk_score=overall_risk_score,
            risk_factors=risk_factors,
            mitigation_strategies=mitigation_strategies,
            approval_required=approval_required,
            estimated_rollback_time=rollback_time,
            deployment_impact=deployment_impact
        )
        
        # 更新指標
        self._update_metrics(assessment)
        
        # 保存評估歷史
        self.assessment_history.append(assessment)
        
        self.logger.info(f"風險評估完成 - 風險分數: {overall_risk_score:.1f}, 風險等級: {risk_level.value}")
        
        return assessment
    
    def _generate_deployment_id(self, commit_sha: str, environment: str) -> str:
        """生成部署 ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"deploy_{timestamp}_{commit_sha[:8]}_{environment}"
    
    def _analyze_code_changes(self, commit_sha: str) -> ChangeImpact:
        """分析代碼變更"""
        try:
            repo = git.Repo('.')
            
            # 獲取變更統計
            diff = repo.git.diff('--stat', f'{commit_sha}^', commit_sha)
            lines = diff.strip().split('\n')
            
            files_changed = 0
            lines_added = 0
            lines_removed = 0
            
            for line in lines:
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 2:
                        stats = parts[1].strip()
                        if '+' in stats or '-' in stats:
                            files_changed += 1
                            # 解析添加/刪除的行數
                            match = re.search(r'(\d+)\s+insertion\(\+\)', stats)
                            if match:
                                lines_added += int(match.group(1))
                            match = re.search(r'(\d+)\s+deletion\(-\)', stats)
                            if match:
                                lines_removed += int(match.group(1))
            
            # 獲取提交歷史
            commits = list(repo.iter_commits(f'{commit_sha}^..{commit_sha}'))
            commit_count = len(commits)
            
            # 分析變更類型
            hotfixes = 0
            breaking_changes = 0
            database_migrations = 0
            config_changes = 0
            
            for commit in commits:
                # 檢查是否為熱修復
                if any(keyword in commit.message.lower() for keyword in ['hotfix', 'urgent', 'critical']):
                    hotfixes += 1
                
                # 檢查破壞性變更
                if any(keyword in commit.message.lower() for keyword in ['breaking', 'breaking-change', 'api-change']):
                    breaking_changes += 1
                
                # 檢查數據庫遷移
                for item in commit.stats.files:
                    if 'migration' in item.lower() or 'schema' in item.lower():
                        database_migrations += 1
                
                # 檢查配置變更
                for item in commit.stats.files:
                    if any(ext in item.lower() for ext in ['.yaml', '.yml', '.json', '.env']):
                        config_changes += 1
            
            # 評估測試覆蓋率影響（簡化實現）
            test_coverage_impact = min(10.0, files_changed * 0.5)
            
            return ChangeImpact(
                commit_count=commit_count,
                files_changed=files_changed,
                lines_added=lines_added,
                lines_removed=lines_removed,
                hotfixes=hotfixes,
                breaking_changes=breaking_changes,
                database_migrations=database_migrations,
                config_changes=config_changes,
                test_coverage_impact=test_coverage_impact
            )
            
        except Exception as e:
            self.logger.error(f"分析代碼變更失敗: {e}")
            return ChangeImpact(0, 0, 0, 0, 0, 0, 0, 0, 0)
    
    def _assess_code_change_risk(self, impact: ChangeImpact) -> RiskFactor:
        """評估代碼變更風險"""
        weight = self.config['risk_factors']['code_change_impact']
        
        # 計算變更分數
        change_score = 0
        
        # 基於文件變更數量
        if impact.files_changed > 50:
            change_score += 30
        elif impact.files_changed > 20:
            change_score += 20
        elif impact.files_changed > 10:
            change_score += 10
        
        # 基於行數變更
        total_lines = impact.lines_added + impact.lines_removed
        if total_lines > 1000:
            change_score += 25
        elif total_lines > 500:
            change_score += 15
        elif total_lines > 100:
            change_score += 5
        
        # 破壞性變更影響
        change_score += impact.breaking_changes * 20
        
        # 數據庫遷移風險
        change_score += impact.database_migrations * 15
        
        # 熱修復風險
        change_score += impact.hotfixes * 10
        
        value = min(100, change_score)
        
        # 生成建議
        recommendations = []
        if impact.breaking_changes > 0:
            recommendations.append("考慮分階段部署破壞性變更")
        if impact.database_migrations > 0:
            recommendations.append("確保數據庫遷移腳本已充分測試")
        if impact.files_changed > 20:
            recommendations.append("考慮將大型變更拆分為多個較小的部署")
        
        impact_desc = "高" if value > 70 else "中" if value > 40 else "低"
        
        return RiskFactor(
            name="代碼變更影響",
            description=f"代碼變更規模和複雜度帶來的風險 - 影響級別: {impact_desc}",
            weight=weight,
            value=value,
            impact=impact_desc,
            recommendations=recommendations
        )
    
    def _assess_test_coverage_risk(self, commit_sha: str) -> RiskFactor:
        """評估測試覆蓋率風險"""
        weight = self.config['risk_factors']['test_coverage']
        
        # 這裡應該集成實際的測試覆蓋率報告
        # 簡化實現，假設覆蓋率基於某些規則
        coverage_score = 75  # 假設當前覆蓋率
        risk_value = max(0, 100 - coverage_score)
        
        recommendations = []
        if coverage_score < 60:
            recommendations = [
                "增加單元測試覆蓋率",
                "添加集成測試",
                "確保關鍵路徑都有測試覆蓋"
            ]
        elif coverage_score < 80:
            recommendations = [
                "提高邊界條件測試覆蓋",
                "添加異常處理測試"
            ]
        
        impact_desc = "高" if risk_value > 70 else "中" if risk_value > 40 else "低"
        
        return RiskFactor(
            name="測試覆蓋率",
            description=f"測試覆蓋率不足可能導致的生產問題 - 覆蓋率: {coverage_score}%",
            weight=weight,
            value=risk_value,
            impact=impact_desc,
            recommendations=recommendations
        )
    
    def _assess_security_risk(self, commit_sha: str) -> RiskFactor:
        """評估安全風險"""
        weight = self.config['risk_factors']['security_vulnerabilities']
        
        # 這裡應該集成安全掃描結果
        # 簡化實現，基於一些規則評估
        security_issues = 2  # 假設發現的安全問題數
        risk_value = min(100, security_issues * 25)
        
        recommendations = []
        if security_issues > 0:
            recommendations = [
                "修復已發現的安全漏洞",
                "運行完整的安全掃描",
                "審權限和認證邏輯"
            ]
        
        impact_desc = "高" if risk_value > 70 else "中" if risk_value > 40 else "低"
        
        return RiskFactor(
            name="安全漏洞",
            description=f"代碼中可能存在的安全問題 - 發現 {security_issues} 個問題",
            weight=weight,
            value=risk_value,
            impact=impact_desc,
            recommendations=recommendations
        )
    
    def _assess_performance_risk(self, commit_sha: str) -> RiskFactor:
        """評估性能影響風險"""
        weight = self.config['risk_factors']['performance_impact']
        
        # 這裡應該集成性能測試結果
        # 簡化實現，基於變更類型評估
        performance_impact_score = 30  # 假設的性能影響分數
        risk_value = performance_impact_score
        
        recommendations = []
        if performance_impact_score > 50:
            recommendations = [
                "執行性能基準測試",
                "監控關鍵性能指標",
                "準備性能回滾方案"
            ]
        
        impact_desc = "高" if risk_value > 70 else "中" if risk_value > 40 else "低"
        
        return RiskFactor(
            name="性能影響",
            description=f"代碼變更可能對系統性能造成的影響",
            weight=weight,
            value=risk_value,
            impact=impact_desc,
            recommendations=recommendations
        )
    
    def _assess_deployment_complexity_risk(self, deployment_type: DeploymentType) -> RiskFactor:
        """評估部署複雜度風險"""
        weight = self.config['risk_factors']['deployment_complexity']
        
        # 基於部署類型評估複雜度
        complexity_scores = {
            DeploymentType.ROLLING: 20,
            DeploymentType.BLUE_GREEN: 40,
            DeploymentType.CANARY: 60,
            DeploymentType.RECREATE: 80
        }
        
        risk_value = complexity_scores.get(deployment_type, 50)
        
        recommendations = {
            DeploymentType.ROLLING: ["確保服務向下兼容", "監控部署進程"],
            DeploymentType.BLUE_GREEN: ["驗證綠色環境", "準備快速切換方案"],
            DeploymentType.CANARY: ["設置流量控制", "密切監控早期指標"],
            DeploymentType.RECREATE: ["通知用戶維護窗口", "準備快速恢復"]
        }.get(deployment_type, [])
        
        impact_desc = "高" if risk_value > 70 else "中" if risk_value > 40 else "低"
        
        return RiskFactor(
            name="部署複雜度",
            description=f"{deployment_type.value} 部署模式的複雜性和風險",
            weight=weight,
            value=risk_value,
            impact=impact_desc,
            recommendations=recommendations
        )
    
    def _assess_environment_stability_risk(self, environment: str) -> RiskFactor:
        """評估環境穩定性風險"""
        weight = self.config['risk_factors']['environment_stability']
        
        # 基於環境類型評估穩定性
        stability_scores = {
            'development': 10,
            'staging': 30,
            'production': 50,
            'production-critical': 80
        }
        
        risk_value = stability_scores.get(environment.lower(), 40)
        
        recommendations = []
        if environment.lower().startswith('production'):
            recommendations = [
                "確保完整的監控覆蓋",
                "準備緊急回滾程序",
                "安排值班人員監控"
            ]
        
        impact_desc = "高" if risk_value > 70 else "中" if risk_value > 40 else "低"
        
        return RiskFactor(
            name="環境穩定性",
            description=f"{environment} 環境的穩定性風險",
            weight=weight,
            value=risk_value,
            impact=impact_desc,
            recommendations=recommendations
        )
    
    def _calculate_overall_risk_score(self, risk_factors: List[RiskFactor]) -> float:
        """計算總體風險分數"""
        total_score = 0
        for factor in risk_factors:
            total_score += factor.value * factor.weight
        
        return min(100, total_score)
    
    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """確定風險等級"""
        thresholds = self.config['risk_thresholds']
        
        if risk_score >= thresholds['critical']:
            return RiskLevel.CRITICAL
        elif risk_score >= thresholds['high']:
            return RiskLevel.HIGH
        elif risk_score >= thresholds['medium']:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _generate_mitigation_strategies(self, risk_factors: List[RiskFactor]) -> List[str]:
        """生成緩解策略"""
        strategies = []
        
        # 收集所有高風險因子的建議
        for factor in risk_factors:
            if factor.value > 60:
                strategies.extend(factor.recommendations)
        
        # 通用緩解策略
        high_risk_factors = [f for f in risk_factors if f.value > 70]
        if high_risk_factors:
            strategies.extend([
                "考慮分階段部署",
                "增強監控和告警",
                "準備回滾方案",
                "安排專門監控人員"
            ])
        
        # 去重
        return list(set(strategies))
    
    def _estimate_rollback_time(self, deployment_type: DeploymentType, impact: ChangeImpact) -> int:
        """估算回滾時間（分鐘）"""
        base_times = {
            DeploymentType.ROLLING: 15,
            DeploymentType.BLUE_GREEN: 5,
            DeploymentType.CANARY: 10,
            DeploymentType.RECREATE: 20
        }
        
        base_time = base_times.get(deployment_type, 15)
        
        # 根據變更規模調整
        if impact.files_changed > 50:
            base_time *= 1.5
        elif impact.files_changed > 20:
            base_time *= 1.2
        
        if impact.database_migrations > 0:
            base_time += 10  # 數據庫回滾需要更多時間
        
        return int(base_time)
    
    def _analyze_deployment_impact(self, impact: ChangeImpact, deployment_type: DeploymentType) -> Dict[str, Any]:
        """分析部署影響"""
        return {
            'expected_downtime_minutes': {
                DeploymentType.ROLLING: 0,
                DeploymentType.BLUE_GREEN: 0,
                DeploymentType.CANARY: 0,
                DeploymentType.RECREATE: 5
            }.get(deployment_type, 0),
            'user_impact': 'minimal' if deployment_type != DeploymentType.RECREATE else 'full',
            'affected_services': impact.files_changed,  # 簡化
            'estimated_risk_users': 'low' if impact.breaking_changes == 0 else 'high'
        }
    
    def _requires_approval(self, risk_level: RiskLevel, risk_score: float) -> bool:
        """判斷是否需要審批"""
        if not self.config['approval_workflow']['require_approval_for_high_risk']:
            return False
        
        return risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] or risk_score > self.config['approval_workflow']['auto_approval_threshold']
    
    def _update_metrics(self, assessment: RiskAssessment):
        """更新 Prometheus 指標"""
        self.risk_score_gauge.labels(
            environment=assessment.environment,
            deployment_type=assessment.deployment_type.value
        ).set(assessment.risk_score)
        
        self.assessment_counter.labels(
            risk_level=assessment.overall_risk_level.value
        ).inc()
    
    def generate_risk_report(self, assessment: RiskAssessment) -> str:
        """生成風險評估報告"""
        report = f"""
# 部署風險評估報告

## 基本信息
- **部署ID**: {assessment.deployment_id}
- **評估時間**: {assessment.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
- **目標環境**: {assessment.environment}
- **部署類型**: {assessment.deployment_type.value}
- **總體風險等級**: {assessment.overall_risk_level.value.upper()}
- **風險分數**: {assessment.risk_score:.1f}/100

## 風險因子分析
"""
        
        for factor in assessment.risk_factors:
            report += f"""
### {factor.name}
- **描述**: {factor.description}
- **權重**: {factor.weight:.2f}
- **分數**: {factor.value:.1f}
- **影響級別**: {factor.impact}
- **建議**: {', '.join(factor.recommendations)}
"""
        
        report += f"""
## 緩解策略
{chr(10).join(f"- {strategy}" for strategy in assessment.mitigation_strategies)}

## 部署影響分析
- **預計停機時間**: {assessment.deployment_impact['expected_downtime_minutes']} 分鐘
- **用戶影響**: {assessment.deployment_impact['user_impact']}
- **受影響服務數**: {assessment.deployment_impact['affected_services']}
- **預計受影響用戶**: {assessment.deployment_impact['estimated_risk_users']}
- **預計回滾時間**: {assessment.estimated_rollback_time} 分鐘

## 審批要求
- **需要審批**: {'是' if assessment.approval_required else '否'}
"""
        
        if assessment.approval_required:
            report += f"- **審批人**: {', '.join(self.config['approval_workflow']['approvers'])}\n"
        
        return report
    
    def export_assessment(self, assessment: RiskAssessment, output_path: str, format_type: str = 'json'):
        """導出評估結果"""
        output_data = asdict(assessment)
        output_data['timestamp'] = assessment.timestamp.isoformat()
        output_data['deployment_type'] = assessment.deployment_type.value
        output_data['overall_risk_level'] = assessment.overall_risk_level.value
        
        if format_type.lower() == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
        elif format_type.lower() == 'yaml':
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(output_data, f, default_flow_style=False, allow_unicode=True)
        
        self.logger.info(f"評估結果已導出到: {output_path}")


# 使用示例
if __name__ == "__main__":
    # 初始化風險評估器
    assessor = DeploymentRiskAssessor()
    
    # 評估部署風險
    assessment = assessor.assess_deployment_risk(
        commit_sha="abc123def456",
        target_environment="staging",
        deployment_type=DeploymentType.CANARY
    )
    
    # 生成報告
    report = assessor.generate_risk_report(assessment)
    print(report)
    
    # 導出結果
    assessor.export_assessment(assessment, "risk_assessment.json", "json")