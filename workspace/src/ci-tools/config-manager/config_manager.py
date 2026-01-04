# ==============================================================================
# CI 配置管理函數庫
# CI Configuration Management Library
# ==============================================================================

import os
import json
import yaml
import jsonschema
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import logging
from enum import Enum

from git import Repo
import jinja2


class ConfigType(Enum):
    """配置文件類型"""
    WORKFLOW = "workflow"
    ACTION = "action"
    ENVIRONMENT = "environment"
    SECURITY = "security"
    DEPLOYMENT = "deployment"


@dataclass
class CIConfig:
    """CI 配置數據結構"""
    name: str
    config_type: ConfigType
    version: str
    description: str
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    file_path: Optional[str] = None


@dataclass
class ValidationRule:
    """驗證規則"""
    name: str
    schema: Dict[str, Any]
    description: str
    severity: str  # 'error', 'warning', 'info'


@dataclass
class ConfigTemplate:
    """配置模板"""
    name: str
    config_type: ConfigType
    template_content: str
    variables: List[str]
    description: str
    category: str


class CIConfigManager:
    """CI 配置管理器核心類"""
    
    def __init__(self, workspace_path: str = None):
        self.workspace_path = workspace_path or os.getcwd()
        self.logger = self._setup_logger()
        self.configs = {}
        self.templates = {}
        self.validation_rules = {}
        self.template_env = self._setup_template_environment()
        
        # 載入默認配置
        self._load_default_templates()
        self._load_validation_rules()
    
    def _setup_logger(self) -> logging.Logger:
        """設置日誌記錄器"""
        logger = logging.getLogger('CIConfigManager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _setup_template_environment(self) -> jinja2.Environment:
        """設置模板環境"""
        template_dir = Path(self.workspace_path) / "templates" / "ci-configs"
        
        if template_dir.exists():
            loader = jinja2.FileSystemLoader(str(template_dir))
        else:
            loader = jinja2.DictLoader({})
        
        env = jinja2.Environment(
            loader=loader,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        return env
    
    def _load_default_templates(self):
        """載入默認配置模板"""
        
        # CI/CD 工作流模板
        ci_workflow_template = """
name: {{ workflow_name }}

on:
  {% for trigger in triggers %}
  {{ trigger.type }}:
    {% if trigger.branches %}
    branches:
      {% for branch in trigger.branches %}
      - {{ branch }}
      {% endfor %}
    {% endif %}
  {% endfor %}

jobs:
  {% for job in jobs %}
  {{ job.name }}:
    runs-on: {{ job.runner }}
    {% if job.needs %}
    needs:
      {% for need in job.needs %}
      - {{ need }}
      {% endfor %}
    {% endif %}
    
    steps:
      {% for step in job.steps %}
      - name: {{ step.name }}
        {% if step.uses %}
        uses: {{ step.uses }}
        {% if step.with %}
        with:
          {% for key, value in step.with.items() %}
          {{ key }}: {{ value }}
          {% endfor %}
        {% endif %}
        {% else %}
        run: |
          {{ step.run }}
        {% endif %}
      {% endfor %}
  {% endfor %}
"""
        
        self.templates['ci-workflow'] = ConfigTemplate(
            name="CI Workflow",
            config_type=ConfigType.WORKFLOW,
            template_content=ci_workflow_template,
            variables=['workflow_name', 'triggers', 'jobs'],
            description="標準 CI 工作流模板",
            category="ci-cd"
        )
        
        # 部署配置模板
        deployment_template = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ app_name }}
  namespace: {{ namespace }}
spec:
  replicas: {{ replicas }}
  selector:
    matchLabels:
      app: {{ app_name }}
  template:
    metadata:
      labels:
        app: {{ app_name }}
    spec:
      containers:
      - name: {{ app_name }}
        image: {{ image_name }}:{{ image_tag }}
        ports:
        - containerPort: {{ container_port }}
        env:
          {% for env in environment_vars %}
          - name: {{ env.name }}
            value: {{ env.value }}
          {% endfor %}
        resources:
          requests:
            memory: "{{ memory_request }}"
            cpu: "{{ cpu_request }}"
          limits:
            memory: "{{ memory_limit }}"
            cpu: "{{ cpu_limit }}"
"""
        
        self.templates['deployment'] = ConfigTemplate(
            name="Kubernetes Deployment",
            config_type=ConfigType.DEPLOYMENT,
            template_content=deployment_template,
            variables=['app_name', 'namespace', 'replicas', 'image_name', 'image_tag', 'container_port', 'environment_vars', 'memory_request', 'cpu_request', 'memory_limit', 'cpu_limit'],
            description="Kubernetes 部署配置模板",
            category="kubernetes"
        )
        
        # 環境配置模板
        environment_template = """
# Environment Configuration for {{ environment }}
# Generated on: {{ generated_date }}

# Application Settings
APP_NAME={{ app_name }}
APP_VERSION={{ app_version }}
APP_ENVIRONMENT={{ environment }}
DEBUG={{ debug_mode }}

# Database Configuration
DATABASE_URL={{ database_url }}
DATABASE_POOL_SIZE={{ db_pool_size }}
DATABASE_TIMEOUT={{ db_timeout }}

# Redis Configuration
REDIS_URL={{ redis_url }}
REDIS_POOL_SIZE={{ redis_pool_size }}

# Security Configuration
SECRET_KEY={{ secret_key }}
JWT_EXPIRE_HOURS={{ jwt_expire_hours }}

# External Services
API_BASE_URL={{ api_base_url }}
EXTERNAL_SERVICE_TIMEOUT={{ service_timeout }}

# Monitoring
LOG_LEVEL={{ log_level }}
METRICS_ENABLED={{ metrics_enabled }}
TRACE_ENABLED={{ trace_enabled }}
"""
        
        self.templates['environment'] = ConfigTemplate(
            name="Environment Variables",
            config_type=ConfigType.ENVIRONMENT,
            template_content=environment_template,
            variables=['environment', 'app_name', 'app_version', 'debug_mode', 'database_url', 'db_pool_size', 'db_timeout', 'redis_url', 'redis_pool_size', 'secret_key', 'jwt_expire_hours', 'api_base_url', 'service_timeout', 'log_level', 'metrics_enabled', 'trace_enabled'],
            description="環境變數配置模板",
            category="environment"
        )
    
    def _load_validation_rules(self):
        """載入驗證規則"""
        
        # GitHub Actions 工作流驗證規則
        workflow_schema = {
            "type": "object",
            "required": ["name", "on", "jobs"],
            "properties": {
                "name": {"type": "string"},
                "on": {
                    "anyOf": [
                        {"type": "string"},
                        {"type": "object"},
                        {"type": "array"}
                    ]
                },
                "env": {"type": "object"},
                "jobs": {
                    "type": "object",
                    "patternProperties": {
                        "^[a-zA-Z0-9_-]+$": {
                            "type": "object",
                            "required": ["runs-on"],
                            "properties": {
                                "runs-on": {
                                    "anyOf": [
                                        {"type": "string"},
                                        {"type": "array"}
                                    ]
                                },
                                "needs": {
                                    "anyOf": [
                                        {"type": "string"},
                                        {"type": "array"}
                                    ]
                                },
                                "steps": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "required": ["name"],
                                        "properties": {
                                            "name": {"type": "string"},
                                            "uses": {"type": "string"},
                                            "run": {"type": "string"},
                                            "with": {"type": "object"},
                                            "env": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        self.validation_rules['workflow'] = ValidationRule(
            name="GitHub Actions Workflow",
            schema=workflow_schema,
            description="GitHub Actions 工作流配置驗證規則",
            severity="error"
        )
        
        # Kubernetes 部署驗證規則
        deployment_schema = {
            "type": "object",
            "required": ["apiVersion", "kind", "metadata", "spec"],
            "properties": {
                "apiVersion": {"type": "string"},
                "kind": {"type": "string"},
                "metadata": {
                    "type": "object",
                    "required": ["name"],
                    "properties": {
                        "name": {"type": "string"},
                        "namespace": {"type": "string"}
                    }
                },
                "spec": {
                    "type": "object",
                    "required": ["replicas", "selector", "template"],
                    "properties": {
                        "replicas": {"type": "integer", "minimum": 1},
                        "selector": {
                            "type": "object",
                            "required": ["matchLabels"]
                        },
                        "template": {
                            "type": "object",
                            "required": ["metadata", "spec"],
                            "properties": {
                                "metadata": {
                                    "type": "object",
                                    "required": ["labels"]
                                },
                                "spec": {
                                    "type": "object",
                                    "required": ["containers"],
                                    "properties": {
                                        "containers": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "required": ["name", "image"],
                                                "properties": {
                                                    "name": {"type": "string"},
                                                    "image": {"type": "string"},
                                                    "ports": {
                                                        "type": "array",
                                                        "items": {
                                                            "type": "object",
                                                            "required": ["containerPort"],
                                                            "properties": {
                                                                "containerPort": {"type": "integer"}
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        self.validation_rules['deployment'] = ValidationRule(
            name="Kubernetes Deployment",
            schema=deployment_schema,
            description="Kubernetes 部署配置驗證規則",
            severity="error"
        )
    
    def create_config_from_template(
        self,
        template_name: str,
        variables: Dict[str, Any],
        config_name: str,
        description: str = ""
    ) -> CIConfig:
        """從模板創建配置"""
        
        if template_name not in self.templates:
            raise ValueError(f"模板 '{template_name}' 不存在")
        
        template = self.templates[template_name]
        
        # 渲染模板
        try:
            jinja_template = self.template_env.from_string(template.template_content)
            rendered_content = jinja_template.render(**variables)
            
            # 解析渲染後的內容
            if template.config_type in [ConfigType.WORKFLOW, ConfigType.DEPLOYMENT]:
                content = yaml.safe_load(rendered_content)
            elif template.config_type == ConfigType.ENVIRONMENT:
                # 環境變數配置特殊處理
                content = {
                    "raw_content": rendered_content,
                    "variables": variables
                }
            else:
                content = json.loads(rendered_content)
                
        except Exception as e:
            self.logger.error(f"模板渲染失敗: {e}")
            raise ValueError(f"模板渲染失敗: {e}")
        
        # 創建配置對象
        config = CIConfig(
            name=config_name,
            config_type=template.config_type,
            version="1.0.0",
            description=description or template.description,
            content=content,
            metadata={
                "template": template_name,
                "variables": variables,
                "category": template.category
            },
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.configs[config_name] = config
        return config
    
    def validate_config(self, config: CIConfig) -> Tuple[bool, List[str]]:
        """驗證配置"""
        
        # 獲取對應的驗證規則
        rule_key = config.config_type.value
        if rule_key not in self.validation_rules:
            return True, []
        
        rule = self.validation_rules[rule_key]
        errors = []
        
        try:
            # 使用 jsonschema 驗證
            jsonschema.validate(config.content, rule.schema)
            self.logger.info(f"配置 '{config.name}' 驗證通過")
            return True, []
            
        except jsonschema.ValidationError as e:
            error_msg = f"驗證失敗: {e.message}"
            if e.path:
                error_msg += f" (路徑: {'.'.join(str(p) for p in e.path)})"
            errors.append(error_msg)
            
        except jsonschema.SchemaError as e:
            errors.append(f"驗證規則錯誤: {e.message}")
            
        except Exception as e:
            errors.append(f"驗證過程發生異常: {str(e)}")
        
        # 記錄驗證結果
        if errors:
            self.logger.warning(f"配置 '{config.name}' 驗證失敗: {errors}")
        else:
            self.logger.info(f"配置 '{config.name}' 驗證通過")
        
        return len(errors) == 0, errors
    
    def save_config(self, config: CIConfig, file_path: str = None) -> str:
        """保存配置到文件"""
        
        if file_path is None:
            # 根據配置類型生成默認文件路徑
            if config.config_type == ConfigType.WORKFLOW:
                base_dir = Path(self.workspace_path) / ".github" / "workflows"
                file_path = base_dir / f"{config.name.lower().replace(' ', '-')}.yml"
            elif config.config_type == ConfigType.DEPLOYMENT:
                base_dir = Path(self.workspace_path) / "k8s" / "deployments"
                file_path = base_dir / f"{config.name.lower().replace(' ', '-')}.yaml"
            elif config.config_type == ConfigType.ENVIRONMENT:
                base_dir = Path(self.workspace_path) / "config" / "environments"
                file_path = base_dir / f"{config.name.lower().replace(' ', '-')}.env"
            else:
                base_dir = Path(self.workspace_path) / "config"
                file_path = base_dir / f"{config.name.lower().replace(' ', '-')}.yaml"
        
        file_path = Path(file_path)
        
        # 確保目錄存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # 根據配置類型保存格式
            if config.config_type == ConfigType.ENVIRONMENT and "raw_content" in config.content:
                # 環境變數配置直接保存原始內容
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(config.content["raw_content"])
            else:
                # 其他配置使用 YAML 格式
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config.content, f, default_flow_style=False, allow_unicode=True)
            
            # 更新配置文件路徑
            config.file_path = str(file_path)
            config.updated_at = datetime.now()
            
            self.logger.info(f"配置已保存到: {file_path}")
            return str(file_path)
            
        except Exception as e:
            self.logger.error(f"保存配置失敗: {e}")
            raise
    
    def load_config(self, file_path: str) -> CIConfig:
        """從文件載入配置"""
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {file_path}")
        
        try:
            # 載入文件內容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析內容
            if file_path.suffix in ['.yml', '.yaml']:
                parsed_content = yaml.safe_load(content)
            elif file_path.suffix == '.json':
                parsed_content = json.loads(content)
            elif file_path.suffix == '.env':
                # 環境變數文件特殊處理
                parsed_content = {"raw_content": content}
            else:
                # 默認使用 YAML 解析
                parsed_content = yaml.safe_load(content)
            
            # 判斷配置類型
            config_type = self._detect_config_type(file_path, parsed_content)
            
            # 創建配置對象
            config = CIConfig(
                name=file_path.stem,
                config_type=config_type,
                version="1.0.0",
                description=f"從文件載入: {file_path}",
                content=parsed_content,
                metadata={
                    "source_file": str(file_path),
                    "loaded_at": datetime.now().isoformat()
                },
                created_at=datetime.now(),
                updated_at=datetime.now(),
                file_path=str(file_path)
            )
            
            self.configs[config.name] = config
            self.logger.info(f"配置已載入: {file_path}")
            
            return config
            
        except Exception as e:
            self.logger.error(f"載入配置失敗: {e}")
            raise
    
    def _detect_config_type(self, file_path: Path, content: Any) -> ConfigType:
        """檢測配置類型"""
        
        # 根據文件路徑判斷
        if '.github/workflows' in str(file_path):
            return ConfigType.WORKFLOW
        elif 'k8s' in str(file_path) or 'kubernetes' in str(file_path):
            return ConfigType.DEPLOYMENT
        elif file_path.suffix == '.env':
            return ConfigType.ENVIRONMENT
        elif 'security' in str(file_path).lower():
            return ConfigType.SECURITY
        
        # 根據內容判斷
        if isinstance(content, dict):
            if 'jobs' in content and 'on' in content:
                return ConfigType.WORKFLOW
            elif 'apiVersion' in content and 'kind' in content:
                if content.get('kind') == 'Deployment':
                    return ConfigType.DEPLOYMENT
                elif content.get('kind') == 'CronJob':
                    return ConfigType.WORKFLOW
        
        # 默認為環境配置
        return ConfigType.ENVIRONMENT
    
    def get_config_list(self, config_type: ConfigType = None) -> List[CIConfig]:
        """獲取配置列表"""
        
        configs = list(self.configs.values())
        
        if config_type:
            configs = [c for c in configs if c.config_type == config_type]
        
        return configs
    
    def get_template_list(self, config_type: ConfigType = None) -> List[ConfigTemplate]:
        """獲取模板列表"""
        
        templates = list(self.templates.values())
        
        if config_type:
            templates = [t for t in templates if t.config_type == config_type]
        
        return templates
    
    def update_config(self, config_name: str, updates: Dict[str, Any]) -> CIConfig:
        """更新配置"""
        
        if config_name not in self.configs:
            raise ValueError(f"配置 '{config_name}' 不存在")
        
        config = self.configs[config_name]
        
        # 更新內容
        if 'content' in updates:
            config.content.update(updates['content'])
        
        if 'metadata' in updates:
            config.metadata.update(updates['metadata'])
        
        if 'description' in updates:
            config.description = updates['description']
        
        config.updated_at = datetime.now()
        
        # 重新驗證
        is_valid, errors = self.validate_config(config)
        if not is_valid:
            self.logger.warning(f"更新後的配置驗證失敗: {errors}")
        
        self.logger.info(f"配置 '{config_name}' 已更新")
        return config
    
    def delete_config(self, config_name: str, delete_file: bool = False) -> bool:
        """刪除配置"""
        
        if config_name not in self.configs:
            return False
        
        config = self.configs[config_name]
        
        # 刪除文件
        if delete_file and config.file_path:
            file_path = Path(config.file_path)
            if file_path.exists():
                file_path.unlink()
                self.logger.info(f"已删除配置文件: {file_path}")
        
        # 刪除配置
        del self.configs[config_name]
        self.logger.info(f"配置 '{config_name}' 已删除")
        
        return True
    
    def export_configs(self, output_dir: str, config_type: ConfigType = None) -> List[str]:
        """導出配置到指定目錄"""
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        exported_files = []
        configs = self.get_config_list(config_type)
        
        for config in configs:
            file_name = f"{config.name.replace(' ', '_')}.yaml"
            file_path = output_dir / file_name
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config.content, f, default_flow_style=False, allow_unicode=True)
                
                exported_files.append(str(file_path))
                
            except Exception as e:
                self.logger.error(f"導出配置 '{config.name}' 失敗: {e}")
        
        self.logger.info(f"已導出 {len(exported_files)} 個配置到: {output_dir}")
        return exported_files
    
    def import_configs_from_directory(self, directory: str) -> List[CIConfig]:
        """從目錄導入配置"""
        
        directory = Path(directory)
        
        if not directory.exists():
            raise FileNotFoundError(f"目錄不存在: {directory}")
        
        imported_configs = []
        
        # 支持的文件擴展名
        extensions = ['.yml', '.yaml', '.json', '.env']
        
        for file_path in directory.rglob('*'):
            if file_path.is_file() and file_path.suffix in extensions:
                try:
                    config = self.load_config(str(file_path))
                    imported_configs.append(config)
                    
                except Exception as e:
                    self.logger.error(f"導入配置文件失敗 {file_path}: {e}")
        
        self.logger.info(f"已導入 {len(imported_configs)} 個配置")
        return imported_configs
    
    def generate_config_documentation(self, config_name: str) -> str:
        """生成配置文檔"""
        
        if config_name not in self.configs:
            raise ValueError(f"配置 '{config_name}' 不存在")
        
        config = self.configs[config_name]
        
        doc = f"""
# {config.name}

## 基本信息
- **配置類型**: {config.config_type.value}
- **版本**: {config.version}
- **描述**: {config.description}
- **創建時間**: {config.created_at.strftime('%Y-%m-%d %H:%M:%S')}
- **更新時間**: {config.updated_at.strftime('%Y-%m-%d %H:%M:%S')}

## 配置內容
```yaml
{yaml.dump(config.content, default_flow_style=False, allow_unicode=True)}
```

## 元數據
```json
{json.dumps(config.metadata, indent=2, ensure_ascii=False)}
```
"""
        
        return doc


# 使用示例
if __name__ == "__main__":
    # 初始化配置管理器
    manager = CIConfigManager()
    
    # 從模板創建 CI 工作流配置
    workflow_vars = {
        'workflow_name': 'CI Pipeline',
        'triggers': [
            {'type': 'push', 'branches': ['main', 'develop']},
            {'type': 'pull_request', 'branches': ['main']}
        ],
        'jobs': [
            {
                'name': 'test',
                'runner': 'ubuntu-latest',
                'steps': [
                    {
                        'name': 'Checkout code',
                        'uses': 'actions/checkout@v4'
                    },
                    {
                        'name': 'Run tests',
                        'run': 'pytest tests/'
                    }
                ]
            }
        ]
    }
    
    ci_config = manager.create_config_from_template(
        'ci-workflow',
        workflow_vars,
        'CI Pipeline',
        '標準 CI 流水線配置'
    )
    
    # 驗證配置
    is_valid, errors = manager.validate_config(ci_config)
    print(f"配置驗證結果: {is_valid}")
    if errors:
        print(f"驗證錯誤: {errors}")
    
    # 保存配置
    file_path = manager.save_config(ci_config)
    print(f"配置已保存到: {file_path}")
    
    # 生成文檔
    doc = manager.generate_config_documentation('CI Pipeline')
    print(doc)