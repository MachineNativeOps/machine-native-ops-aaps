# ==============================================================================
# 自動化測試生成器 - 高階開發者工具
# Automated Test Generator - Advanced Developer Tool
# ==============================================================================

import ast
import os
import re
import json
import inspect
import importlib.util
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import astroid
from jinja2 import Environment, FileSystemLoader
import black
import pytest


class TestType(Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    API = "api"
    PERFORMANCE = "performance"
    SECURITY = "security"


class ComplexityLevel(Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


@dataclass
class FunctionAnalysis:
    """函數分析結果"""
    name: str
    module_path: str
    line_number: int
    docstring: Optional[str]
    parameters: List[Dict[str, Any]]
    return_type: Optional[str]
    decorators: List[str]
    complexity_score: int
    is_async: bool
    is_private: bool
    is_test_function: bool
    dependencies: List[str]


@dataclass
class TestCase:
    """測試用例數據結構"""
    name: str
    description: str
    test_type: TestType
    setup_code: str
    test_code: str
    teardown_code: str
    assertions: List[str]
    mock_objects: List[str]
    test_data: Dict[str, Any]


class AutomatedTestGenerator:
    """自動化測試生成器核心類"""
    
    def __init__(self, config_path: str = "config/test-generator-config.yaml"):
        self.config = self._load_config(config_path)
        self.template_env = self._setup_template_environment()
        self.analysis_cache = {}
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """載入配置文件"""
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # 默認配置
            return {
                'output_directory': 'tests/generated',
                'test_types': ['unit', 'integration'],
                'complexity_levels': ['basic', 'intermediate'],
                'templates_directory': 'templates/test-templates',
                'coverage_threshold': 80,
                'max_functions_per_file': 50,
                'excluded_patterns': ['test_', '__', '_test'],
                'mock_generation': True,
                'data_driven_tests': True
            }
    
    def _setup_template_environment(self) -> Environment:
        """設置 Jinja2 模板環境"""
        templates_dir = Path(self.config['templates_directory'])
        if templates_dir.exists():
            return Environment(loader=FileSystemLoader(str(templates_dir)))
        else:
            # 內建模板
            return Environment(loader=FileSystemLoader(''))
    
    def analyze_codebase(self, source_path: str) -> List[FunctionAnalysis]:
        """分析代碼庫"""
        source_path = Path(source_path)
        if not source_path.exists():
            raise FileNotFoundError(f"源代碼路徑不存在: {source_path}")
        
        functions = []
        
        if source_path.is_file() and source_path.suffix == '.py':
            functions.extend(self._analyze_python_file(source_path))
        elif source_path.is_dir():
            for py_file in source_path.rglob('*.py'):
                if not self._should_exclude_file(py_file):
                    functions.extend(self._analyze_python_file(py_file))
        
        return functions
    
    def _should_exclude_file(self, file_path: Path) -> bool:
        """判斷是否應該排除文件"""
        excluded_patterns = self.config.get('excluded_patterns', [])
        file_str = str(file_path)
        
        for pattern in excluded_patterns:
            if pattern in file_str:
                return True
        
        return False
    
    def _analyze_python_file(self, file_path: Path) -> List[FunctionAnalysis]:
        """分析 Python 文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 使用 AST 解析
            tree = ast.parse(content)
            
            # 使用 astroid 進行更深入的分析
            module = astroid.parse(content)
            
            functions = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    analysis = self._analyze_function(node, file_path, module)
                    if analysis:
                        functions.append(analysis)
            
            return functions
            
        except Exception as e:
            print(f"分析文件失敗 {file_path}: {e}")
            return []
    
    def _analyze_function(self, node: ast.FunctionDef, file_path: Path, module: astroid.Module) -> Optional[FunctionAnalysis]:
        """分析單個函數"""
        # 檢查是否應該排除
        if self._should_exclude_function(node.name):
            return None
        
        try:
            # 獲取函數信息
            docstring = ast.get_docstring(node)
            is_async = isinstance(node, ast.AsyncFunctionDef)
            is_private = node.name.startswith('_')
            is_test_function = node.name.startswith('test') or '_test' in node.name
            
            # 分析參數
            parameters = self._analyze_parameters(node)
            
            # 分析返回類型
            return_type = self._analyze_return_type(node)
            
            # 分析裝飾器
            decorators = self._analyze_decorators(node)
            
            # 計算複雜度分數
            complexity_score = self._calculate_complexity(node)
            
            # 分析依賴
            dependencies = self._analyze_dependencies(node, module)
            
            return FunctionAnalysis(
                name=node.name,
                module_path=str(file_path),
                line_number=node.lineno,
                docstring=docstring,
                parameters=parameters,
                return_type=return_type,
                decorators=decorators,
                complexity_score=complexity_score,
                is_async=is_async,
                is_private=is_private,
                is_test_function=is_test_function,
                dependencies=dependencies
            )
            
        except Exception as e:
            print(f"分析函數失敗 {node.name}: {e}")
            return None
    
    def _should_exclude_function(self, func_name: str) -> bool:
        """判斷是否應該排除函數"""
        excluded_patterns = self.config.get('excluded_patterns', [])
        
        for pattern in excluded_patterns:
            if pattern in func_name:
                return True
        
        return False
    
    def _analyze_parameters(self, node: ast.FunctionDef) -> List[Dict[str, Any]]:
        """分析函數參數"""
        parameters = []
        
        # 一般參數
        for arg in node.args.args:
            param_info = {
                'name': arg.arg,
                'type': self._get_annotation_string(arg.annotation) if arg.annotation else None,
                'default': None,
                'kind': 'positional'
            }
            parameters.append(param_info)
        
        # 默認值
        defaults = node.args.defaults
        if defaults:
            default_offset = len(parameters) - len(defaults)
            for i, default in enumerate(defaults):
                param_index = default_offset + i
                if param_index < len(parameters):
                    parameters[param_index]['default'] = ast.unparse(default)
        
        # 關鍵字參數
        for kwarg in node.args.kwonlyargs:
            param_info = {
                'name': kwarg.arg,
                'type': self._get_annotation_string(kwarg.annotation) if kwarg.annotation else None,
                'default': None,
                'kind': 'keyword_only'
            }
            parameters.append(param_info)
        
        # **kwargs
        if node.args.kwarg:
            parameters.append({
                'name': node.args.kwarg.arg,
                'type': None,
                'default': None,
                'kind': 'kwargs'
            })
        
        return parameters
    
    def _get_annotation_string(self, annotation: ast.AST) -> Optional[str]:
        """獲取類型註解字符串"""
        try:
            return ast.unparse(annotation)
        except Exception:
            return None
    
    def _analyze_return_type(self, node: ast.FunctionDef) -> Optional[str]:
        """分析返回類型"""
        if node.returns:
            try:
                return ast.unparse(node.returns)
            except Exception:
                return None
        return None
    
    def _analyze_decorators(self, node: ast.FunctionDef) -> List[str]:
        """分析裝飾器"""
        decorators = []
        
        for decorator in node.decorator_list:
            try:
                decorator_str = ast.unparse(decorator)
                decorators.append(decorator_str)
            except Exception:
                continue
        
        return decorators
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """計算函數複雜度"""
        complexity = 1  # 基礎複雜度
        
        for child in ast.walk(node):
            # 條件語句
            if isinstance(child, (ast.If, ast.IfExp)):
                complexity += 1
            # 循環語句
            elif isinstance(child, (ast.For, ast.While)):
                complexity += 1
            # 異常處理
            elif isinstance(child, (ast.ExceptHandler, ast.Try)):
                complexity += 1
            # 邏輯運算符
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _analyze_dependencies(self, node: ast.FunctionDef, module: astroid.Module) -> List[str]:
        """分析函數依賴"""
        dependencies = set()
        
        # 簡單的依賴分析 - 查找函數調用
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    dependencies.add(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    dependencies.add(child.func.attr)
        
        return list(dependencies)
    
    def generate_test_cases(self, function_analysis: FunctionAnalysis) -> List[TestCase]:
        """生成測試用例"""
        test_cases = []
        
        # 根據配置生成不同類型的測試
        test_types = self.config.get('test_types', ['unit'])
        
        for test_type in test_types:
            if test_type == 'unit':
                test_cases.extend(self._generate_unit_tests(function_analysis))
            elif test_type == 'integration':
                test_cases.extend(self._generate_integration_tests(function_analysis))
            elif test_type == 'api':
                test_cases.extend(self._generate_api_tests(function_analysis))
            elif test_type == 'performance':
                test_cases.extend(self._generate_performance_tests(function_analysis))
            elif test_type == 'security':
                test_cases.extend(self._generate_security_tests(function_analysis))
        
        return test_cases
    
    def _generate_unit_tests(self, analysis: FunctionAnalysis) -> List[TestCase]:
        """生成單元測試"""
        test_cases = []
        
        # 正常情況測試
        test_cases.append(self._create_happy_path_test(analysis))
        
        # 邊界條件測試
        test_cases.extend(self._create_boundary_tests(analysis))
        
        # 錯誤情況測試
        test_cases.extend(self._create_error_tests(analysis))
        
        return test_cases
    
    def _create_happy_path_test(self, analysis: FunctionAnalysis) -> TestCase:
        """創建正常路徑測試"""
        test_name = f"test_{analysis.name}_happy_path"
        
        # 生成測試數據
        test_data = self._generate_test_data(analysis.parameters)
        
        # 生成測試代碼
        test_code = self._generate_test_code(analysis, test_data, "happy_path")
        
        # 生成斷言
        assertions = self._generate_assertions(analysis, test_data)
        
        return TestCase(
            name=test_name,
            description=f"測試 {analysis.name} 的正常執行路徑",
            test_type=TestType.UNIT,
            setup_code=self._generate_setup_code(analysis),
            test_code=test_code,
            teardown_code="",
            assertions=assertions,
            mock_objects=self._generate_mocks(analysis),
            test_data=test_data
        )
    
    def _create_boundary_tests(self, analysis: FunctionAnalysis) -> List[TestCase]:
        """創建邊界條件測試"""
        test_cases = []
        
        # 空值測試
        if self._has_nullable_parameters(analysis.parameters):
            test_cases.append(self._create_null_test(analysis))
        
        # 極值測試
        if self._has_numeric_parameters(analysis.parameters):
            test_cases.append(self._create_extreme_value_test(analysis))
        
        return test_cases
    
    def _create_error_tests(self, analysis: FunctionAnalysis) -> List[TestCase]:
        """創建錯誤情況測試"""
        test_cases = []
        
        # 無效參數測試
        test_cases.append(self._create_invalid_params_test(analysis))
        
        # 依賴異常測試
        if analysis.dependencies:
            test_cases.append(self._create_dependency_error_test(analysis))
        
        return test_cases
    
    def _generate_test_data(self, parameters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成測試數據"""
        test_data = {}
        
        for param in parameters:
            if param['kind'] in ['positional', 'keyword_only']:
                test_data[param['name']] = self._generate_value_for_type(param['type'])
        
        return test_data
    
    def _generate_value_for_type(self, type_hint: Optional[str]) -> Any:
        """根據類型生成測試值"""
        if not type_hint:
            return "mock_value"
        
        type_lower = type_hint.lower()
        
        if 'str' in type_lower or 'string' in type_lower:
            return "test_string"
        elif 'int' in type_lower:
            return 42
        elif 'float' in type_lower:
            return 3.14
        elif 'bool' in type_lower:
            return True
        elif 'list' in type_lower:
            return [1, 2, 3]
        elif 'dict' in type_lower:
            return {"key": "value"}
        elif 'none' in type_lower:
            return None
        else:
            return "mock_value"
    
    def _generate_test_code(self, analysis: FunctionAnalysis, test_data: Dict[str, Any], scenario: str) -> str:
        """生成測試代碼"""
        # 這是一個簡化的實現，實際應該更智能
        args_list = []
        for param in analysis.parameters:
            if param['name'] in test_data:
                args_list.append(f"{param['name']}={test_data[param['name']]}")
        
        if analysis.is_async:
            test_code = f"""
import pytest

async def test_{analysis.name}_{scenario}():
    # 測試 {analysis.name}
    {'; '.join(args_list)}
"""
        else:
            test_code = f"""
def test_{analysis.name}_{scenario}():
    # 測試 {analysis.name}
    {'; '.join(args_list)}
"""
        
        return test_code
    
    def _generate_assertions(self, analysis: FunctionAnalysis, test_data: Dict[str, Any]) -> List[str]:
        """生成斷言"""
        assertions = []
        
        # 基本斷言 - 檢查返回值
        assertions.append("assert result is not None")
        
        # 根據返回類型生成特定斷言
        if analysis.return_type:
            return_lower = analysis.return_type.lower()
            if 'bool' in return_lower:
                assertions.append("assert isinstance(result, bool)")
            elif 'int' in return_lower:
                assertions.append("assert isinstance(result, int)")
            elif 'str' in return_lower:
                assertions.append("assert isinstance(result, str)")
            elif 'list' in return_lower:
                assertions.append("assert isinstance(result, list)")
        
        return assertions
    
    def _generate_setup_code(self, analysis: FunctionAnalysis) -> str:
        """生成設置代碼"""
        setup_code = ""
        
        # 導入模塊
        module_name = Path(analysis.module_path).stem
        setup_code += f"from {module_name} import {analysis.name}\n"
        
        # 設置 mock 對象
        if self.config.get('mock_generation', True) and analysis.dependencies:
            setup_code += "from unittest.mock import Mock, patch\n"
        
        return setup_code
    
    def _generate_mocks(self, analysis: FunctionAnalysis) -> List[str]:
        """生成 mock 對象"""
        mocks = []
        
        if self.config.get('mock_generation', True) and analysis.dependencies:
            for dep in analysis.dependencies:
                mocks.append(f"mock_{dep} = Mock()")
        
        return mocks
    
    def _has_nullable_parameters(self, parameters: List[Dict[str, Any]]) -> bool:
        """檢查是否有可空參數"""
        for param in parameters:
            if param.get('type') and ('Optional' in param['type'] or 'Union' in param['type']):
                return True
        return False
    
    def _has_numeric_parameters(self, parameters: List[Dict[str, Any]]) -> bool:
        """檢查是否有數字參數"""
        for param in parameters:
            if param.get('type') and any(t in param['type'].lower() for t in ['int', 'float']):
                return True
        return False
    
    def _create_null_test(self, analysis: FunctionAnalysis) -> TestCase:
        """創建空值測試"""
        test_name = f"test_{analysis.name}_with_null_values"
        
        # 生成空值測試數據
        test_data = {}
        for param in analysis.parameters:
            if param['kind'] in ['positional', 'keyword_only']:
                if param.get('default') is None:
                    test_data[param['name']] = None
        
        return TestCase(
            name=test_name,
            description=f"測試 {analysis.name} 處理空值的能力",
            test_type=TestType.UNIT,
            setup_code=self._generate_setup_code(analysis),
            test_code=self._generate_test_code(analysis, test_data, "null_values"),
            teardown_code="",
            assertions=["assert result is not None"],
            mock_objects=[],
            test_data=test_data
        )
    
    def _create_extreme_value_test(self, analysis: FunctionAnalysis) -> TestCase:
        """創建極值測試"""
        test_name = f"test_{analysis.name}_extreme_values"
        
        test_data = {}
        for param in analysis.parameters:
            if param['kind'] in ['positional', 'keyword_only']:
                param_type = param.get('type', '').lower()
                if 'int' in param_type:
                    test_data[param['name']] = 999999
                elif 'float' in param_type:
                    test_data[param['name']] = 999999.99
        
        return TestCase(
            name=test_name,
            description=f"測試 {analysis.name} 處理極值的能力",
            test_type=TestType.UNIT,
            setup_code=self._generate_setup_code(analysis),
            test_code=self._generate_test_code(analysis, test_data, "extreme_values"),
            teardown_code="",
            assertions=["assert result is not None"],
            mock_objects=[],
            test_data=test_data
        )
    
    def _create_invalid_params_test(self, analysis: FunctionAnalysis) -> TestCase:
        """創建無效參數測試"""
        test_name = f"test_{analysis.name}_invalid_params"
        
        return TestCase(
            name=test_name,
            description=f"測試 {analysis.name} 對無效參數的處理",
            test_type=TestType.UNIT,
            setup_code=self._generate_setup_code(analysis),
            test_code=f"""
def test_{analysis.name}_invalid_params():
    with pytest.raises((ValueError, TypeError)):
        # 傳入無效參數
        result = {analysis.name}(invalid_param="invalid_value")
""",
            teardown_code="",
            assertions=[""],
            mock_objects=[],
            test_data={"invalid_param": "invalid_value"}
        )
    
    def _create_dependency_error_test(self, analysis: FunctionAnalysis) -> TestCase:
        """創建依賴異常測試"""
        test_name = f"test_{analysis.name}_dependency_error"
        
        return TestCase(
            name=test_name,
            description=f"測試 {analysis.name} 當依賴失敗時的行為",
            test_type=TestType.UNIT,
            setup_code=self._generate_setup_code(analysis),
            test_code=f"""
def test_{analysis.name}_dependency_error():
    with patch('{analysis.dependencies[0]}', side_effect=Exception("Dependency failed")):
        with pytest.raises(Exception):
            result = {analysis.name}()
""",
            teardown_code="",
            assertions=[""],
            mock_objects=[f"mock_{dep}" for dep in analysis.dependencies],
            test_data={}
        )
    
    def _generate_integration_tests(self, analysis: FunctionAnalysis) -> List[TestCase]:
        """生成集成測試"""
        # 簡化實現
        return []
    
    def _generate_api_tests(self, analysis: FunctionAnalysis) -> List[TestCase]:
        """生成 API 測試"""
        # 簡化實現
        return []
    
    def _generate_performance_tests(self, analysis: FunctionAnalysis) -> List[TestCase]:
        """生成性能測試"""
        # 簡化實現
        return []
    
    def _generate_security_tests(self, analysis: FunctionAnalysis) -> List[TestCase]:
        """生成安全測試"""
        # 簡化實現
        return []
    
    def generate_test_file(self, module_path: str, test_cases: List[TestCase]) -> str:
        """生成測試文件內容"""
        # 按類型分組測試用例
        grouped_tests = {}
        for test_case in test_cases:
            test_type = test_case.test_type.value
            if test_type not in grouped_tests:
                grouped_tests[test_type] = []
            grouped_tests[test_type].append(test_case)
        
        # 生成文件內容
        content = []
        content.append('"""\n自動生成的測試文件\n請不要手動修改此文件\n"""\n')
        
        # 導入語句
        imports = set()
        for test_case in test_cases:
            if 'import' in test_case.setup_code:
                for line in test_case.setup_code.split('\n'):
                    if line.strip().startswith('import') or line.strip().startswith('from'):
                        imports.add(line.strip())
        
        content.extend(sorted(imports))
        content.append('\n')
        
        # 測試類
        for test_type, tests in grouped_tests.items():
            content.append(f'\nclass Test{test_type.title()}:\n')
            
            for test_case in tests:
                # 添加文檔字符串
                if test_case.description:
                    content.append(f'    """{test_case.description}"""\n')
                
                # 添加設置代碼
                if test_case.setup_code:
                    setup_lines = test_case.setup_code.strip().split('\n')
                    for line in setup_lines:
                        if line.strip() and not line.strip().startswith('#'):
                            content.append(f'    {line}\n')
                
                # 添加測試代碼
                test_lines = test_case.test_code.strip().split('\n')
                for line in test_lines:
                    if line.strip():
                        if line.strip().startswith('def ') or line.strip().startswith('async def '):
                            content.append(f'    {line}\n')
                        else:
                            content.append(f'        {line}\n')
                
                content.append('\n')
        
        # 格式化代碼
        file_content = ''.join(content)
        
        try:
            # 使用 black 格式化
            formatted_content = black.format_str(file_content, mode=black.FileMode())
            return formatted_content
        except Exception:
            return file_content
    
    def save_test_files(self, functions_analysis: List[FunctionAnalysis], output_dir: str):
        """保存測試文件"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 按模塊分組
        module_groups = {}
        for analysis in functions_analysis:
            module_name = Path(analysis.module_path).stem
            if module_name not in module_groups:
                module_groups[module_name] = []
            module_groups[module_name].append(analysis)
        
        # 為每個模塊生成測試文件
        for module_name, analyses in module_groups.items():
            # 收集所有測試用例
            all_test_cases = []
            for analysis in analyses:
                test_cases = self.generate_test_cases(analysis)
                all_test_cases.extend(test_cases)
            
            # 生成測試文件
            test_file_content = self.generate_test_file(module_name, all_test_cases)
            
            # 保存文件
            test_file_path = output_path / f"test_{module_name}.py"
            with open(test_file_path, 'w', encoding='utf-8') as f:
                f.write(test_file_content)
            
            print(f"生成測試文件: {test_file_path}")
    
    def generate_report(self, functions_analysis: List[FunctionAnalysis]) -> Dict[str, Any]:
        """生成分析報告"""
        total_functions = len(functions_analysis)
        testable_functions = len([f for f in functions_analysis if not f.is_test_function])
        
        complexity_stats = {
            'low': 0,      # 1-5
            'medium': 0,   # 6-10
            'high': 0,     # 11+
            'very_high': 0 # 20+
        }
        
        for analysis in functions_analysis:
            if analysis.complexity_score <= 5:
                complexity_stats['low'] += 1
            elif analysis.complexity_score <= 10:
                complexity_stats['medium'] += 1
            elif analysis.complexity_score <= 20:
                complexity_stats['high'] += 1
            else:
                complexity_stats['very_high'] += 1
        
        return {
            'total_functions': total_functions,
            'testable_functions': testable_functions,
            'excluded_functions': total_functions - testable_functions,
            'complexity_distribution': complexity_stats,
            'average_complexity': sum(f.complexity_score for f in functions_analysis) / total_functions if total_functions > 0 else 0,
            'modules_analyzed': len(set(f.module_path for f in functions_analysis)),
            'async_functions': len([f for f in functions_analysis if f.is_async]),
            'private_functions': len([f for f in functions_analysis if f.is_private])
        }


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="自動化測試生成器")
    parser.add_argument("source_path", help="源代碼路徑")
    parser.add_argument("--output", "-o", default="tests/generated", help="輸出目錄")
    parser.add_argument("--config", "-c", help="配置文件路徑")
    parser.add_argument("--report", "-r", help="生成報告文件路徑")
    
    args = parser.parse_args()
    
    # 創建測試生成器
    generator = AutomatedTestGenerator(args.config)
    
    # 分析代碼
    print("分析源代碼...")
    functions_analysis = generator.analyze_codebase(args.source_path)
    
    # 保存測試文件
    print("生成測試文件...")
    generator.save_test_files(functions_analysis, args.output)
    
    # 生成報告
    report = generator.generate_report(functions_analysis)
    print(f"\n分析報告:")
    print(f"總函數數: {report['total_functions']}")
    print(f"可測試函數: {report['testable_functions']}")
    print(f"平均複雜度: {report['average_complexity']:.2f}")
    print(f"模塊數: {report['modules_analyzed']}")
    
    if args.report:
        import json
        with open(args.report, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"報告已保存到: {args.report}")


if __name__ == "__main__":
    main()