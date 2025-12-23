# ==============================================================================
# 測試自動化框架
# Test Automation Framework
# ==============================================================================

import os
import sys
import json
import time
import asyncio
import subprocess
from typing import Dict, List, Optional, Any, Tuple, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from datetime import datetime
import logging
import unittest
import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from jinja2 import Environment, FileSystemLoader
import yaml


class TestType(Enum):
    """測試類型"""
    UNIT = "unit"
    INTEGRATION = "integration"
    END_TO_END = "e2e"
    PERFORMANCE = "performance"
    SECURITY = "security"
    API = "api"
    UI = "ui"


class TestStatus(Enum):
    """測試狀態"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class Priority(Enum):
    """優先級"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TestResult:
    """測試結果"""
    test_id: str
    test_name: str
    test_type: TestType
    status: TestStatus
    duration: float
    start_time: datetime
    end_time: datetime
    error_message: Optional[str]
    stack_trace: Optional[str]
    metadata: Dict[str, Any]
    assertions_count: int = 0
    coverage_data: Optional[Dict[str, Any]] = None


@dataclass
class TestSuite:
    """測試套件"""
    name: str
    description: str
    tests: List[str]  # test IDs
    test_type: TestType
    priority: Priority
    parallel: bool = True
    max_workers: int = 4
    setup_hooks: List[str] = []
    teardown_hooks: List[str] = []
    environment: Dict[str, Any] = None


@dataclass
class TestReport:
    """測試報告"""
    suite_name: str
    start_time: datetime
    end_time: datetime
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_tests: int
    total_duration: float
    success_rate: float
    test_results: List[TestResult]
    coverage_summary: Dict[str, Any]
    performance_metrics: Dict[str, Any]


class TestAutomationFramework:
    """測試自動化框架核心類"""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logger()
        self.test_suites = {}
        self.test_registry = {}
        self.test_results = {}
        self.hooks = {}
        self.report_generators = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # 初始化測試環境
        self._setup_test_environment()
        self._load_builtin_hooks()
        self._load_report_generators()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """載入配置文件"""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        
        # 默認配置
        return {
            'test_directories': {
                'unit': 'tests/unit',
                'integration': 'tests/integration',
                'e2e': 'tests/e2e',
                'performance': 'tests/performance',
                'security': 'tests/security'
            },
            'reporting': {
                'output_directory': 'test-reports',
                'formats': ['html', 'json', 'junit'],
                'include_coverage': True,
                'include_screenshots': True
            },
            'execution': {
                'parallel_execution': True,
                'max_workers': 4,
                'timeout_per_test': 300,
                'retry_failed_tests': True,
                'max_retries': 2
            },
            'environment': {
                'base_url': 'http://localhost:8000',
                'database_url': 'sqlite:///test.db',
                'debug_mode': False
            },
            'notifications': {
                'slack_webhook': os.getenv('SLACK_WEBHOOK_URL'),
                'email_enabled': False,
                'teams_webhook': os.getenv('TEAMS_WEBHOOK_URL')
            }
        }
    
    def _setup_logger(self) -> logging.Logger:
        """設置日誌記錄器"""
        logger = logging.getLogger('TestAutomationFramework')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _setup_test_environment(self):
        """設置測試環境"""
        # 創建測試目錄
        for test_type, directory in self.config['test_directories'].items():
            test_dir = Path(directory)
            test_dir.mkdir(parents=True, exist_ok=True)
        
        # 創建報告輸出目錄
        report_dir = Path(self.config['reporting']['output_directory'])
        report_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_builtin_hooks(self):
        """載入內置鉤子"""
        
        def setup_test_database():
            """設置測試數據庫"""
            self.logger.info("設置測試數據庫...")
            # 這裡可以實現數據庫初始化邏輯
            pass
        
        def cleanup_test_database():
            """清理測試數據庫"""
            self.logger.info("清理測試數據庫...")
            # 這裡可以實現數據庫清理邏輯
            pass
        
        def start_test_services():
            """啟動測試服務"""
            self.logger.info("啟動測試服務...")
            # 這裡可以實現服務啟動邏輯
            pass
        
        def stop_test_services():
            """停止測試服務"""
            self.logger.info("停止測試服務...")
            # 這裡可以實現服務停止邏輯
            pass
        
        # 註冊鉤子
        self.register_hook('before_suite', start_test_services)
        self.register_hook('after_suite', stop_test_services)
        self.register_hook('before_test', setup_test_database)
        self.register_hook('after_test', cleanup_test_database)
    
    def _load_report_generators(self):
        """載入報告生成器"""
        
        def generate_html_report(report: TestReport, output_path: str):
            """生成 HTML 報告"""
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>測試報告 - {report.suite_name}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                    .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
                    .metric {{ background-color: #e8f4f8; padding: 15px; border-radius: 5px; text-align: center; }}
                    .test-results {{ margin-top: 20px; }}
                    .test-result {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ddd; }}
                    .passed {{ border-left-color: #28a745; }}
                    .failed {{ border-left-color: #dc3545; }}
                    .skipped {{ border-left-color: #ffc107; }}
                    .error {{ border-left-color: #fd7e14; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🧪 測試報告</h1>
                    <h2>{report.suite_name}</h2>
                    <p>執行時間: {report.start_time.strftime('%Y-%m-%d %H:%M:%S')} - {report.end_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div class="summary">
                    <div class="metric">
                        <h3>{report.total_tests}</h3>
                        <p>總測試數</p>
                    </div>
                    <div class="metric">
                        <h3>{report.success_rate:.1f}%</h3>
                        <p>成功率</p>
                    </div>
                    <div class="metric">
                        <h3>{report.total_duration:.2f}s</h3>
                        <p>總耗時</p>
                    </div>
                    <div class="metric">
                        <h3>{report.passed_tests}</h3>
                        <p>通過測試</p>
                    </div>
                    <div class="metric">
                        <h3>{report.failed_tests}</h3>
                        <p>失敗測試</p>
                    </div>
                </div>
                
                <div class="test-results">
                    <h3>測試詳情</h3>
                    {self._generate_test_results_html(report.test_results)}
                </div>
            </body>
            </html>
            """
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        self.report_generators['html'] = generate_html_report
    
    def _generate_test_results_html(self, test_results: List[TestResult]) -> str:
        """生成測試結果 HTML"""
        html = ""
        
        for result in test_results:
            status_class = result.status.value
            html += f"""
            <div class="test-result {status_class}">
                <strong>{result.test_name}</strong> ({result.test_type.value})
                <span style="float: right;">{result.duration:.2f}s</span>
                <br>
                <small>狀態: {result.status.value}</small>
                {f'<br><small style="color: red;">錯誤: {result.error_message}</small>' if result.error_message else ''}
            </div>
            """
        
        return html
    
    def register_test(self, test_func: Callable, test_name: str, test_type: TestType, priority: Priority = Priority.MEDIUM):
        """註冊測試"""
        test_id = f"{test_type.value}_{test_name}"
        
        self.test_registry[test_id] = {
            'function': test_func,
            'name': test_name,
            'type': test_type,
            'priority': priority,
            'id': test_id
        }
        
        self.logger.info(f"已註冊測試: {test_id}")
    
    def create_test_suite(self, name: str, description: str, test_type: TestType, test_ids: List[str], priority: Priority = Priority.MEDIUM) -> TestSuite:
        """創建測試套件"""
        suite = TestSuite(
            name=name,
            description=description,
            tests=test_ids,
            test_type=test_type,
            priority=priority
        )
        
        self.test_suites[name] = suite
        self.logger.info(f"已創建測試套件: {name} ({len(test_ids)} 個測試)")
        
        return suite
    
    def register_hook(self, hook_name: str, hook_func: Callable):
        """註冊鉤子"""
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        
        self.hooks[hook_name].append(hook_func)
        self.logger.info(f"已註冊鉤子: {hook_name}")
    
    async def run_test(self, test_id: str) -> TestResult:
        """運行單個測試"""
        if test_id not in self.test_registry:
            raise ValueError(f"測試 '{test_id}' 不存在")
        
        test_info = self.test_registry[test_id]
        start_time = datetime.now()
        
        # 執行前置鉤子
        await self._execute_hooks('before_test', test_id)
        
        result = TestResult(
            test_id=test_id,
            test_name=test_info['name'],
            test_type=test_info['type'],
            status=TestStatus.RUNNING,
            duration=0.0,
            start_time=start_time,
            end_time=start_time,
            error_message=None,
            stack_trace=None,
            metadata={}
        )
        
        try:
            # 執行測試
            self.logger.info(f"執行測試: {test_id}")
            
            if asyncio.iscoroutinefunction(test_info['function']):
                await test_info['function']()
            else:
                test_info['function']()
            
            # 測試成功
            result.status = TestStatus.PASSED
            
        except Exception as e:
            # 測試失敗
            result.status = TestStatus.FAILED
            result.error_message = str(e)
            result.stack_trace = traceback.format_exc()
            self.logger.error(f"測試失敗 {test_id}: {e}")
        
        finally:
            end_time = datetime.now()
            result.duration = (end_time - start_time).total_seconds()
            result.end_time = end_time
            
            # 執行後置鉤子
            await self._execute_hooks('after_test', test_id)
            
            self.test_results[test_id] = result
        
        return result
    
    async def run_test_suite(self, suite_name: str) -> TestReport:
        """運行測試套件"""
        if suite_name not in self.test_suites:
            raise ValueError(f"測試套件 '{suite_name}' 不存在")
        
        suite = self.test_suites[suite_name]
        start_time = datetime.now()
        
        self.logger.info(f"開始執行測試套件: {suite_name}")
        
        # 執行套件前置鉤子
        await self._execute_hooks('before_suite', suite_name)
        
        test_results = []
        
        if suite.parallel and len(suite.tests) > 1:
            # 並行執行
            semaphore = asyncio.Semaphore(suite.max_workers)
            tasks = []
            
            for test_id in suite.tests:
                task = self._run_test_with_semaphore(semaphore, test_id)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, TestResult):
                    test_results.append(result)
                else:
                    # 處理異常
                    self.logger.error(f"測試執行異常: {result}")
        else:
            # 串行執行
            for test_id in suite.tests:
                try:
                    result = await self.run_test(test_id)
                    test_results.append(result)
                except Exception as e:
                    self.logger.error(f"執行測試失敗 {test_id}: {e}")
        
        end_time = datetime.now()
        
        # 執行套件後置鉤子
        await self._execute_hooks('after_suite', suite_name)
        
        # 生成測試報告
        report = self._generate_test_report(suite_name, start_time, end_time, test_results)
        
        self.logger.info(f"測試套件執行完成: {suite_name} - 成功率: {report.success_rate:.1f}%")
        
        return report
    
    async def _run_test_with_semaphore(self, semaphore: asyncio.Semaphore, test_id: str) -> TestResult:
        """使用信號量控制並發的測試執行"""
        async with semaphore:
            return await self.run_test(test_id)
    
    async def _execute_hooks(self, hook_name: str, *args):
        """執行鉤子"""
        if hook_name in self.hooks:
            for hook_func in self.hooks[hook_name]:
                try:
                    if asyncio.iscoroutinefunction(hook_func):
                        await hook_func(*args)
                    else:
                        hook_func(*args)
                except Exception as e:
                    self.logger.error(f"執行鉤子失敗 {hook_name}: {e}")
    
    def _generate_test_report(self, suite_name: str, start_time: datetime, end_time: datetime, test_results: List[TestResult]) -> TestReport:
        """生成測試報告"""
        total_tests = len(test_results)
        passed_tests = len([r for r in test_results if r.status == TestStatus.PASSED])
        failed_tests = len([r for r in test_results if r.status == TestStatus.FAILED])
        skipped_tests = len([r for r in test_results if r.status == TestStatus.SKIPPED])
        error_tests = len([r for r in test_results if r.status == TestStatus.ERROR])
        
        total_duration = sum(r.duration for r in test_results)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # 覆蓋率匯總（簡化實現）
        coverage_summary = {
            'total_lines': 1000,
            'covered_lines': 850,
            'coverage_percentage': 85.0
        }
        
        # 性能指標
        performance_metrics = {
            'average_test_duration': total_duration / total_tests if total_tests > 0 else 0,
            'slowest_test': max((r.duration for r in test_results), default=0),
            'fastest_test': min((r.duration for r in test_results), default=0)
        }
        
        return TestReport(
            suite_name=suite_name,
            start_time=start_time,
            end_time=end_time,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
            error_tests=error_tests,
            total_duration=total_duration,
            success_rate=success_rate,
            test_results=test_results,
            coverage_summary=coverage_summary,
            performance_metrics=performance_metrics
        )
    
    def generate_report(self, report: TestReport, format_type: str = 'html') -> str:
        """生成測試報告文件"""
        
        output_dir = Path(self.config['reporting']['output_directory'])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if format_type == 'html':
            output_path = output_dir / f"{report.suite_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            
            if format_type in self.report_generators:
                self.report_generators[format_type](report, str(output_path))
            else:
                self.logger.error(f"不支持的報告格式: {format_type}")
                return ""
            
            self.logger.info(f"測試報告已生成: {output_path}")
            return str(output_path)
        
        elif format_type == 'json':
            output_path = output_dir / f"{report.suite_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            report_data = asdict(report)
            # 處理 datetime 序列化
            report_data['start_time'] = report.start_time.isoformat()
            report_data['end_time'] = report.end_time.isoformat()
            report_data['test_results'] = [
                {
                    **asdict(r),
                    'start_time': r.start_time.isoformat(),
                    'end_time': r.end_time.isoformat()
                }
                for r in report.test_results
            ]
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"JSON 測試報告已生成: {output_path}")
            return str(output_path)
        
        else:
            self.logger.error(f"不支持的報告格式: {format_type}")
            return ""
    
    async def run_all_tests(self) -> Dict[str, TestReport]:
        """運行所有測試套件"""
        reports = {}
        
        for suite_name in self.test_suites:
            try:
                report = await self.run_test_suite(suite_name)
                reports[suite_name] = report
                
            except Exception as e:
                self.logger.error(f"執行測試套件失敗 {suite_name}: {e}")
        
        return reports
    
    def discover_tests(self, test_directory: str) -> List[str]:
        """自動發現測試"""
        test_dir = Path(test_directory)
        discovered_tests = []
        
        if not test_dir.exists():
            self.logger.warning(f"測試目錄不存在: {test_directory}")
            return discovered_tests
        
        # 查找測試文件
        for test_file in test_dir.rglob("test_*.py"):
            try:
                # 使用 pytest 發現測試
                result = subprocess.run(
                    [sys.executable, '-m', 'pytest', '--collect-only', str(test_file)],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    # 解析 pytest 輸出，提取測試名稱
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if '::test_' in line:
                            test_name = line.strip().split()[-1]
                            discovered_tests.append(test_name)
                
            except Exception as e:
                self.logger.error(f"發現測試失敗 {test_file}: {e}")
        
        self.logger.info(f"在 {test_directory} 中發現 {len(discovered_tests)} 個測試")
        return discovered_tests
    
    def filter_tests_by_priority(self, test_ids: List[str], min_priority: Priority) -> List[str]:
        """根據優先級過濾測試"""
        priority_order = {
            Priority.LOW: 0,
            Priority.MEDIUM: 1,
            Priority.HIGH: 2,
            Priority.CRITICAL: 3
        }
        
        min_score = priority_order[min_priority]
        filtered_tests = []
        
        for test_id in test_ids:
            if test_id in self.test_registry:
                test_priority = self.test_registry[test_id]['priority']
                if priority_order[test_priority] >= min_score:
                    filtered_tests.append(test_id)
        
        return filtered_tests
    
    async def send_test_notifications(self, report: TestReport):
        """發送測試通知"""
        # 發送 Slack 通知
        slack_webhook = self.config['notifications']['slack_webhook']
        if slack_webhook and report.failed_tests > 0:
            await self._send_slack_notification(report, slack_webhook)
        
        # 發送 Teams 通知
        teams_webhook = self.config['notifications']['teams_webhook']
        if teams_webhook and report.failed_tests > 0:
            await self._send_teams_notification(report, teams_webhook)
    
    async def _send_slack_notification(self, report: TestReport, webhook_url: str):
        """發送 Slack 通知"""
        import aiohttp
        
        color = "danger" if report.failed_tests > 0 else "good"
        
        payload = {
            "text": f"測試報告 - {report.suite_name}",
            "attachments": [{
                "color": color,
                "fields": [
                    {"title": "總測試數", "value": str(report.total_tests), "short": True},
                    {"title": "通過", "value": str(report.passed_tests), "short": True},
                    {"title": "失敗", "value": str(report.failed_tests), "short": True},
                    {"title": "成功率", "value": f"{report.success_rate:.1f}%", "short": True}
                ]
            }]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status != 200:
                    self.logger.error(f"Slack 通知發送失敗: {response.status}")
    
    async def _send_teams_notification(self, report: TestReport, webhook_url: str):
        """發送 Teams 通知"""
        import aiohttp
        
        color = "FF0000" if report.failed_tests > 0 else "00FF00"
        
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": color,
            "summary": f"測試報告 - {report.suite_name}",
            "sections": [{
                "activityTitle": f"測試完成 - {report.suite_name}",
                "activitySubtitle": f"成功率: {report.success_rate:.1f}%",
                "facts": [
                    {"name": "總測試數", "value": str(report.total_tests)},
                    {"name": "通過測試", "value": str(report.passed_tests)},
                    {"name": "失敗測試", "value": str(report.failed_tests)},
                    {"name": "總耗時", "value": f"{report.total_duration:.2f}s"}
                ]
            }]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status != 200:
                    self.logger.error(f"Teams 通知發送失敗: {response.status}")


# 測試裝飾器
def test_case(test_name: str, test_type: TestType = TestType.UNIT, priority: Priority = Priority.MEDIUM):
    """測試用例裝飾器"""
    def decorator(func):
        # 獲取全局框架實例（這裡需要實現單例模式或全局變數）
        if not hasattr(test_case, 'framework'):
            test_case.framework = TestAutomationFramework()
        
        test_case.framework.register_test(func, test_name, test_type, priority)
        return func
    
    return decorator


# 使用示例
if __name__ == "__main__":
    import asyncio
    import traceback
    
    # 創建測試框架實例
    framework = TestAutomationFramework()
    
    # 定義測試用例
    @test_case("example_unit_test", TestType.UNIT, Priority.HIGH)
    def test_example():
        """示例單元測試"""
        assert 1 + 1 == 2
        time.sleep(0.1)  # 模擬測試耗時
    
    @test_case("example_integration_test", TestType.INTEGRATION, Priority.MEDIUM)
    def test_integration():
        """示例集成測試"""
        # 模擬 API 調用
        response = requests.get("https://httpbin.org/json")
        assert response.status_code == 200
    
    @test_case("example_failing_test", TestType.UNIT, Priority.LOW)
    def test_failing():
        """示例失敗測試"""
        assert False, "這是一個故意的失敗測試"
    
    # 創建測試套件
    test_ids = list(framework.test_registry.keys())
    suite = framework.create_test_suite(
        "Example Test Suite",
        "示例測試套件",
        TestType.UNIT,
        test_ids,
        Priority.HIGH
    )
    
    # 運行測試套件
    async def run_tests():
        report = await framework.run_test_suite("Example Test Suite")
        
        # 生成報告
        report_path = framework.generate_report(report, 'html')
        print(f"測試報告: {report_path}")
        
        # 發送通知
        await framework.send_test_notifications(report)
        
        return report
    
    # 執行測試
    result = asyncio.run(run_tests())
    print(f"測試完成 - 成功率: {result.success_rate:.1f}%")