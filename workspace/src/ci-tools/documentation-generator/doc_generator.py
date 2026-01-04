# ==============================================================================
# 文檔自動生成工具
# Documentation Auto-Generator Tool
# ==============================================================================

import os
import re
import json
import ast
import time
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from datetime import datetime
import logging
import importlib.util

import markdown
from jinja2 import Environment, FileSystemLoader
import yaml
from git import Repo
import requests


class DocType(Enum):
    """文檔類型"""
    API = "api"
    CODE = "code"
    ARCHITECTURE = "architecture"
    USER_GUIDE = "user_guide"
    TUTORIAL = "tutorial"
    CHANGELOG = "changelog"
    README = "readme"


class OutputFormat(Enum):
    """輸出格式"""
    HTML = "html"
    MARKDOWN = "markdown"
    PDF = "pdf"
    JSON = "json"
    YAML = "yaml"


@dataclass
class DocSection:
    """文檔章節"""
    title: str
    content: str
    level: int  # 標題級別 1-6
    anchor: str
    metadata: Dict[str, Any]


@dataclass
class Documentation:
    """文檔"""
    doc_id: str
    title: str
    description: str
    doc_type: DocType
    sections: List[DocSection]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    file_path: Optional[str] = None


@dataclass
class APIEndpoint:
    """API 端點"""
    path: str
    method: str
    description: str
    parameters: List[Dict[str, Any]]
    responses: List[Dict[str, Any]]
    examples: List[Dict[str, Any]]
    authentication: Optional[str] = None


@dataclass
class CodeModule:
    """代碼模組"""
    name: str
    file_path: str
    docstring: Optional[str]
    functions: List[Dict[str, Any]]
    classes: List[Dict[str, Any]]
    constants: List[Dict[str, Any]]
    imports: List[str]


class DocumentationGenerator:
    """文檔生成器核心類"""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logger()
        self.template_env = self._setup_template_environment()
        self.documentation_cache = {}
        self.code_analysis_cache = {}
        
        # 初始化組件
        self._init_extractors()
        self._init_generators()
        self._init_exporters()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """載入配置文件"""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        
        # 默認配置
        return {
            'source_paths': {
                'python': 'src',
                'api': 'src/api',
                'docs': 'docs',
                'config': 'config'
            },
            'output_directory': 'generated-docs',
            'templates_directory': 'templates/docs',
            'formats': ['html', 'markdown'],
            'include_private': False,
            'include_tests': False,
            'api_spec_format': 'openapi',
            'code_analysis': {
                'include_docstrings': True,
                'include_type_hints': True,
                'include_examples': True
            },
            'git_integration': {
                'enabled': True,
                'include_git_info': True,
                'auto_commit_docs': False
            },
            'publishing': {
                'auto_deploy': False,
                'deploy_target': 'gh-pages',
                'base_url': ''
            }
        }
    
    def _setup_logger(self) -> logging.Logger:
        """設置日誌記錄器"""
        logger = logging.getLogger('DocumentationGenerator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _setup_template_environment(self) -> Environment:
        """設置模板環境"""
        template_dir = Path(self.config['templates_directory'])
        
        if template_dir.exists():
            loader = FileSystemLoader(str(template_dir))
        else:
            loader = FileSystemLoader('templates')
        
        env = Environment(
            loader=loader,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # 添加自定義過濾器
        env.filters['markdown'] = self._markdown_filter
        env.filters['code_highlight'] = self._code_highlight_filter
        
        return env
    
    def _init_extractors(self):
        """初始化提取器"""
        self.extractors = {
            'python': PythonCodeExtractor(),
            'api': APISpecExtractor(),
            'markdown': MarkdownExtractor(),
            'git': GitInfoExtractor()
        }
    
    def _init_generators(self):
        """初始化生成器"""
        self.generators = {
            DocType.API: APIDocGenerator(self.template_env),
            DocType.CODE: CodeDocGenerator(self.template_env),
            DocType.ARCHITECTURE: ArchitectureDocGenerator(self.template_env),
            DocType.USER_GUIDE: UserGuideGenerator(self.template_env),
            DocType.TUTORIAL: TutorialGenerator(self.template_env),
            DocType.CHANGELOG: ChangelogGenerator(self.template_env),
            DocType.README: ReadmeGenerator(self.template_env)
        }
    
    def _init_exporters(self):
        """初始化導出器"""
        self.exporters = {
            OutputFormat.HTML: HTMLExporter(),
            OutputFormat.MARKDOWN: MarkdownExporter(),
            OutputFormat.PDF: PDFExporter(),
            OutputFormat.JSON: JSONExporter(),
            OutputFormat.YAML: YAMLExporter()
        }
    
    def generate_documentation(
        self,
        doc_type: DocType,
        source_path: str = None,
        output_formats: List[OutputFormat] = None
    ) -> Dict[str, Documentation]:
        """生成文檔"""
        
        output_formats = output_formats or [OutputFormat.MARKDOWN]
        source_path = source_path or self._get_default_source_path(doc_type)
        
        self.logger.info(f"開始生成文檔: {doc_type.value}")
        
        try:
            # 提取源數據
            source_data = self._extract_source_data(doc_type, source_path)
            
            # 生成文檔
            docs = self._generate_docs(doc_type, source_data)
            
            # 導出文檔
            self._export_docs(docs, output_formats)
            
            # 緩存文檔
            for doc_id, doc in docs.items():
                self.documentation_cache[doc_id] = doc
            
            self.logger.info(f"文檔生成完成: {len(docs)} 個文檔")
            
            return docs
            
        except Exception as e:
            self.logger.error(f"文檔生成失敗: {e}")
            raise
    
    def _extract_source_data(self, doc_type: DocType, source_path: str) -> Dict[str, Any]:
        """提取源數據"""
        
        source_path = Path(source_path)
        extractor = self.extractors.get(doc_type.name.lower())
        
        if not extractor:
            raise ValueError(f"不支持的文檔類型: {doc_type}")
        
        if doc_type == DocType.API:
            return extractor.extract_api_spec(source_path)
        elif doc_type == DocType.CODE:
            return extractor.extract_code_info(source_path)
        elif doc_type == DocType.ARCHITECTURE:
            return extractor.extract_architecture_info(source_path)
        else:
            return extractor.extract_general_info(source_path)
    
    def _generate_docs(self, doc_type: DocType, source_data: Dict[str, Any]) -> Dict[str, Documentation]:
        """生成文檔"""
        
        generator = self.generators.get(doc_type)
        
        if not generator:
            raise ValueError(f"不支持的文檔類型: {doc_type}")
        
        return generator.generate(source_data, self.config)
    
    def _export_docs(self, docs: Dict[str, Documentation], output_formats: List[OutputFormat]):
        """導出文檔"""
        
        output_dir = Path(self.config['output_directory'])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for doc_id, doc in docs.items():
            for format_type in output_formats:
                exporter = self.exporters.get(format_type)
                
                if exporter:
                    try:
                        file_path = exporter.export(doc, output_dir)
                        self.logger.info(f"已導出文檔: {file_path}")
                    except Exception as e:
                        self.logger.error(f"導出文檔失敗 {doc_id} ({format_type.value}): {e}")
    
    def _get_default_source_path(self, doc_type: DocType) -> str:
        """獲取默認源路徑"""
        source_paths = self.config['source_paths']
        
        if doc_type == DocType.API:
            return source_paths.get('api', 'src/api')
        elif doc_type == DocType.CODE:
            return source_paths.get('python', 'src')
        elif doc_type == DocType.ARCHITECTURE:
            return source_paths.get('docs', 'docs/architecture')
        else:
            return source_paths.get('docs', 'docs')
    
    def _markdown_filter(self, text: str) -> str:
        """Markdown 過濾器"""
        return markdown.markdown(text)
    
    def _code_highlight_filter(self, code: str, language: str = 'python') -> str:
        """代碼高亮過濾器"""
        try:
            import pygments
            from pygments import highlight
            from pygments.lexers import get_lexer_by_name
            from pygments.formatters import HtmlFormatter
            
            lexer = get_lexer_by_name(language)
            formatter = HtmlFormatter(style='default')
            return highlight(code, lexer, formatter)
        except ImportError:
            return f'<pre><code>{code}</code></pre>'
    
    def generate_api_documentation(self, api_path: str = None) -> Dict[str, Documentation]:
        """生成 API 文檔"""
        return self.generate_documentation(DocType.API, api_path)
    
    def generate_code_documentation(self, code_path: str = None) -> Dict[str, Documentation]:
        """生成代碼文檔"""
        return self.generate_documentation(DocType.CODE, code_path)
    
    def generate_architecture_documentation(self, arch_path: str = None) -> Dict[str, Documentation]:
        """生成架構文檔"""
        return self.generate_documentation(DocType.ARCHITECTURE, arch_path)
    
    def generate_readme(self, project_root: str = None) -> Documentation:
        """生成 README 文檔"""
        docs = self.generate_documentation(DocType.README, project_root, [OutputFormat.MARKDOWN])
        return docs.get('readme')
    
    def update_documentation(self, doc_id: str, source_changes: Dict[str, Any]) -> Documentation:
        """更新文檔"""
        
        if doc_id not in self.documentation_cache:
            raise ValueError(f"文檔不存在: {doc_id}")
        
        doc = self.documentation_cache[doc_id]
        
        # 重新提取數據並生成文檔
        updated_docs = self.generate_documentation(
            doc.doc_type,
            self._get_default_source_path(doc.doc_type)
        )
        
        if doc_id in updated_docs:
            self.documentation_cache[doc_id] = updated_docs[doc_id]
            return updated_docs[doc_id]
        
        raise ValueError(f"無法更新文檔: {doc_id}")
    
    def get_documentation_stats(self) -> Dict[str, Any]:
        """獲取文檔統計信息"""
        
        total_docs = len(self.documentation_cache)
        docs_by_type = {}
        
        for doc in self.documentation_cache.values():
            doc_type = doc.doc_type.value
            docs_by_type[doc_type] = docs_by_type.get(doc_type, 0) + 1
        
        return {
            'total_documents': total_docs,
            'documents_by_type': docs_by_type,
            'last_updated': datetime.now().isoformat(),
            'cache_size': len(self.documentation_cache)
        }


# 基礎提取器類
class BaseExtractor:
    """基礎提取器"""
    
    def extract(self, source_path: Path) -> Dict[str, Any]:
        raise NotImplementedError


class PythonCodeExtractor(BaseExtractor):
    """Python 代碼提取器"""
    
    def extract_code_info(self, source_path: Path) -> Dict[str, Any]:
        """提取 Python 代碼信息"""
        
        modules = []
        
        for py_file in source_path.rglob('*.py'):
            if self._should_exclude_file(py_file):
                continue
            
            try:
                module = self._analyze_python_file(py_file)
                if module:
                    modules.append(module)
            except Exception as e:
                logging.warning(f"分析 Python 文件失敗 {py_file}: {e}")
        
        return {
            'modules': modules,
            'total_modules': len(modules),
            'extraction_time': datetime.now().isoformat()
        }
    
    def _should_exclude_file(self, file_path: Path) -> bool:
        """判斷是否應該排除文件"""
        exclude_patterns = ['test_', '__pycache__', '.git', 'node_modules']
        
        for pattern in exclude_patterns:
            if pattern in str(file_path):
                return True
        
        return False
    
    def _analyze_python_file(self, file_path: Path) -> Optional[CodeModule]:
        """分析 Python 文件"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # 提取模組級文檔字符串
            docstring = ast.get_docstring(tree)
            
            # 提取函數
            functions = []
            classes = []
            constants = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = self._extract_function_info(node)
                    functions.append(func_info)
                elif isinstance(node, ast.ClassDef):
                    class_info = self._extract_class_info(node)
                    classes.append(class_info)
                elif isinstance(node, ast.Assign):
                    const_info = self._extract_constant_info(node)
                    if const_info:
                        constants.extend(const_info)
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    import_info = self._extract_import_info(node)
                    imports.extend(import_info)
            
            return CodeModule(
                name=file_path.stem,
                file_path=str(file_path.relative_to(file_path.parents[1])),
                docstring=docstring,
                functions=functions,
                classes=classes,
                constants=constants,
                imports=imports
            )
            
        except Exception as e:
            logging.error(f"分析 Python 文件失敗 {file_path}: {e}")
            return None
    
    def _extract_function_info(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """提取函數信息"""
        
        return {
            'name': node.name,
            'line_number': node.lineno,
            'docstring': ast.get_docstring(node),
            'args': [arg.arg for arg in node.args.args],
            'returns': ast.unparse(node.returns) if hasattr(ast, 'unparse') and node.returns else None,
            'decorators': [ast.unparse(dec) for dec in node.decorators] if hasattr(ast, 'unparse') else [],
            'is_async': isinstance(node, ast.AsyncFunctionDef),
            'complexity': self._calculate_complexity(node)
        }
    
    def _extract_class_info(self, node: ast.ClassDef) -> Dict[str, Any]:
        """提取類信息"""
        
        methods = []
        
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_info = self._extract_function_info(item)
                methods.append(method_info)
        
        return {
            'name': node.name,
            'line_number': node.lineno,
            'docstring': ast.get_docstring(node),
            'bases': [ast.unparse(base) for base in node.bases] if hasattr(ast, 'unparse') else [],
            'methods': methods,
            'decorators': [ast.unparse(dec) for dec in node.decorators] if hasattr(ast, 'unparse') else []
        }
    
    def _extract_constant_info(self, node: ast.Assign) -> List[Dict[str, Any]]:
        """提取常量信息"""
        
        constants = []
        
        for target in node.targets:
            if isinstance(target, ast.Name):
                const_info = {
                    'name': target.id,
                    'line_number': node.lineno,
                    'value': ast.unparse(node.value) if hasattr(ast, 'unparse') else str(node.value),
                    'is_uppercase': target.id.isupper()
                }
                constants.append(const_info)
        
        return constants
    
    def _extract_import_info(self, node) -> List[Dict[str, Any]]:
        """提取導入信息"""
        
        imports = []
        
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({
                    'type': 'import',
                    'module': alias.name,
                    'alias': alias.asname,
                    'line_number': node.lineno
                })
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imports.append({
                    'type': 'from_import',
                    'module': node.module,
                    'name': alias.name,
                    'alias': alias.asname,
                    'line_number': node.lineno
                })
        
        return imports
    
    def _calculate_complexity(self, node) -> int:
        """計算複雜度"""
        
        complexity = 1  # 基礎複雜度
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.With)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity


class APISpecExtractor(BaseExtractor):
    """API 規範提取器"""
    
    def extract_api_spec(self, source_path: Path) -> Dict[str, Any]:
        """提取 API 規範"""
        
        endpoints = []
        
        # 從 OpenAPI/Swagger 文件提取
        openapi_files = list(source_path.rglob('*.yaml')) + list(source_path.rglob('*.yml')) + list(source_path.rglob('*.json'))
        
        for file_path in openapi_files:
            if any(name in str(file_path).lower() for name in ['openapi', 'swagger', 'api']):
                try:
                    spec_endpoints = self._extract_openapi_endpoints(file_path)
                    endpoints.extend(spec_endpoints)
                except Exception as e:
                    logging.warning(f"提取 OpenAPI 規範失敗 {file_path}: {e}")
        
        # 從 Python FastAPI/Flask 代碼提取
        for py_file in source_path.rglob('*.py'):
            try:
                code_endpoints = self._extract_code_endpoints(py_file)
                endpoints.extend(code_endpoints)
            except Exception as e:
                logging.warning(f"從代碼提取 API 端點失敗 {py_file}: {e}")
        
        return {
            'endpoints': endpoints,
            'total_endpoints': len(endpoints),
            'spec_version': '3.0.0',
            'extraction_time': datetime.now().isoformat()
        }
    
    def _extract_openapi_endpoints(self, file_path: Path) -> List[APIEndpoint]:
        """從 OpenAPI 文件提取端點"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix in ['.yaml', '.yml']:
                    spec = yaml.safe_load(f)
                else:
                    spec = json.load(f)
            
            endpoints = []
            paths = spec.get('paths', {})
            
            for path, path_item in paths.items():
                for method, operation in path_item.items():
                    if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                        endpoint = APIEndpoint(
                            path=path,
                            method=method.upper(),
                            description=operation.get('summary', ''),
                            parameters=self._extract_parameters(operation),
                            responses=self._extract_responses(operation),
                            examples=self._extract_examples(operation),
                            authentication=operation.get('security')
                        )
                        endpoints.append(endpoint)
            
            return endpoints
            
        except Exception as e:
            logging.error(f"解析 OpenAPI 文件失敗 {file_path}: {e}")
            return []
    
    def _extract_code_endpoints(self, file_path: Path) -> List[APIEndpoint]:
        """從代碼提取端點"""
        
        # 這裡可以添加解析 FastAPI/Flask 代碼的邏輯
        # 暫時返回空列表
        return []
    
    def _extract_parameters(self, operation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取參數"""
        return operation.get('parameters', [])
    
    def _extract_responses(self, operation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取響應"""
        responses = []
        for status_code, response in operation.get('responses', {}).items():
            responses.append({
                'status_code': status_code,
                'description': response.get('description', ''),
                'content': response.get('content', {})
            })
        return responses
    
    def _extract_examples(self, operation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取示例"""
        return operation.get('examples', [])


class MarkdownExtractor(BaseExtractor):
    """Markdown 提取器"""
    
    def extract_general_info(self, source_path: Path) -> Dict[str, Any]:
        """提取通用信息"""
        
        content = []
        
        for md_file in source_path.rglob('*.md'):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                
                content.append({
                    'file_path': str(md_file),
                    'content': file_content,
                    'title': self._extract_title(file_content)
                })
            except Exception as e:
                logging.warning(f"讀取 Markdown 文件失敗 {md_file}: {e}")
        
        return {
            'content': content,
            'total_files': len(content),
            'extraction_time': datetime.now().isoformat()
        }
    
    def _extract_title(self, content: str) -> str:
        """提取標題"""
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
        return ''


class GitInfoExtractor(BaseExtractor):
    """Git 信息提取器"""
    
    def extract_git_info(self, source_path: Path) -> Dict[str, Any]:
        """提取 Git 信息"""
        
        try:
            repo = Repo(source_path)
            
            return {
                'branch': repo.active_branch.name,
                'commit_hash': repo.head.commit.hexsha,
                'commit_message': repo.head.commit.message,
                'author': str(repo.head.commit.author),
                'last_modified': repo.head.commit.committed_date.isoformat(),
                'remote_url': next(iter(repo.remotes.urls()), '') if repo.remotes else '',
                'is_dirty': repo.is_dirty(),
                'untracked_files': len(repo.untracked_files)
            }
            
        except Exception as e:
            logging.warning(f"提取 Git 信息失敗: {e}")
            return {}


# 文檔生成器類
class BaseDocGenerator:
    """基礎文檔生成器"""
    
    def __init__(self, template_env: Environment):
        self.template_env = template_env
    
    def generate(self, source_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Documentation]:
        raise NotImplementedError


class APIDocGenerator(BaseDocGenerator):
    """API 文檔生成器"""
    
    def generate(self, source_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Documentation]:
        """生成 API 文檔"""
        
        endpoints = source_data.get('endpoints', [])
        
        sections = [
            DocSection(
                title="API 概述",
                content=f"本文檔包含 {len(endpoints)} 個 API 端點。",
                level=1,
                anchor="overview",
                metadata={}
            )
        ]
        
        # 按路徑分組端點
        grouped_endpoints = {}
        for endpoint in endpoints:
            path_prefix = '/' + endpoint.path.split('/')[1] if len(endpoint.path.split('/')) > 1 else 'root'
            if path_prefix not in grouped_endpoints:
                grouped_endpoints[path_prefix] = []
            grouped_endpoints[path_prefix].append(endpoint)
        
        for path_prefix, path_endpoints in grouped_endpoints.items():
            section = DocSection(
                title=f"{path_prefix} 端點",
                content=self._generate_endpoints_content(path_endpoints),
                level=2,
                anchor=path_prefix.replace('/', ''),
                metadata={'endpoints': [asdict(ep) for ep in path_endpoints]}
            )
            sections.append(section)
        
        doc = Documentation(
            doc_id="api",
            title="API 文檔",
            description="完整的 API 參考文檔",
            doc_type=DocType.API,
            sections=sections,
            metadata={
                'total_endpoints': len(endpoints),
                'spec_version': source_data.get('spec_version', '3.0.0'),
                'generated_at': datetime.now().isoformat()
            },
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        return {'api': doc}
    
    def _generate_endpoints_content(self, endpoints: List[APIEndpoint]) -> str:
        """生成端點內容"""
        content = []
        
        for endpoint in endpoints:
            content.append(f"### {endpoint.method} {endpoint.path}")
            content.append(f"**描述**: {endpoint.description}")
            
            if endpoint.parameters:
                content.append("\n**參數**:")
                for param in endpoint.parameters:
                    content.append(f"- `{param.get('name')}` ({param.get('type', 'string')}): {param.get('description', '')}")
            
            if endpoint.responses:
                content.append("\n**響應**:")
                for response in endpoint.responses:
                    content.append(f"- `{response.get('status_code')}`: {response.get('description', '')}")
            
            content.append("")
        
        return '\n'.join(content)


class CodeDocGenerator(BaseDocGenerator):
    """代碼文檔生成器"""
    
    def generate(self, source_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Documentation]:
        """生成代碼文檔"""
        
        modules = source_data.get('modules', [])
        
        sections = [
            DocSection(
                title="代碼概覽",
                content=f"本文檔包含 {len(modules)} 個 Python 模組的詳細信息。",
                level=1,
                anchor="overview",
                metadata={}
            )
        ]
        
        for module in modules:
            section = DocSection(
                title=module.name,
                content=self._generate_module_content(module),
                level=2,
                anchor=module.name,
                metadata=asdict(module)
            )
            sections.append(section)
        
        doc = Documentation(
            doc_id="code",
            title="代碼文檔",
            description="完整的代碼參考文檔",
            doc_type=DocType.CODE,
            sections=sections,
            metadata={
                'total_modules': len(modules),
                'generated_at': datetime.now().isoformat()
            },
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        return {'code': doc}
    
    def _generate_module_content(self, module: CodeModule) -> str:
        """生成模組內容"""
        content = []
        
        if module.docstring:
            content.append(f"**描述**: {module.docstring}")
            content.append("")
        
        if module.functions:
            content.append("#### 函數")
            for func in module.functions:
                content.append(f"##### `{func['name']}`")
                if func['docstring']:
                    content.append(func['docstring'])
                content.append(f"**參數**: {', '.join(func['args'])}")
                content.append("")
        
        if module.classes:
            content.append("#### 類")
            for cls in module.classes:
                content.append(f"##### `{cls['name']}`")
                if cls['docstring']:
                    content.append(cls['docstring'])
                content.append("")
        
        return '\n'.join(content)


class ArchitectureDocGenerator(BaseDocGenerator):
    """架構文檔生成器"""
    
    def generate(self, source_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Documentation]:
        """生成架構文檔"""
        
        # 這裡可以添加架構文檔的生成邏輯
        doc = Documentation(
            doc_id="architecture",
            title="架構文檔",
            description="系統架構設計文檔",
            doc_type=DocType.ARCHITECTURE,
            sections=[],
            metadata={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        return {'architecture': doc}


class UserGuideGenerator(BaseDocGenerator):
    """用戶指南生成器"""
    
    def generate(self, source_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Documentation]:
        """生成用戶指南"""
        
        doc = Documentation(
            doc_id="user_guide",
            title="用戶指南",
            description="用戶操作指南",
            doc_type=DocType.USER_GUIDE,
            sections=[],
            metadata={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        return {'user_guide': doc}


class TutorialGenerator(BaseDocGenerator):
    """教程生成器"""
    
    def generate(self, source_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Documentation]:
        """生成教程"""
        
        doc = Documentation(
            doc_id="tutorial",
            title="教程",
            description="使用教程",
            doc_type=DocType.TUTORIAL,
            sections=[],
            metadata={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        return {'tutorial': doc}


class ChangelogGenerator(BaseDocGenerator):
    """更新日誌生成器"""
    
    def generate(self, source_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Documentation]:
        """生成更新日誌"""
        
        doc = Documentation(
            doc_id="changelog",
            title="更新日誌",
            description="版本更新記錄",
            doc_type=DocType.CHANGELOG,
            sections=[],
            metadata={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        return {'changelog': doc}


class ReadmeGenerator(BaseDocGenerator):
    """README 生成器"""
    
    def generate(self, source_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Documentation]:
        """生成 README"""
        
        sections = [
            DocSection(
                title="項目介紹",
                content="這是一個自動生成的 README 文檔。",
                level=1,
                anchor="introduction",
                metadata={}
            ),
            DocSection(
                title="安裝",
                content="```bash\npip install -r requirements.txt\n```",
                level=2,
                anchor="installation",
                metadata={}
            ),
            DocSection(
                title="使用方法",
                content="詳細的使用方法請參考文檔。",
                level=2,
                anchor="usage",
                metadata={}
            )
        ]
        
        doc = Documentation(
            doc_id="readme",
            title="README",
            description="項目說明文檔",
            doc_type=DocType.README,
            sections=sections,
            metadata={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        return {'readme': doc}


# 導出器類
class BaseExporter:
    """基礎導出器"""
    
    def export(self, doc: Documentation, output_dir: Path) -> Path:
        raise NotImplementedError


class HTMLExporter(BaseExporter):
    """HTML 導出器"""
    
    def export(self, doc: Documentation, output_dir: Path) -> Path:
        """導出為 HTML"""
        
        # 簡單的 HTML 生成
        html_content = self._generate_html(doc)
        
        file_path = output_dir / f"{doc.doc_id}.html"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return file_path
    
    def _generate_html(self, doc: Documentation) -> str:
        """生成 HTML 內容"""
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{doc.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1, h2, h3 {{ color: #333; }}
        code {{ background-color: #f4f4f4; padding: 2px 4px; border-radius: 3px; }}
        pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
    </style>
</head>
<body>
    <h1>{doc.title}</h1>
    <p>{doc.description}</p>
"""
        
        for section in doc.sections:
            html += f"    <h{section.level}>{section.title}</h{section.level}>\n"
            html += f"    <div>{section.content}</div>\n"
        
        html += """</body>
</html>"""
        
        return html


class MarkdownExporter(BaseExporter):
    """Markdown 導出器"""
    
    def export(self, doc: Documentation, output_dir: Path) -> Path:
        """導出為 Markdown"""
        
        markdown_content = self._generate_markdown(doc)
        
        file_path = output_dir / f"{doc.doc_id}.md"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return file_path
    
    def _generate_markdown(self, doc: Documentation) -> str:
        """生成 Markdown 內容"""
        
        markdown = f"# {doc.title}\n\n{doc.description}\n\n"
        
        for section in doc.sections:
            markdown += f"{'#' * section.level} {section.title}\n\n"
            markdown += f"{section.content}\n\n"
        
        return markdown


class JSONExporter(BaseExporter):
    """JSON 導出器"""
    
    def export(self, doc: Documentation, output_dir: Path) -> Path:
        """導出為 JSON"""
        
        doc_dict = asdict(doc)
        
        # 轉換 datetime 對象
        doc_dict['created_at'] = doc.created_at.isoformat()
        doc_dict['updated_at'] = doc.updated_at.isoformat()
        
        file_path = output_dir / f"{doc.doc_id}.json"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(doc_dict, f, ensure_ascii=False, indent=2)
        
        return file_path


class YAMLExporter(BaseExporter):
    """YAML 導出器"""
    
    def export(self, doc: Documentation, output_dir: Path) -> Path:
        """導出為 YAML"""
        
        doc_dict = asdict(doc)
        
        # 轉換 datetime 對象
        doc_dict['created_at'] = doc.created_at.isoformat()
        doc_dict['updated_at'] = doc.updated_at.isoformat()
        
        file_path = output_dir / f"{doc.doc_id}.yaml"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(doc_dict, f, default_flow_style=False, allow_unicode=True)
        
        return file_path


class PDFExporter(BaseExporter):
    """PDF 導出器"""
    
    def export(self, doc: Documentation, output_dir: Path) -> Path:
        """導出為 PDF"""
        
        # 這裡可以添加 PDF 生成邏輯
        # 暫時拋出未實現錯誤
        raise NotImplementedError("PDF 導出功能尚未實現")