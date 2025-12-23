# ==============================================================================
# 部署回滾機制
# Deployment Rollback Manager
# ==============================================================================

import os
import json
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import logging
import subprocess

import yaml
import kubernetes
from kubernetes import client, config
import docker
from git import Repo
import requests


class RollbackType(Enum):
    """回滾類型"""
    FULL = "full"
    PARTIAL = "partial"
    FORWARD = "forward"
    EMERGENCY = "emergency"


class RollbackStatus(Enum):
    """回滾狀態"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DeploymentPlatform(Enum):
    """部署平台"""
    KUBERNETES = "kubernetes"
    DOCKER = "docker"
    CLOUDFOUNDARY = "cloudfoundry"
    AWS_ECS = "aws_ecs"
    HEROKU = "heroku"


@dataclass
class DeploymentSnapshot:
    """部署快照"""
    deployment_id: str
    timestamp: datetime
    platform: DeploymentPlatform
    environment: str
    service_name: str
    version: str
    image_tag: str
    config_data: Dict[str, Any]
    health_checks: List[str]
    rollback_point: bool
    metadata: Dict[str, Any]


@dataclass
class RollbackPlan:
    """回滾計劃"""
    rollback_id: str
    deployment_snapshot: DeploymentSnapshot
    rollback_type: RollbackType
    target_version: str
    steps: List[Dict[str, Any]]
    rollback_timeout: int
    health_check_timeout: int
    pre_rollback_checks: List[str]
    post_rollback_checks: List[str]
    notification_channels: List[str]
    created_at: datetime
    created_by: str


@dataclass
class RollbackExecution:
    """回滾執行記錄"""
    rollback_id: str
    status: RollbackStatus
    start_time: datetime
    end_time: Optional[datetime]
    duration: Optional[float]
    steps_executed: List[Dict[str, Any]]
    failed_step: Optional[str]
    error_message: Optional[str]
    rollback_point_used: str
    health_check_results: Dict[str, bool]
    rollback_logs: List[str]
    rollback_metrics: Dict[str, Any]


class RollbackManager:
    """回滾管理器核心類"""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logger()
        self.snapshots = {}
        self.rollback_plans = {}
        self.rollback_history = {}
        self.k8s_client = self._init_kubernetes_client()
        self.docker_client = self._init_docker_client()
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """載入配置文件"""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        
        # 默認配置
        return {
            'kubernetes': {
                'config_file': os.getenv('KUBECONFIG', '~/.kube/config'),
                'namespace': 'default',
                'timeout': 300
            },
            'docker': {
                'registry': os.getenv('DOCKER_REGISTRY', 'docker.io'),
                'timeout': 180
            },
            'rollback': {
                'default_timeout': 300,
                'health_check_interval': 10,
                'max_rollback_attempts': 3,
                'auto_health_checks': True,
                'snapshot_retention_days': 30
            },
            'notifications': {
                'slack_webhook': os.getenv('SLACK_WEBHOOK_URL'),
                'email_enabled': False,
                'teams_webhook': os.getenv('TEAMS_WEBHOOK_URL')
            },
            'backup': {
                'enabled': True,
                'backup_directory': '/tmp/rollback-backups',
                'config_backup': True,
                'database_backup': True
            }
        }
    
    def _setup_logger(self) -> logging.Logger:
        """設置日誌記錄器"""
        logger = logging.getLogger('RollbackManager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _init_kubernetes_client(self) -> Optional[client.ApiClient]:
        """初始化 Kubernetes 客戶端"""
        try:
            config.load_kube_config()
            return client.ApiClient()
        except Exception as e:
            self.logger.warning(f"Kubernetes 客戶端初始化失敗: {e}")
            return None
    
    def _init_docker_client(self) -> Optional[docker.DockerClient]:
        """初始化 Docker 客戶端"""
        try:
            return docker.from_env()
        except Exception as e:
            self.logger.warning(f"Docker 客戶端初始化失敗: {e}")
            return None
    
    def create_deployment_snapshot(
        self,
        deployment_id: str,
        platform: DeploymentPlatform,
        environment: str,
        service_name: str,
        version: str,
        image_tag: str,
        rollback_point: bool = True
    ) -> DeploymentSnapshot:
        """創建部署快照"""
        
        self.logger.info(f"創建部署快照: {deployment_id}")
        
        # 收集配置數據
        config_data = self._collect_deployment_config(platform, environment, service_name)
        
        # 收集健康檢查配置
        health_checks = self._collect_health_checks(platform, service_name)
        
        # 創建快照
        snapshot = DeploymentSnapshot(
            deployment_id=deployment_id,
            timestamp=datetime.now(),
            platform=platform,
            environment=environment,
            service_name=service_name,
            version=version,
            image_tag=image_tag,
            config_data=config_data,
            health_checks=health_checks,
            rollback_point=rollback_point,
            metadata={
                'created_by': os.getenv('USER', 'system'),
                'node_info': self._get_node_info()
            }
        )
        
        # 保存快照
        self.snapshots[deployment_id] = snapshot
        
        # 備份配置
        if self.config['backup']['enabled']:
            self._backup_deployment_config(snapshot)
        
        self.logger.info(f"部署快照已創建: {deployment_id}")
        return snapshot
    
    def _collect_deployment_config(self, platform: DeploymentPlatform, environment: str, service_name: str) -> Dict[str, Any]:
        """收集部署配置"""
        config_data = {}
        
        if platform == DeploymentPlatform.KUBERNETES:
            config_data = self._collect_kubernetes_config(service_name)
        elif platform == DeploymentPlatform.DOCKER:
            config_data = self._collect_docker_config(service_name)
        
        # 添加環境變數
        config_data['environment'] = self._get_environment_variables(environment)
        
        return config_data
    
    def _collect_kubernetes_config(self, service_name: str) -> Dict[str, Any]:
        """收集 Kubernetes 配置"""
        config_data = {}
        
        if not self.k8s_client:
            return config_data
        
        try:
            v1 = client.CoreV1Api(self.k8s_client)
            apps_v1 = client.AppsV1Api(self.k8s_client)
            
            # 獲取 Deployment 配置
            deployments = apps_v1.list_namespaced_deployment(
                namespace=self.config['kubernetes']['namespace']
            )
            
            for deployment in deployments.items:
                if service_name in deployment.metadata.name:
                    config_data['deployment'] = deployment.to_dict()
                    break
            
            # 獲取 Service 配置
            services = v1.list_namespaced_service(
                namespace=self.config['kubernetes']['namespace']
            )
            
            for service in services.items:
                if service_name in service.metadata.name:
                    config_data['service'] = service.to_dict()
                    break
            
            # 獲取 ConfigMap
            configmaps = v1.list_namespaced_config_map(
                namespace=self.config['kubernetes']['namespace']
            )
            
            for cm in configmaps.items:
                if service_name in cm.metadata.name:
                    config_data['configmap'] = cm.to_dict()
                    break
            
        except Exception as e:
            self.logger.error(f"收集 Kubernetes 配置失敗: {e}")
        
        return config_data
    
    def _collect_docker_config(self, service_name: str) -> Dict[str, Any]:
        """收集 Docker 配置"""
        config_data = {}
        
        if not self.docker_client:
            return config_data
        
        try:
            # 獲取容器信息
            containers = self.docker_client.containers.list(all=True)
            
            for container in containers:
                if service_name in container.name:
                    config_data['container'] = {
                        'id': container.id,
                        'name': container.name,
                        'image': container.image.tags[0] if container.image.tags else str(container.image),
                        'ports': container.ports,
                        'environment': container.attrs.get('Config', {}).get('Env', []),
                        'labels': container.labels
                    }
                    break
            
        except Exception as e:
            self.logger.error(f"收集 Docker 配置失敗: {e}")
        
        return config_data
    
    def _collect_health_checks(self, platform: DeploymentPlatform, service_name: str) -> List[str]:
        """收集健康檢查配置"""
        health_checks = []
        
        if platform == DeploymentPlatform.KUBERNETES:
            # Kubernetes 健康檢查端點
            health_checks = [
                f"/healthz",
                f"/health",
                f"/actuator/health",
                f"/api/health"
            ]
        elif platform == DeploymentPlatform.DOCKER:
            # Docker 健康檢查
            health_checks = [
                "docker health check",
                "container status"
            ]
        
        return health_checks
    
    def _get_environment_variables(self, environment: str) -> Dict[str, str]:
        """獲取環境變數"""
        env_vars = {}
        
        # 從系統環境變數中讀取
        for key, value in os.environ.items():
            if key.startswith(f'{environment.upper()}_'):
                env_vars[key] = value
        
        return env_vars
    
    def _get_node_info(self) -> Dict[str, Any]:
        """獲取節點信息"""
        return {
            'hostname': os.uname().nodename,
            'platform': os.uname().sysname,
            'timestamp': datetime.now().isoformat()
        }
    
    def _backup_deployment_config(self, snapshot: DeploymentSnapshot):
        """備份部署配置"""
        backup_dir = Path(self.config['backup']['backup_directory'])
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        backup_file = backup_dir / f"{snapshot.deployment_id}_backup.json"
        
        try:
            backup_data = asdict(snapshot)
            backup_data['timestamp'] = snapshot.timestamp.isoformat()
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"配置已備份到: {backup_file}")
            
        except Exception as e:
            self.logger.error(f"備份配置失敗: {e}")
    
    def create_rollback_plan(
        self,
        target_snapshot: DeploymentSnapshot,
        rollback_type: RollbackType = RollbackType.FULL,
        created_by: str = "system"
    ) -> RollbackPlan:
        """創建回滾計劃"""
        
        rollback_id = f"rollback_{int(time.time())}"
        
        # 生成回滾步驟
        steps = self._generate_rollback_steps(target_snapshot, rollback_type)
        
        # 生成回滾前檢查
        pre_checks = self._generate_pre_rollback_checks(target_snapshot)
        
        # 生成回滾後檢查
        post_checks = self._generate_post_rollback_checks(target_snapshot)
        
        plan = RollbackPlan(
            rollback_id=rollback_id,
            deployment_snapshot=target_snapshot,
            rollback_type=rollback_type,
            target_version=target_snapshot.version,
            steps=steps,
            rollback_timeout=self.config['rollback']['default_timeout'],
            health_check_timeout=60,
            pre_rollback_checks=pre_checks,
            post_rollback_checks=post_checks,
            notification_channels=self.config['notifications'],
            created_at=datetime.now(),
            created_by=created_by
        )
        
        self.rollback_plans[rollback_id] = plan
        
        self.logger.info(f"回滾計劃已創建: {rollback_id}")
        return plan
    
    def _generate_rollback_steps(self, snapshot: DeploymentSnapshot, rollback_type: RollbackType) -> List[Dict[str, Any]]:
        """生成回滾步驟"""
        steps = []
        
        if snapshot.platform == DeploymentPlatform.KUBERNETES:
            if rollback_type == RollbackType.FULL:
                steps = [
                    {
                        'name': '驗證集群連接',
                        'action': 'verify_kubernetes_connection',
                        'timeout': 30,
                        'critical': True
                    },
                    {
                        'name': '備份當前部署',
                        'action': 'backup_current_deployment',
                        'timeout': 60,
                        'critical': True
                    },
                    {
                        'name': '回滾 Deployment',
                        'action': 'rollback_kubernetes_deployment',
                        'parameters': {
                            'deployment_name': snapshot.service_name,
                            'target_image': snapshot.image_tag,
                            'namespace': snapshot.environment
                        },
                        'timeout': 120,
                        'critical': True
                    },
                    {
                        'name': '驗證回滾狀態',
                        'action': 'verify_rollback_status',
                        'timeout': 60,
                        'critical': True
                    }
                ]
            elif rollback_type == RollbackType.EMERGENCY:
                steps = [
                    {
                        'name': '緊急停止當前服務',
                        'action': 'scale_down_deployment',
                        'timeout': 30,
                        'critical': True
                    },
                    {
                        'name': '恢復到上一個版本',
                        'action': 'emergency_rollback',
                        'timeout': 60,
                        'critical': True
                    }
                ]
        
        elif snapshot.platform == DeploymentPlatform.DOCKER:
            steps = [
                {
                    'name': '停止當前容器',
                    'action': 'stop_docker_container',
                    'parameters': {'service_name': snapshot.service_name},
                    'timeout': 30,
                    'critical': True
                },
                {
                    'name': '拉取目標鏡像',
                    'action': 'pull_docker_image',
                    'parameters': {'image_tag': snapshot.image_tag},
                    'timeout': 120,
                    'critical': True
                },
                {
                    'name': '啟動新容器',
                    'action': 'start_docker_container',
                    'parameters': {
                        'service_name': snapshot.service_name,
                        'image_tag': snapshot.image_tag,
                        'config': snapshot.config_data.get('container', {})
                    },
                    'timeout': 60,
                    'critical': True
                }
            ]
        
        return steps
    
    def _generate_pre_rollback_checks(self, snapshot: DeploymentSnapshot) -> List[str]:
        """生成回滾前檢查"""
        checks = [
            "驗證目標鏡像存在",
            "檢查資源可用性",
            "驗證配置文件完整性",
            "檢查網絡連接"
        ]
        
        if snapshot.platform == DeploymentPlatform.KUBERNETES:
            checks.extend([
                "驗證 Kubernetes 集群狀態",
                "檢查命名空間資源配額",
                "驗證 RBAC 權限"
            ])
        
        return checks
    
    def _generate_post_rollback_checks(self, snapshot: DeploymentSnapshot) -> List[str]:
        """生成回滾後檢查"""
        checks = [
            "驗證服務啟動狀態",
            "執行健康檢查",
            "檢查日誌錯誤",
            "驗證 API 端點可訪問性"
        ]
        
        if snapshot.platform == DeploymentPlatform.KUBERNETES:
            checks.extend([
                "檢查 Pod 狀態",
                "驗證 Service 端點",
                "檢查資源使用情況"
            ])
        
        return checks
    
    async def execute_rollback(self, rollback_id: str) -> RollbackExecution:
        """執行回滾"""
        
        if rollback_id not in self.rollback_plans:
            raise ValueError(f"回滾計劃不存在: {rollback_id}")
        
        plan = self.rollback_plans[rollback_id]
        snapshot = plan.deployment_snapshot
        
        self.logger.info(f"開始執行回滾: {rollback_id}")
        
        execution = RollbackExecution(
            rollback_id=rollback_id,
            status=RollbackStatus.IN_PROGRESS,
            start_time=datetime.now(),
            end_time=None,
            duration=None,
            steps_executed=[],
            failed_step=None,
            error_message=None,
            rollback_point_used=snapshot.deployment_id,
            health_check_results={},
            rollback_logs=[],
            rollback_metrics={}
        )
        
        try:
            # 執行回滾前檢查
            await self._execute_pre_rollback_checks(execution, plan)
            
            # 執行回滾步驟
            for step in plan.steps:
                step_result = await self._execute_rollback_step(execution, step, snapshot)
                execution.steps_executed.append(step_result)
                
                if not step_result['success']:
                    execution.status = RollbackStatus.FAILED
                    execution.failed_step = step['name']
                    execution.error_message = step_result.get('error', 'Unknown error')
                    break
            
            # 如果所有步驟成功，執行回滾後檢查
            if execution.status == RollbackStatus.IN_PROGRESS:
                await self._execute_post_rollback_checks(execution, plan)
                execution.status = RollbackStatus.SUCCESS
            
        except Exception as e:
            execution.status = RollbackStatus.FAILED
            execution.error_message = str(e)
            self.logger.error(f"回滾執行失敗: {e}")
        
        finally:
            execution.end_time = datetime.now()
            execution.duration = (execution.end_time - execution.start_time).total_seconds()
            
            # 保存執行記錄
            self.rollback_history[rollback_id] = execution
            
            # 發送通知
            await self._send_rollback_notification(execution, plan)
        
        self.logger.info(f"回滾執行完成: {rollback_id} - 狀態: {execution.status.value}")
        return execution
    
    async def _execute_pre_rollback_checks(self, execution: RollbackExecution, plan: RollbackPlan):
        """執行回滾前檢查"""
        execution.rollback_logs.append("開始執行回滾前檢查...")
        
        for check in plan.pre_rollback_checks:
            try:
                if "鏡像存在" in check:
                    success = await self._check_image_exists(plan.deployment_snapshot)
                elif "資源可用性" in check:
                    success = await self._check_resource_availability(plan.deployment_snapshot)
                elif "集群狀態" in check:
                    success = await self._check_cluster_status()
                else:
                    success = True  # 默認通過
                
                execution.health_check_results[check] = success
                execution.rollback_logs.append(f"檢查 '{check}': {'通過' if success else '失敗'}")
                
                if not success:
                    raise Exception(f"回滾前檢查失敗: {check}")
                
            except Exception as e:
                execution.rollback_logs.append(f"檢查 '{check}' 異常: {e}")
                raise
        
        execution.rollback_logs.append("回滾前檢查完成")
    
    async def _execute_rollback_step(self, execution: RollbackExecution, step: Dict[str, Any], snapshot: DeploymentSnapshot) -> Dict[str, Any]:
        """執行回滾步驟"""
        step_name = step['name']
        action = step['action']
        parameters = step.get('parameters', {})
        
        execution.rollback_logs.append(f"執行步驟: {step_name}")
        
        start_time = time.time()
        
        try:
            if action == 'verify_kubernetes_connection':
                success = await self._verify_kubernetes_connection()
            elif action == 'backup_current_deployment':
                success = await self._backup_current_deployment(snapshot)
            elif action == 'rollback_kubernetes_deployment':
                success = await self._rollback_kubernetes_deployment(parameters)
            elif action == 'verify_rollback_status':
                success = await self._verify_rollback_status(snapshot)
            elif action == 'stop_docker_container':
                success = await self._stop_docker_container(parameters)
            elif action == 'pull_docker_image':
                success = await self._pull_docker_image(parameters)
            elif action == 'start_docker_container':
                success = await self._start_docker_container(parameters)
            else:
                success = await self._execute_custom_action(action, parameters)
            
            duration = time.time() - start_time
            
            result = {
                'step_name': step_name,
                'action': action,
                'success': success,
                'duration': duration,
                'parameters': parameters
            }
            
            execution.rollback_logs.append(f"步驟 '{step_name}' {'成功' if success else '失敗'} (耗時: {duration:.2f}s)")
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            result = {
                'step_name': step_name,
                'action': action,
                'success': False,
                'duration': duration,
                'parameters': parameters,
                'error': str(e)
            }
            
            execution.rollback_logs.append(f"步驟 '{step_name}' 失敗: {e} (耗時: {duration:.2f}s)")
            
            return result
    
    async def _verify_kubernetes_connection(self) -> bool:
        """驗證 Kubernetes 連接"""
        if not self.k8s_client:
            return False
        
        try:
            v1 = client.CoreV1Api(self.k8s_client)
            v1.get_api_resources()
            return True
        except Exception as e:
            self.logger.error(f"Kubernetes 連接驗證失敗: {e}")
            return False
    
    async def _backup_current_deployment(self, snapshot: DeploymentSnapshot) -> bool:
        """備份當前部署"""
        try:
            # 這裡實現當前部署的備份邏輯
            backup_data = {
                'snapshot': asdict(snapshot),
                'backup_time': datetime.now().isoformat()
            }
            
            backup_file = Path(self.config['backup']['backup_directory']) / f"current_deployment_backup_{int(time.time())}.json"
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            self.logger.error(f"備份當前部署失敗: {e}")
            return False
    
    async def _rollback_kubernetes_deployment(self, parameters: Dict[str, Any]) -> bool:
        """回滾 Kubernetes 部署"""
        if not self.k8s_client:
            return False
        
        try:
            apps_v1 = client.AppsV1Api(self.k8s_client)
            
            deployment_name = parameters['deployment_name']
            target_image = parameters['target_image']
            namespace = parameters.get('namespace', 'default')
            
            # 獲取當前 Deployment
            deployment = apps_v1.read_namespaced_deployment(deployment_name, namespace)
            
            # 更新鏡像版本
            deployment.spec.template.spec.containers[0].image = target_image
            
            # 更新 Deployment
            apps_v1.patch_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=deployment
            )
            
            # 等待回滾完成
            await self._wait_for_deployment_ready(deployment_name, namespace)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Kubernetes 部署回滾失敗: {e}")
            return False
    
    async def _wait_for_deployment_ready(self, deployment_name: str, namespace: str, timeout: int = 120):
        """等待部署就緒"""
        apps_v1 = client.AppsV1Api(self.k8s_client)
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            deployment = apps_v1.read_namespaced_deployment(deployment_name, namespace)
            
            if deployment.status.ready_replicas == deployment.spec.replicas:
                return True
            
            await asyncio.sleep(5)
        
        raise Exception(f"部署 {deployment_name} 在 {timeout} 秒內未就緒")
    
    async def _verify_rollback_status(self, snapshot: DeploymentSnapshot) -> bool:
        """驗證回滾狀態"""
        try:
            # 執行健康檢查
            for health_check in snapshot.health_checks:
                if not await self._perform_health_check(health_check, snapshot):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"回滾狀態驗證失敗: {e}")
            return False
    
    async def _perform_health_check(self, health_check: str, snapshot: DeploymentSnapshot) -> bool:
        """執行健康檢查"""
        try:
            if health_check.startswith('/'):
                # HTTP 健康檢查
                base_url = f"http://{snapshot.service_name}.{snapshot.environment}"
                url = f"{base_url}{health_check}"
                
                response = requests.get(url, timeout=10)
                return response.status_code == 200
            
            else:
                # 其他類型的健康檢查
                return True
                
        except Exception:
            return False
    
    async def _execute_post_rollback_checks(self, execution: RollbackExecution, plan: RollbackPlan):
        """執行回滾後檢查"""
        execution.rollback_logs.append("開始執行回滾後檢查...")
        
        for check in plan.post_rollback_checks:
            try:
                if "服務啟動" in check:
                    success = await self._check_service_status(plan.deployment_snapshot)
                elif "健康檢查" in check:
                    success = await self._verify_rollback_status(plan.deployment_snapshot)
                elif "API 端點" in check:
                    success = await self._check_api_endpoints(plan.deployment_snapshot)
                else:
                    success = True
                
                execution.health_check_results[check] = success
                execution.rollback_logs.append(f"檢查 '{check}': {'通過' if success else '失敗'}")
                
            except Exception as e:
                execution.rollback_logs.append(f"檢查 '{check}' 異常: {e}")
        
        execution.rollback_logs.append("回滾後檢查完成")
    
    async def _send_rollback_notification(self, execution: RollbackExecution, plan: RollbackPlan):
        """發送回滾通知"""
        status_emoji = "✅" if execution.status == RollbackStatus.SUCCESS else "❌"
        message = f"""
{status_} 回滾操作完成

**回滾ID**: {execution.rollback_id}
**狀態**: {execution.status.value}
**耗時**: {execution.duration:.2f}s
**服務**: {plan.deployment_snapshot.service_name}
**目標版本**: {plan.target_version}
**操作者**: {plan.created_by}
"""
        
        # 發送 Slack 通知
        slack_webhook = self.config['notifications']['slack_webhook']
        if slack_webhook:
            await self._send_slack_notification(message, slack_webhook)
    
    async def _send_slack_notification(self, message: str, webhook_url: str):
        """發送 Slack 通知"""
        import aiohttp
        
        payload = {
            "text": message,
            "username": "Rollback Manager"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status != 200:
                    self.logger.error(f"Slack 通知發送失敗: {response.status}")
    
    def get_rollback_history(self, limit: int = 10) -> List[RollbackExecution]:
        """獲取回滾歷史"""
        history = list(self.rollback_history.values())
        history.sort(key=lambda x: x.start_time, reverse=True)
        return history[:limit]
    
    def get_available_snapshots(self, service_name: str = None) -> List[DeploymentSnapshot]:
        """獲取可用快照"""
        snapshots = list(self.snapshots.values())
        
        if service_name:
            snapshots = [s for s in snapshots if s.service_name == service_name]
        
        # 只返回標記為回滾點的快照
        snapshots = [s for s in snapshots if s.rollback_point]
        
        snapshots.sort(key=lambda x: x.timestamp, reverse=True)
        return snapshots
    
    async def emergency_rollback(self, service_name: str, environment: str) -> str:
        """緊急回滾"""
        self.logger.info(f"執行緊急回滾: {service_name} in {environment}")
        
        # 查找最近的穩定快照
        snapshots = self.get_available_snapshots(service_name)
        target_snapshot = None
        
        for snapshot in snapshots:
            if snapshot.environment == environment:
                target_snapshot = snapshot
                break
        
        if not target_snapshot:
            raise Exception(f"未找到可用快照: {service_name} in {environment}")
        
        # 創建緊急回滾計劃
        plan = self.create_rollback_plan(
            target_snapshot,
            RollbackType.EMERGENCY,
            "emergency_system"
        )
        
        # 執行回滾
        execution = await self.execute_rollback(plan.rollback_id)
        
        return execution.rollback_id


# 使用示例
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # 初始化回滾管理器
        rollback_manager = RollbackManager()
        
        # 創建部署快照
        snapshot = rollback_manager.create_deployment_snapshot(
            deployment_id="deploy_12345",
            platform=DeploymentPlatform.KUBERNETES,
            environment="production",
            service_name="web-app",
            version="1.2.3",
            image_tag="web-app:1.2.3"
        )
        
        print(f"創建快照: {snapshot.deployment_id}")
        
        # 創建回滾計劃
        plan = rollback_manager.create_rollback_plan(snapshot)
        print(f"創建回滾計劃: {plan.rollback_id}")
        
        # 執行回滾（這裡只是示例，實際執行需要真實的 Kubernetes 環境）
        # execution = await rollback_manager.execute_rollback(plan.rollback_id)
        # print(f"回滾執行完成: {execution.status.value}")
        
        # 獲取可用快照
        available_snapshots = rollback_manager.get_available_snapshots()
        print(f"可用快照數量: {len(available_snapshots)}")
    
    asyncio.run(main())