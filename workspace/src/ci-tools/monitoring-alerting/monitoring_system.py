# ==============================================================================
# 監控告警系統
# Monitoring and Alerting System
# ==============================================================================

import os
import json
import time
import asyncio
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import logging
import threading

import prometheus_client
from prometheus_client import CollectorRegistry, Gauge, Counter, Histogram, generate_latest
import requests
import yaml
import psutil
import aiohttp
from redis import Redis


class MetricType(Enum):
    """指標類型"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class AlertSeverity(Enum):
    """告警嚴重程度"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertStatus(Enum):
    """告警狀態"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    SILENCED = "silenced"
    SUPPRESSED = "suppressed"


@dataclass
class MetricData:
    """指標數據"""
    name: str
    value: float
    labels: Dict[str, str]
    timestamp: datetime
    metric_type: MetricType
    help_text: str


@dataclass
class AlertRule:
    """告警規則"""
    rule_id: str
    name: str
    description: str
    metric_name: str
    condition: str  # "> 100", "< 50", "== 0", etc.
    threshold: float
    severity: AlertSeverity
    for_duration: int  # 持續時間（秒）
    labels: Dict[str, str]
    annotations: Dict[str, str]
    enabled: bool = True
    evaluation_interval: int = 60  # 評估間隔（秒）


@dataclass
class Alert:
    """告警"""
    alert_id: str
    rule_id: str
    status: AlertStatus
    severity: AlertSeverity
    start_time: datetime
    end_time: Optional[datetime]
    message: str
    labels: Dict[str, str]
    annotations: Dict[str, str]
    evaluation_count: int = 0
    last_evaluated: Optional[datetime] = None


@dataclass
class NotificationChannel:
    """通知渠道"""
    channel_id: str
    name: str
    type: str  # 'slack', 'email', 'webhook', 'teams'
    config: Dict[str, Any]
    enabled: bool = True
    rate_limit: int = 60  # 速率限制（秒）


class MonitoringSystem:
    """監控系統核心類"""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logger()
        self.metrics_registry = CollectorRegistry()
        self.prometheus_metrics = {}
        self.alert_rules = {}
        self.active_alerts = {}
        self.notification_channels = {}
        self.metric_data = []
        self.redis_client = self._init_redis_client()
        
        # 初始化系統監控
        self._init_system_metrics()
        
        # 啟動監控任務
        self.monitoring_tasks = []
        self.alert_evaluation_task = None
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """載入配置文件"""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        
        # 默認配置
        return {
            'prometheus': {
                'enabled': True,
                'port': 8090,
                'endpoint': '/metrics'
            },
            'metrics': {
                'retention_hours': 24,
                'collection_interval': 30,
                'batch_size': 100
            },
            'alerts': {
                'evaluation_interval': 60,
                'max_alerts_per_rule': 10,
                'alert_history_retention_days': 7
            },
            'notifications': {
                'default_rate_limit': 300,
                'max_notifications_per_minute': 10,
                'retry_attempts': 3,
                'retry_delay': 30
            },
            'redis': {
                'host': os.getenv('REDIS_HOST', 'localhost'),
                'port': int(os.getenv('REDIS_PORT', 6379)),
                'db': int(os.getenv('REDIS_DB', 0)),
                'enabled': False
            }
        }
    
    def _setup_logger(self) -> logging.Logger:
        """設置日誌記錄器"""
        logger = logging.getLogger('MonitoringSystem')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _init_redis_client(self) -> Optional[Redis]:
        """初始化 Redis 客戶端"""
        if not self.config['redis']['enabled']:
            return None
        
        try:
            redis_config = self.config['redis']
            return Redis(
                host=redis_config['host'],
                port=redis_config['port'],
                db=redis_config['db'],
                decode_responses=True
            )
        except Exception as e:
            self.logger.warning(f"Redis 連接失敗: {e}")
            return None
    
    def _init_system_metrics(self):
        """初始化系統監控指標"""
        # CPU 使用率
        self.create_metric(
            name="system_cpu_usage_percent",
            metric_type=MetricType.GAUGE,
            help_text="System CPU usage percentage",
            labels={"node": os.uname().nodename}
        )
        
        # 內存使用率
        self.create_metric(
            name="system_memory_usage_percent",
            metric_type=MetricType.GAUGE,
            help_text="System memory usage percentage",
            labels={"node": os.uname().nodename}
        )
        
        # 磁盤使用率
        self.create_metric(
            name="system_disk_usage_percent",
            metric_type=MetricType.GAUGE,
            help_text="System disk usage percentage",
            labels={"node": os.uname().nodename}
        )
        
        # 網絡 I/O
        self.create_metric(
            name="system_network_bytes_sent",
            metric_type=MetricType.COUNTER,
            help_text="System network bytes sent",
            labels={"node": os.uname().nodename}
        )
        
        self.create_metric(
            name="system_network_bytes_recv",
            metric_type=MetricType.COUNTER,
            help_text="System network bytes received",
            labels={"node": os.uname().nodename}
        )
        
        # 應用指標
        self.create_metric(
            name="http_requests_total",
            metric_type=MetricType.COUNTER,
            help_text="Total HTTP requests",
            labels={"method", "status", "endpoint"}
        )
        
        self.create_metric(
            name="http_request_duration_seconds",
            metric_type=MetricType.HISTOGRAM,
            help_text="HTTP request duration in seconds",
            labels={"method", "endpoint"}
        )
        
        self.create_metric(
            name="application_errors_total",
            metric_type=MetricType.COUNTER,
            help_text="Total application errors",
            labels={"error_type", "component"}
        )
    
    def create_metric(
        self,
        name: str,
        metric_type: MetricType,
        help_text: str,
        labels: Dict[str, str] = None,
        buckets: List[float] = None
    ):
        """創建 Prometheus 指標"""
        
        if name in self.prometheus_metrics:
            self.logger.warning(f"指標 '{name}' 已存在")
            return
        
        try:
            if metric_type == MetricType.COUNTER:
                metric = Counter(
                    name,
                    help_text,
                    list(labels.keys()) if labels else [],
                    registry=self.metrics_registry
                )
            elif metric_type == MetricType.GAUGE:
                metric = Gauge(
                    name,
                    help_text,
                    list(labels.keys()) if labels else [],
                    registry=self.metrics_registry
                )
            elif metric_type == MetricType.HISTOGRAM:
                default_buckets = [0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
                metric = Histogram(
                    name,
                    help_text,
                    list(labels.keys()) if labels else [],
                    buckets=buckets or default_buckets,
                    registry=self.metrics_registry
                )
            else:
                raise ValueError(f"不支持的指標類型: {metric_type}")
            
            self.prometheus_metrics[name] = {
                'metric': metric,
                'type': metric_type,
                'help_text': help_text,
                'labels': labels or {}
            }
            
            self.logger.info(f"已創建指標: {name}")
            
        except Exception as e:
            self.logger.error(f"創建指標失敗 '{name}': {e}")
    
    def record_metric(self, name: str, value: float, labels: Dict[str, str] = None):
        """記錄指標數據"""
        
        if name not in self.prometheus_metrics:
            self.logger.error(f"指標 '{name}' 不存在")
            return
        
        try:
            metric_info = self.prometheus_metrics[name]
            metric = metric_info['metric']
            metric_type = metric_info['type']
            
            # 合併標籤
            final_labels = {**(metric_info['labels'] or {}), **(labels or {})}
            
            if metric_type == MetricType.COUNTER:
                if final_labels:
                    metric.labels(**final_labels).inc(value)
                else:
                    metric.inc(value)
            elif metric_type == MetricType.GAUGE:
                if final_labels:
                    metric.labels(**final_labels).set(value)
                else:
                    metric.set(value)
            elif metric_type == MetricType.HISTOGRAM:
                if final_labels:
                    metric.labels(**final_labels).observe(value)
                else:
                    metric.observe(value)
            
            # 保存到內存數據
            metric_data = MetricData(
                name=name,
                value=value,
                labels=final_labels,
                timestamp=datetime.now(),
                metric_type=metric_type,
                help_text=metric_info['help_text']
            )
            
            self.metric_data.append(metric_data)
            
            # 保存到 Redis（如果可用）
            if self.redis_client:
                self._save_metric_to_redis(metric_data)
            
            # 清理舊數據
            self._cleanup_old_metrics()
            
        except Exception as e:
            self.logger.error(f"記錄指標失敗 '{name}': {e}")
    
    def _save_metric_to_redis(self, metric_data: MetricData):
        """保存指標數據到 Redis"""
        try:
            key = f"metric:{metric_data.name}"
            data = {
                'value': metric_data.value,
                'labels': metric_data.labels,
                'timestamp': metric_data.timestamp.isoformat(),
                'type': metric_data.metric_type.value
            }
            
            self.redis_client.lpush(key, json.dumps(data))
            self.redis_client.expire(key, self.config['metrics']['retention_hours'] * 3600)
            
        except Exception as e:
            self.logger.error(f"保存指標到 Redis 失敗: {e}")
    
    def _cleanup_old_metrics(self):
        """清理舊的指標數據"""
        retention_time = datetime.now() - timedelta(hours=self.config['metrics']['retention_hours'])
        
        # 保留最近的數據
        max_items = self.config['metrics']['batch_size'] * 10
        
        # 按時間排序並刪除舊數據
        self.metric_data.sort(key=lambda x: x.timestamp, reverse=True)
        
        if len(self.metric_data) > max_items:
            self.metric_data = self.metric_data[:max_items]
        
        # 刪除過期的數據
        self.metric_data = [
            m for m in self.metric_data 
            if m.timestamp > retention_time
        ]
    
    def create_alert_rule(
        self,
        rule_id: str,
        name: str,
        description: str,
        metric_name: str,
        condition: str,
        threshold: float,
        severity: AlertSeverity,
        for_duration: int = 60,
        labels: Dict[str, str] = None,
        annotations: Dict[str, str] = None,
        evaluation_interval: int = 60
    ) -> AlertRule:
        """創建告警規則"""
        
        rule = AlertRule(
            rule_id=rule_id,
            name=name,
            description=description,
            metric_name=metric_name,
            condition=condition,
            threshold=threshold,
            severity=severity,
            for_duration=for_duration,
            labels=labels or {},
            annotations=annotations or {},
            enabled=True,
            evaluation_interval=evaluation_interval
        )
        
        self.alert_rules[rule_id] = rule
        self.logger.info(f"已創建告警規則: {rule_id}")
        
        return rule
    
    def create_notification_channel(
        self,
        channel_id: str,
        name: str,
        channel_type: str,
        config: Dict[str, Any],
        enabled: bool = True,
        rate_limit: int = 300
    ) -> NotificationChannel:
        """創建通知渠道"""
        
        channel = NotificationChannel(
            channel_id=channel_id,
            name=name,
            type=channel_type,
            config=config,
            enabled=enabled,
            rate_limit=rate_limit
        )
        
        self.notification_channels[channel_id] = channel
        self.logger.info(f"已創建通知渠道: {channel_id}")
        
        return channel
    
    async def evaluate_alert_rules(self):
        """評估告警規則"""
        while True:
            try:
                for rule_id, rule in self.alert_rules.items():
                    if not rule.enabled:
                        continue
                    
                    await self._evaluate_alert_rule(rule)
                
                await asyncio.sleep(self.config['alerts']['evaluation_interval'])
                
            except Exception as e:
                self.logger.error(f"告警規則評估失敗: {e}")
                await asyncio.sleep(10)
    
    async def _evaluate_alert_rule(self, rule: AlertRule):
        """評估單個告警規則"""
        try:
            # 獲取最新的指標數據
            current_value = self._get_latest_metric_value(rule.metric_name, rule.labels)
            
            if current_value is None:
                return
            
            # 評估條件
            is_triggered = self._evaluate_condition(current_value, rule.condition, rule.threshold)
            
            # 檢查是否已經存在告警
            existing_alert = self.active_alerts.get(rule_id)
            
            if is_triggered:
                if not existing_alert:
                    # 創建新告警
                    await self._create_alert(rule, current_value)
                else:
                    # 更新現有告警
                    await self._update_alert(existing_alert, current_value)
            else:
                if existing_alert and existing_alert.status == AlertStatus.ACTIVE:
                    # 解決告警
                    await self._resolve_alert(existing_alert)
                
        except Exception as e:
            self.logger.error(f"評估告警規則失敗 '{rule.rule_id}': {e}")
    
    def _get_latest_metric_value(self, metric_name: str, labels: Dict[str, str] = None) -> Optional[float]:
        """獲取最新的指標數據"""
        
        # 從內存數據中查找
        for metric_data in reversed(self.metric_data):
            if metric_data.name == metric_name:
                # 檢查標籤是否匹配
                if not labels or all(metric_data.labels.get(k) == v for k, v in labels.items()):
                    return metric_data.value
        
        # 從 Redis 中查找
        if self.redis_client:
            try:
                key = f"metric:{metric_name}"
                data = self.redis_client.lindex(key, 0)  # 獲取最新數據
                
                if data:
                    metric_info = json.loads(data)
                    if not labels or all(metric_info['labels'].get(k) == v for k, v in labels.items()):
                        return metric_info['value']
                        
            except Exception as e:
                self.logger.error(f"從 Redis 獲取指標失敗: {e}")
        
        return None
    
    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """評估條件"""
        try:
            if condition == ">":
                return value > threshold
            elif condition == ">=":
                return value >= threshold
            elif condition == "<":
                return value < threshold
            elif condition == "<=":
                return value <= threshold
            elif condition == "==":
                return value == threshold
            elif condition == "!=":
                return value != threshold
            else:
                self.logger.warning(f"不支持的條件: {condition}")
                return False
                
        except Exception as e:
            self.logger.error(f"條件評估失敗: {e}")
            return False
    
    async def _create_alert(self, rule: AlertRule, current_value: float):
        """創建告警"""
        
        alert_id = f"alert_{rule.rule_id}_{int(time.time())}"
        
        message = f"告警 '{rule.name}' 觸發 - {rule.metric_name} = {current_value} {rule.condition} {rule.threshold}"
        
        alert = Alert(
            alert_id=alert_id,
            rule_id=rule.rule_id,
            status=AlertStatus.ACTIVE,
            severity=rule.severity,
            start_time=datetime.now(),
            end_time=None,
            message=message,
            labels=rule.labels.copy(),
            annotations=rule.annotations.copy(),
            evaluation_count=1,
            last_evaluated=datetime.now()
        )
        
        self.active_alerts[rule.rule_id] = alert
        
        self.logger.warning(f"告警已觸發: {message}")
        
        # 發送通知
        await self._send_alert_notification(alert, rule)
    
    async def _update_alert(self, alert: Alert, current_value: float):
        """更新告警"""
        alert.evaluation_count += 1
        alert.last_evaluated = datetime.now()
        
        # 檢查是否持續時間足夠
        duration = (datetime.now() - alert.start_time).total_seconds()
        rule = self.alert_rules[alert.rule_id]
        
        if duration >= rule.for_duration:
            # 發送持續告警通知
            await self._send_alert_notification(alert, rule)
    
    async def _resolve_alert(self, alert: Alert):
        """解決告警"""
        alert.status = AlertStatus.RESOLVED
        alert.end_time = datetime.now()
        
        self.logger.info(f"告警已解決: {alert.alert_id}")
        
        # 發送解決通知
        rule = self.alert_rules[alert.rule_id]
        await self._send_alert_notification(alert, rule)
    
    async def _send_alert_notification(self, alert: Alert, rule: AlertRule):
        """發送告警通知"""
        
        for channel_id, channel in self.notification_channels.items():
            if not channel.enabled:
                continue
            
            try:
                await self._send_notification_to_channel(alert, rule, channel)
                
            except Exception as e:
                self.logger.error(f"發送通知失敗 '{channel_id}': {e}")
    
    async def _send_notification_to_channel(self, alert: Alert, rule: AlertRule, channel: NotificationChannel):
        """發送通知到指定渠道"""
        
        if channel.type == 'slack':
            await self._send_slack_notification(alert, rule, channel)
        elif channel.type == 'webhook':
            await self._send_webhook_notification(alert, rule, channel)
        elif channel.type == 'email':
            await self._send_email_notification(alert, rule, channel)
        elif channel.type == 'teams':
            await self._send_teams_notification(alert, rule, channel)
        else:
            self.logger.warning(f"不支持的通知渠道類型: {channel.type}")
    
    async def _send_slack_notification(self, alert: Alert, rule: AlertRule, channel: NotificationChannel):
        """發送 Slack 通知"""
        
        webhook_url = channel.config.get('webhook_url')
        if not webhook_url:
            return
        
        # 確定顏色
        colors = {
            AlertSeverity.INFO: "#36a64f",
            AlertSeverity.WARNING: "#ff9500",
            AlertSeverity.CRITICAL: "#ff0000",
            AlertSeverity.EMERGENCY: "#8b0000"
        }
        
        color = colors.get(alert.severity, "#36a64f")
        
        # 構建消息
        status_emoji = "🔴" if alert.status == AlertStatus.ACTIVE else "✅"
        
        payload = {
            "text": f"{status_emoji} {alert.message}",
            "attachments": [{
                "color": color,
                "fields": [
                    {"title": "告警名稱", "value": rule.name, "short": True},
                    {"title": "嚴重程度", "value": alert.severity.value.upper(), "short": True},
                    {"title": "開始時間", "value": alert.start_time.strftime('%Y-%m-%d %H:%M:%S'), "short": True},
                    {"title": "評估次數", "value": str(alert.evaluation_count), "short": True}
                ],
                "footer": "監控系統",
                "ts": int(alert.start_time.timestamp())
            }]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status != 200:
                    self.logger.error(f"Slack 通知發送失敗: {response.status}")
    
    async def _send_webhook_notification(self, alert: Alert, rule: AlertRule, channel: NotificationChannel):
        """發送 Webhook 通知"""
        
        webhook_url = channel.config.get('url')
        if not webhook_url:
            return
        
        payload = {
            "alert_id": alert.alert_id,
            "rule_id": rule.rule_id,
            "status": alert.status.value,
            "severity": alert.severity.value,
            "message": alert.message,
            "start_time": alert.start_time.isoformat(),
            "end_time": alert.end_time.isoformat() if alert.end_time else None,
            "labels": alert.labels,
            "annotations": alert.annotations
        }
        
        headers = channel.config.get('headers', {})
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload, headers=headers) as response:
                if response.status not in [200, 201, 204]:
                    self.logger.error(f"Webhook 通知發送失敗: {response.status}")
    
    async def _send_email_notification(self, alert: Alert, rule: AlertRule, channel: NotificationChannel):
        """發送郵件通知"""
        # 這裡需要實現郵件發送邏輯
        # 簡化實現，實際應該使用 SMTP 或郵件服務
        self.logger.info(f"發送郵件通知: {alert.message}")
    
    async def _send_teams_notification(self, alert: Alert, rule: AlertRule, channel: NotificationChannel):
        """發送 Teams 通知"""
        
        webhook_url = channel.config.get('webhook_url')
        if not webhook_url:
            return
        
        # 確定顏色
        colors = {
            AlertSeverity.INFO: "00FF00",
            AlertSeverity.WARNING: "FFFF00",
            AlertSeverity.CRITICAL: "FF0000",
            AlertSeverity.EMERGENCY: "8B0000"
        }
        
        color = colors.get(alert.severity, "00FF00")
        
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": color,
            "summary": alert.message,
            "sections": [{
                "activityTitle": alert.message,
                "activitySubtitle": rule.description,
                "facts": [
                    {"name": "告警名稱", "value": rule.name},
                    {"name": "嚴重程度", "value": alert.severity.value.upper()},
                    {"name": "狀態", "value": alert.status.value},
                    {"name": "開始時間", "value": alert.start_time.strftime('%Y-%m-%d %H:%M:%S')}
                ],
                "markdown": True
            }]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status != 200:
                    self.logger.error(f"Teams 通知發送失敗: {response.status}")
    
    def collect_system_metrics(self):
        """收集系統指標"""
        while True:
            try:
                # CPU 使用率
                cpu_percent = psutil.cpu_percent(interval=1)
                self.record_metric("system_cpu_usage_percent", cpu_percent)
                
                # 內存使用率
                memory = psutil.virtual_memory()
                self.record_metric("system_memory_usage_percent", memory.percent)
                
                # 磁盤使用率
                disk = psutil.disk_usage('/')
                disk_percent = (disk.used / disk.total) * 100
                self.record_metric("system_disk_usage_percent", disk_percent)
                
                # 網絡 I/O
                net_io = psutil.net_io_counters()
                self.record_metric("system_network_bytes_sent", net_io.bytes_sent)
                self.record_metric("system_network_bytes_recv", net_io.bytes_recv)
                
                time.sleep(self.config['metrics']['collection_interval'])
                
            except Exception as e:
                self.logger.error(f"收集系統指標失敗: {e}")
                time.sleep(10)
    
    def start_prometheus_server(self):
        """啟動 Prometheus 指標服務器"""
        
        if not self.config['prometheus']['enabled']:
            return
        
        from prometheus_client import start_http_server
        
        port = self.config['prometheus']['port']
        start_http_server(port, registry=self.metrics_registry)
        
        self.logger.info(f"Prometheus 指標服務器已啟動: http://localhost:{port}{self.config['prometheus']['endpoint']}")
    
    def get_metrics_data(self, metric_name: str = None, start_time: datetime = None, end_time: datetime = None) -> List[MetricData]:
        """獲取指標數據"""
        
        data = self.metric_data
        
        # 過濾指標名稱
        if metric_name:
            data = [m for m in data if m.name == metric_name]
        
        # 過濾時間範圍
        if start_time:
            data = [m for m in data if m.timestamp >= start_time]
        
        if end_time:
            data = [m for m in data if m.timestamp <= end_time]
        
        return data
    
    def get_active_alerts(self) -> List[Alert]:
        """獲取活躍告警"""
        return [alert for alert in self.active_alerts.values() if alert.status == AlertStatus.ACTIVE]
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """獲取告警歷史"""
        history = list(self.active_alerts.values())
        history.sort(key=lambda x: x.start_time, reverse=True)
        return history[:limit]
    
    def start_monitoring(self):
        """啟動監控系統"""
        self.logger.info("啟動監控系統...")
        
        # 啟動 Prometheus 服務器
        self.start_prometheus_server()
        
        # 啟動系統指標收集
        system_metrics_thread = threading.Thread(target=self.collect_system_metrics, daemon=True)
        system_metrics_thread.start()
        
        # 啟動告警評估任務
        if self.alert_evaluation_task is None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.alert_evaluation_task = loop.create_task(self.evaluate_alert_rules())
            threading.Thread(target=lambda: loop.run_forever(), daemon=True).start()
        
        self.logger.info("監控系統已啟動")
    
    def stop_monitoring(self):
        """停止監控系統"""
        self.logger.info("停止監控系統...")
        
        if self.alert_evaluation_task:
            self.alert_evaluation_task.cancel()
        
        self.logger.info("監控系統已停止")


# 使用示例
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # 初始化監控系統
        monitoring = MonitoringSystem()
        
        # 創建告警規則
        monitoring.create_alert_rule(
            rule_id="high_cpu",
            name="高 CPU 使用率",
            description="CPU 使用率超過 80%",
            metric_name="system_cpu_usage_percent",
            condition=">",
            threshold=80.0,
            severity=AlertSeverity.WARNING,
            for_duration=60
        )
        
        # 創建通知渠道
        monitoring.create_notification_channel(
            channel_id="slack_alerts",
            name="Slack 告警",
            channel_type="slack",
            config={
                "webhook_url": os.getenv("SLACK_WEBHOOK_URL")
            }
        )
        
        # 啟動監控
        monitoring.start_monitoring()
        
        # 模擬一些指標數據
        for i in range(100):
            monitoring.record_metric(
                "http_requests_total",
                i,
                {"method": "GET", "status": "200", "endpoint": "/api/users"}
            )
            await asyncio.sleep(1)
    
    asyncio.run(main())