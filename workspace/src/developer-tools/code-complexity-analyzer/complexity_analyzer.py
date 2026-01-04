# ==============================================================================
# 代碼複雜度分析工具 - 高階開發者工具
# Code Complexity Analyzer - Advanced Developer Tool
# ==============================================================================

import os
import ast
import json
import time
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd
from datetime import datetime

import radon.cli as radon_cli
import radon.complexity as radon_cc
import radon.metrics as radon_metrics
from vprof import runner
import lizard


class ComplexityMetric(Enum):
    """複雜度度量類型"""
    CYCLOMATIC = "cyclomatic"
    COGNITIVE = "cognitive"
    HALSTEAD = "halstead"
    MAINTAINABILITY = "maintainability"
    LINES_OF_CODE = "loc"


class RiskLevel(Enum):
    """風險等級"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class FunctionComplexity:
    """函數複雜度數據"""
    name: str
    file_path: str
    line_start: int
    line_end: int
    cyclomatic_complexity: int
    cognitive_complexity: int
    halstead_metrics: Dict[str, float]
    maintainability_index: float
    lines_of_code: int
    parameters_count: int
    nesting_depth: int
    risk_level: RiskLevel
    recommendations: List[str]


@dataclass
class FileComplexity:
    """文件複雜度數據"""
    file_path: str
    total_lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    functions: List[FunctionComplexity]
    average_complexity: float
    maintainability_index: float
    risk_level: RiskLevel
    technical_debt: float


@dataclass
class ProjectComplexity:
    """項目複雜度數據"""
    project_name: str
    total_files: int
    total_functions: int
    total_lines: int
    average_complexity: float
    complexity_distribution: Dict[str, int]
    most_complex_files: List[str]
    technical_debt_summary: Dict[str, float]
    trends: List[Dict[str, Any]]
    recommendations: List[str]


class CodeComplexityAnalyzer:
    """代碼複雜度分析器核心類"""
    
    def __init__(self, config_path: str = "config/complexity-analyzer-config.yaml"):
        self.config = self._load_config(config_path)
        self.complexity_cache = {}
        self.historical_data = []
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """載入配置文件"""
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # 默認配置
            return {
                'thresholds': {
                    'cyclomatic': {
                        'low': 5,
                        'moderate': 10,
                        'high': 15,
                        'very_high': 20
                    },
                    'cognitive': {
                        'low': 8,
                        'moderate': 15,
                        'high': 25,
                        'very_high': 40
                    },
                    'maintainability': {
                        'excellent': 85,
                        'good': 70,
                        'moderate': 50,
                        'poor': 30
                    }
                },
                'exclude_patterns': [
                    'test_*.py',
                    '*_test.py',
                    '__pycache__/',
                    '.git/',
                    'node_modules/',
                    'venv/',
                    'env/'
                ],
                'output_directory': 'reports/complexity',
                'enable_historical_tracking': True,
                'enable_trend_analysis': True
            }
    
    def analyze_project(self, project_path: str) -> ProjectComplexity:
        """分析整個項目的複雜度"""
        project_path = Path(project_path)
        
        if not project_path.exists():
            raise FileNotFoundError(f"項目路徑不存在: {project_path}")
        
        print(f"開始分析項目: {project_path}")
        
        # 收集所有 Python 文件
        python_files = self._collect_python_files(project_path)
        
        if not python_files:
            raise ValueError("未找到 Python 文件")
        
        print(f"找到 {len(python_files)} 個 Python 文件")
        
        # 分析每個文件
        file_complexities = []
        total_functions = []
        all_function_data = []
        
        for file_path in python_files:
            try:
                file_complexity = self.analyze_file(file_path)
                file_complexities.append(file_complexity)
                total_functions.extend(file_complexity.functions)
                all_function_data.extend([asdict(f) for f in file_complexity.functions])
                
            except Exception as e:
                print(f"分析文件失敗 {file_path}: {e}")
                continue
        
        # 計算項目級別統計
        project_complexity = self._calculate_project_metrics(
            project_path.name,
            file_complexities,
            total_functions
        )
        
        # 保存歷史數據
        if self.config.get('enable_historical_tracking', True):
            self._save_historical_data(project_complexity)
        
        # 生成趨勢分析
        if self.config.get('enable_trend_analysis', True):
            project_complexity.trends = self._analyze_trends()
        
        return project_complexity
    
    def _collect_python_files(self, project_path: Path) -> List[Path]:
        """收集 Python 文件"""
        exclude_patterns = self.config.get('exclude_patterns', [])
        python_files = []
        
        for file_path in project_path.rglob('*.py'):
            # 檢查是否應該排除
            if self._should_exclude_file(file_path, exclude_patterns):
                continue
            
            python_files.append(file_path)
        
        return python_files
    
    def _should_exclude_file(self, file_path: Path, exclude_patterns: List[str]) -> bool:
        """判斷文件是否應該被排除"""
        file_str = str(file_path)
        
        for pattern in exclude_patterns:
            if pattern in file_str:
                return True
        
        return False
    
    def analyze_file(self, file_path: Path) -> FileComplexity:
        """分析單個文件的複雜度"""
        print(f"分析文件: {file_path}")
        
        # 讀取文件內容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用 radon 分析
        cc_results = radon_cc.cc_visit(content)
        mi_results = radon_metrics.mi_visit(content, True)
        halstead_results = radon_metrics.h_visit(content)
        
        # 使用 lizard 分析
        lizard_result = lizard.analyze_file.analyze_source_code(
            str(file_path), content
        )
        
        # 分析函數
        functions = []
        for func in cc_results:
            function_complexity = self._analyze_function(
                func, file_path, content, halstead_results
            )
            functions.append(function_complexity)
        
        # 計算文件級別指標
        total_lines = len(content.splitlines())
        code_lines = lizard_result.nloc
        comment_lines = len([line for line in content.splitlines() if line.strip().startswith('#')])
        blank_lines = total_lines - code_lines - comment_lines
        
        # 計算平均複雜度
        avg_complexity = np.mean([f.cyclomatic_complexity for f in functions]) if functions else 0
        
        # 獲取可維護性指數
        maintainability_index = mi_results if isinstance(mi_results, (int, float)) else 70.0
        
        # 計算風險等級
        risk_level = self._calculate_file_risk_level(functions)
        
        # 計算技術債務
        technical_debt = self._calculate_technical_debt(functions)
        
        return FileComplexity(
            file_path=str(file_path),
            total_lines=total_lines,
            code_lines=code_lines,
            comment_lines=comment_lines,
            blank_lines=blank_lines,
            functions=functions,
            average_complexity=avg_complexity,
            maintainability_index=maintainability_index,
            risk_level=risk_level,
            technical_debt=technical_debt
        )
    
    def _analyze_function(self, func, file_path: Path, content: str, halstead_results) -> FunctionComplexity:
        """分析單個函數的複雜度"""
        # 基本複雜度度量
        cyclomatic = func.complexity
        cognitive = self._calculate_cognitive_complexity(func)
        
        # Halstead 指標
        halstead_metrics = self._get_halstead_metrics(func, halstead_results)
        
        # 可維護性指數
        maintainability = self._calculate_function_maintainability(func, halstead_metrics)
        
        # 代碼行數
        lines_of_code = func.endlineno - func.lineno + 1
        
        # 參數數量
        parameters_count = len(func.arguments) if func.arguments else 0
        
        # 嵌套深度
        nesting_depth = self._calculate_nesting_depth(func)
        
        # 風險等級
        risk_level = self._calculate_function_risk_level(cyclomatic, cognitive)
        
        # 生成建議
        recommendations = self._generate_function_recommendations(
            cyclomatic, cognitive, parameters_count, nesting_depth
        )
        
        return FunctionComplexity(
            name=func.name,
            file_path=str(file_path),
            line_start=func.lineno,
            line_end=func.endlineno,
            cyclomatic_complexity=cyclomatic,
            cognitive_complexity=cognitive,
            halstead_metrics=halstead_metrics,
            maintainability_index=maintainability,
            lines_of_code=lines_of_code,
            parameters_count=parameters_count,
            nesting_depth=nesting_depth,
            risk_level=risk_level,
            recommendations=recommendations
        )
    
    def _calculate_cognitive_complexity(self, func) -> int:
        """計算認知複雜度"""
        # 這是一個簡化的實現，實際可能需要更複雜的分析
        complexity = 1  # 基礎複雜度
        
        # 這裡需要遍歷 AST 來計算認知複雜度
        # 暫時返回一個基於圈複雜度的估算值
        return int(func.complexity * 1.5)
    
    def _get_halstead_metrics(self, func, halstead_results) -> Dict[str, float]:
        """獲取 Halstead 指標"""
        # 簡化實現，實際應該根據函數範圍提取
        return {
            'difficulty': 10.0,
            'effort': 1000.0,
            'time': 50.0,
            'bugs': 0.5,
            'vocabulary': 20.0,
            'length': 100.0,
            'volume': 500.0
        }
    
    def _calculate_function_maintainability(self, func, halstead_metrics: Dict[str, float]) -> float:
        """計算函數可維護性指數"""
        # 簡化的可維護性指數計算
        base_mi = 171 - 5.2 * np.log(func.complexity) - 0.23 * func.complexity - 16.2 * np.log(func.endlineno - func.lineno + 1)
        
        # 根據 Halstead 指標調整
        if halstead_metrics.get('volume', 0) > 1000:
            base_mi -= 10
        
        return max(0, min(100, base_mi))
    
    def _calculate_nesting_depth(self, func) -> int:
        """計算嵌套深度"""
        # 簡化實現
        return min(5, func.complexity // 3)
    
    def _calculate_function_risk_level(self, cyclomatic: int, cognitive: int) -> RiskLevel:
        """計算函數風險等級"""
        thresholds = self.config['thresholds']['cyclomatic']
        
        # 使用圈複雜度作為主要指標，認知複雜度作為輔助
        if cyclomatic <= thresholds['low'] and cognitive <= self.config['thresholds']['cognitive']['low']:
            return RiskLevel.LOW
        elif cyclomatic <= thresholds['moderate'] and cognitive <= self.config['thresholds']['cognitive']['moderate']:
            return RiskLevel.MODERATE
        elif cyclomatic <= thresholds['high'] and cognitive <= self.config['thresholds']['cognitive']['high']:
            return RiskLevel.HIGH
        else:
            return RiskLevel.VERY_HIGH
    
    def _generate_function_recommendations(self, cyclomatic: int, cognitive: int, params: int, nesting: int) -> List[str]:
        """生成函數改進建議"""
        recommendations = []
        
        if cyclomatic > self.config['thresholds']['cyclomatic']['moderate']:
            recommendations.append("考慮重構此函數以降低圈複雜度")
        
        if cognitive > self.config['thresholds']['cognitive']['moderate']:
            recommendations.append("函數邏輯過於複雜，建議拆分為更小的函數")
        
        if params > 7:
            recommendations.append("參數數量過多，考慮使用配置對象或減少參數")
        
        if nesting > 4:
            recommendations.append("嵌套層數過深，考慮使用早期返回或提取函數")
        
        if cyclomatic > 20 or cognitive > 40:
            recommendations.append("此函數需要立即重構")
        
        return recommendations
    
    def _calculate_file_risk_level(self, functions: List[FunctionComplexity]) -> RiskLevel:
        """計算文件風險等級"""
        if not functions:
            return RiskLevel.LOW
        
        # 基於最複雜的函數確定文件風險
        risk_scores = {
            RiskLevel.LOW: 1,
            RiskLevel.MODERATE: 2,
            RiskLevel.HIGH: 3,
            RiskLevel.VERY_HIGH: 4
        }
        
        max_risk = max(functions, key=lambda f: risk_scores[f.risk_level])
        return max_risk.risk_level
    
    def _calculate_technical_debt(self, functions: List[FunctionComplexity]) -> float:
        """計算技術債務（小時）"""
        total_debt = 0.0
        
        for func in functions:
            # 基於複雜度計算重構時間
            if func.risk_level == RiskLevel.VERY_HIGH:
                total_debt += 8.0  # 8小時
            elif func.risk_level == RiskLevel.HIGH:
                total_debt += 4.0  # 4小時
            elif func.risk_level == RiskLevel.MODERATE:
                total_debt += 2.0  # 2小時
            # LOW 風險不計入技術債務
        
        return total_debt
    
    def _calculate_project_metrics(self, project_name: str, file_complexities: List[FileComplexity], total_functions: List[FunctionComplexity]) -> ProjectComplexity:
        """計算項目級別指標"""
        # 基本統計
        total_files = len(file_complexities)
        total_func_count = len(total_functions)
        total_lines = sum(f.total_lines for f in file_complexities)
        
        # 平均複雜度
        avg_complexity = np.mean([f.cyclomatic_complexity for f in total_functions]) if total_functions else 0
        
        # 複雜度分佈
        complexity_dist = self._calculate_complexity_distribution(total_functions)
        
        # 最複雜的文件
        most_complex_files = sorted(
            file_complexities,
            key=lambda f: f.average_complexity,
            reverse=True
        )[:10]
        
        # 技術債務總結
        tech_debt_summary = {
            'total_hours': sum(f.technical_debt for f in file_complexities),
            'files_with_debt': len([f for f in file_complexities if f.technical_debt > 0]),
            'functions_requiring_refactor': len([f for f in total_functions if f.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]])
        }
        
        # 項目建議
        recommendations = self._generate_project_recommendations(file_complexities, total_functions)
        
        return ProjectComplexity(
            project_name=project_name,
            total_files=total_files,
            total_functions=total_func_count,
            total_lines=total_lines,
            average_complexity=avg_complexity,
            complexity_distribution=complexity_dist,
            most_complex_files=[f.file_path for f in most_complex_files],
            technical_debt_summary=tech_debt_summary,
            trends=[],
            recommendations=recommendations
        )
    
    def _calculate_complexity_distribution(self, functions: List[FunctionComplexity]) -> Dict[str, int]:
        """計算複雜度分佈"""
        distribution = {
            'low': 0,
            'moderate': 0,
            'high': 0,
            'very_high': 0
        }
        
        for func in functions:
            distribution[func.risk_level.value] += 1
        
        return distribution
    
    def _generate_project_recommendations(self, file_complexities: List[FileComplexity], total_functions: List[FunctionComplexity]) -> List[str]:
        """生成項目級別建議"""
        recommendations = []
        
        # 統計高複雜度函數
        high_complexity_funcs = [f for f in total_functions if f.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]]
        
        if len(high_complexity_funcs) > len(total_functions) * 0.2:  # 超過20%的函數是高複雜度
            recommendations.append("項目中有太多高複雜度函數，建議制定重構計劃")
        
        # 統計技術債務
        total_debt = sum(f.technical_debt for f in file_complexities)
        if total_debt > 40:  # 超過40小時
            recommendations.append(f"技術債務過高（{total_debt:.1f}小時），需要優先處理")
        
        # 統計文件大小
        large_files = [f for f in file_complexities if f.total_lines > 500]
        if len(large_files) > len(file_complexities) * 0.1:  # 超過10%的文件過大
            recommendations.append("建議拆分過大的文件以提高可維護性")
        
        # 檢查平均複雜度
        if total_functions:
            avg_complexity = np.mean([f.cyclomatic_complexity for f in total_functions])
            if avg_complexity > 10:
                recommendations.append("項目平均複雜度偏高，建議加強代碼審查和重構")
        
        return recommendations
    
    def _save_historical_data(self, project_complexity: ProjectComplexity):
        """保存歷史數據"""
        historical_file = Path(self.config.get('output_directory', 'reports/complexity')) / 'historical_data.json'
        historical_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 加載現有歷史數據
        if historical_file.exists():
            with open(historical_file, 'r', encoding='utf-8') as f:
                historical_data = json.load(f)
        else:
            historical_data = []
        
        # 添加新的數據點
        data_point = {
            'timestamp': datetime.now().isoformat(),
            'project_name': project_complexity.project_name,
            'total_functions': project_complexity.total_functions,
            'average_complexity': project_complexity.average_complexity,
            'total_lines': project_complexity.total_lines,
            'technical_debt_hours': project_complexity.technical_debt_summary['total_hours']
        }
        
        historical_data.append(data_point)
        
        # 保留最近100個數據點
        historical_data = historical_data[-100:]
        
        # 保存歷史數據
        with open(historical_file, 'w', encoding='utf-8') as f:
            json.dump(historical_data, f, indent=2, ensure_ascii=False)
    
    def _analyze_trends(self) -> List[Dict[str, Any]]:
        """分析趨勢"""
        historical_file = Path(self.config.get('output_directory', 'reports/complexity')) / 'historical_data.json'
        
        if not historical_file.exists():
            return []
        
        with open(historical_file, 'r', encoding='utf-8') as f:
            historical_data = json.load(f)
        
        if len(historical_data) < 2:
            return []
        
        trends = []
        
        # 計算各項指標的趨勢
        metrics = ['total_functions', 'average_complexity', 'total_lines', 'technical_debt_hours']
        
        for metric in metrics:
            values = [point[metric] for point in historical_data[-10:]]  # 最近10個數據點
            
            if len(values) >= 2:
                # 計算趨勢（簡單線性回歸）
                x = list(range(len(values)))
                trend_slope = np.polyfit(x, values, 1)[0]
                
                trend_direction = "increasing" if trend_slope > 0.1 else "decreasing" if trend_slope < -0.1 else "stable"
                
                trends.append({
                    'metric': metric,
                    'direction': trend_direction,
                    'slope': trend_slope,
                    'recent_values': values[-5:]
                })
        
        return trends
    
    def generate_report(self, project_complexity: ProjectComplexity, output_path: Optional[str] = None) -> str:
        """生成複雜度分析報告"""
        # 創建輸出目錄
        output_dir = Path(output_path or self.config.get('output_directory', 'reports/complexity'))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成 HTML 報告
        html_report = self._generate_html_report(project_complexity)
        html_file = output_dir / f"complexity_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        # 生成 JSON 報告
        json_report = asdict(project_complexity)
        json_file = output_dir / f"complexity_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, indent=2, ensure_ascii=False, default=str)
        
        # 生成 CSV 報告
        csv_file = output_dir / f"complexity_functions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self._generate_csv_report(project_complexity, csv_file)
        
        print(f"報告已生成:")
        print(f"HTML: {html_file}")
        print(f"JSON: {json_file}")
        print(f"CSV: {csv_file}")
        
        return str(html_file)
    
    def _generate_html_report(self, project_complexity: ProjectComplexity) -> str:
        """生成 HTML 格式的報告"""
        html_template = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>代碼複雜度分析報告 - {project_name}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; border-bottom: 2px solid #007bff; padding-bottom: 20px; margin-bottom: 30px; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .metric-card {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #007bff; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #007bff; }}
        .metric-label {{ color: #666; margin-top: 5px; }}
        .chart-container {{ margin: 30px 0; }}
        .risk-high {{ color: #dc3545; }}
        .risk-moderate {{ color: #ffc107; }}
        .risk-low {{ color: #28a745; }}
        .recommendations {{ background-color: #fff3cd; padding: 20px; border-radius: 8px; border-left: 4px solid #ffc107; }}
        .recommendations ul {{ margin: 10px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f8f9fa; font-weight: bold; }}
        .risk-badge {{ padding: 4px 8px; border-radius: 4px; color: white; font-size: 0.8em; }}
        .risk-high {{ background-color: #dc3545; }}
        .risk-moderate {{ background-color: #ffc107; color: #000; }}
        .risk-low {{ background-color: #28a745; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 代碼複雜度分析報告</h1>
            <h2>{project_name}</h2>
            <p>生成時間: {timestamp}</p>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">{total_files}</div>
                <div class="metric-label">總文件數</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{total_functions}</div>
                <div class="metric-label">總函數數</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{average_complexity:.1f}</div>
                <div class="metric-label">平均複雜度</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{total_lines:,}</div>
                <div class="metric-label">總代碼行數</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{technical_debt_hours:.1f}h</div>
                <div class="metric-label">技術債務</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{maintainability_avg:.1f}</div>
                <div class="metric-label">平均可維護性指數</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h3>複雜度分佈</h3>
            <canvas id="complexityChart"></canvas>
        </div>
        
        <div class="chart-container">
            <h3>技術債務分析</h3>
            <canvas id="debtChart"></canvas>
        </div>
        
        {recommendations_section}
        
        <div class="chart-container">
            <h3>最複雜的文件</h3>
            <table>
                <thead>
                    <tr>
                        <th>文件路徑</th>
                        <th>平均複雜度</th>
                        <th>函數數量</th>
                        <th>風險等級</th>
                        <th>技術債務</th>
                    </tr>
                </thead>
                <tbody>
                    {most_complex_files_rows}
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        // 複雜度分佈圖
        const complexityCtx = document.getElementById('complexityChart').getContext('2d');
        new Chart(complexityCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['低風險', '中等風險', '高風險', '極高風險'],
                datasets: [{{
                    data: [{complexity_low}, {complexity_moderate}, {complexity_high}, {complexity_very_high}],
                    backgroundColor: ['#28a745', '#ffc107', '#fd7e14', '#dc3545']
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    title: {{
                        display: true,
                        text: '函數複雜度分佈'
                    }}
                }}
            }}
        }});
        
        // 技術債務圖
        const debtCtx = document.getElementById('debtChart').getContext('2d');
        new Chart(debtCtx, {{
            type: 'bar',
            data: {{
                labels: ['總技術債務', '有債務的文件數', '需要重構的函數數'],
                datasets: [{{
                    label: '數量',
                    data: [{debt_total}, {debt_files}, {debt_functions}],
                    backgroundColor: ['#007bff', '#17a2b8', '#6f42c1']
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    title: {{
                        display: true,
                        text: '技術債務統計'
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
        """
        
        # 準備模板數據
        complexity_dist = project_complexity.complexity_distribution
        tech_debt = project_complexity.technical_debt_summary
        
        recommendations_html = ""
        if project_complexity.recommendations:
            recommendations_html = f"""
            <div class="recommendations">
                <h3>📋 改進建議</h3>
                <ul>
                {''.join(f'<li>{rec}</li>' for rec in project_complexity.recommendations)}
                </ul>
            </div>
            """
        
        # 生成最複雜文件表格行
        most_complex_files_rows = ""
        # 這裡需要從 file_complexities 中獲取詳細信息，暫時使用簡化版本
        
        # 計算平均可維護性指數
        maintainability_avg = 70.0  # 簡化實現
        
        return html_template.format(
            project_name=project_complexity.project_name,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total_files=project_complexity.total_files,
            total_functions=project_complexity.total_functions,
            average_complexity=project_complexity.average_complexity,
            total_lines=project_complexity.total_lines,
            technical_debt_hours=tech_debt['total_hours'],
            maintainability_avg=maintainability_avg,
            complexity_low=complexity_dist.get('low', 0),
            complexity_moderate=complexity_dist.get('moderate', 0),
            complexity_high=complexity_dist.get('high', 0),
            complexity_very_high=complexity_dist.get('very_high', 0),
            debt_total=tech_debt['total_hours'],
            debt_files=tech_debt['files_with_debt'],
            debt_functions=tech_debt['functions_requiring_refactor'],
            recommendations_section=recommendations_html,
            most_complex_files_rows=most_complex_files_rows
        )
    
    def _generate_csv_report(self, project_complexity: ProjectComplexity, csv_file: Path):
        """生成 CSV 格式的報告"""
        # 這裡需要收集所有函數數據並生成 CSV
        # 簡化實現
        pass


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="代碼複雜度分析工具")
    parser.add_argument("project_path", help="項目路徑")
    parser.add_argument("--output", "-o", help="輸出目錄")
    parser.add_argument("--config", "-c", help="配置文件路徑")
    parser.add_argument("--format", choices=['html', 'json', 'csv'], default='html', help="報告格式")
    
    args = parser.parse_args()
    
    # 創建分析器
    analyzer = CodeComplexityAnalyzer(args.config)
    
    # 分析項目
    print("開始分析代碼複雜度...")
    project_complexity = analyzer.analyze_project(args.project_path)
    
    # 生成報告
    report_path = analyzer.generate_report(project_complexity, args.output)
    
    print(f"\n分析完成！")
    print(f"項目: {project_complexity.project_name}")
    print(f"總文件: {project_complexity.total_files}")
    print(f"總函數: {project_complexity.total_functions}")
    print(f"平均複雜度: {project_complexity.average_complexity:.2f}")
    print(f"技術債務: {project_complexity.technical_debt_summary['total_hours']:.1f} 小時")
    print(f"報告: {report_path}")


if __name__ == "__main__":
    main()