"""
Alert Management Module
告警管理模組

Manages alerts and notifications for the auto-monitor system.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Alert:
    """Represents a monitoring alert"""
    name: str
    severity: AlertSeverity
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def resolve(self):
        """Mark alert as resolved"""
        self.resolved = True
        self.resolved_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "severity": self.severity.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "metadata": self.metadata,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }


class AlertManager:
    """Manages alerts and alert rules"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize alert manager"""
        self.config = config or {}
        self.active_alerts: List[Alert] = []
        self.alert_history: List[Alert] = []
        self.alert_rules = self._load_alert_rules()
    
    def _load_alert_rules(self) -> Dict[str, Any]:
        """Load alert rules from configuration"""
        return self.config.get("alert_rules", {
            "cpu_threshold": 80.0,
            "memory_threshold": 85.0,
            "disk_threshold": 90.0,
            "service_down_threshold": 1
        })
    
    def check_metric(self, metric_name: str, value: float, threshold: float = None) -> Optional[Alert]:
        """
        Check if a metric exceeds threshold and create alert if needed
        
        Args:
            metric_name: Name of the metric
            value: Current metric value
            threshold: Alert threshold (uses configured default if not provided)
        
        Returns:
            Alert object if threshold exceeded, None otherwise
        """
        if threshold is None:
            threshold = self.alert_rules.get(f"{metric_name}_threshold", 100.0)
        
        if value >= threshold:
            severity = self._determine_severity(metric_name, value, threshold)
            alert = Alert(
                name=f"{metric_name}_high",
                severity=severity,
                message=f"{metric_name} is at {value:.1f}% (threshold: {threshold}%)",
                source="auto-monitor",
                metadata={
                    "metric": metric_name,
                    "value": value,
                    "threshold": threshold
                }
            )
            return alert
        
        return None
    
    def _determine_severity(self, metric_name: str, value: float, threshold: float) -> AlertSeverity:
        """Determine alert severity based on how much threshold is exceeded"""
        if value >= threshold * 1.2:  # 20% over threshold
            return AlertSeverity.CRITICAL
        elif value >= threshold * 1.1:  # 10% over threshold
            return AlertSeverity.ERROR
        elif value >= threshold:
            return AlertSeverity.WARNING
        else:
            return AlertSeverity.INFO
    
    def add_alert(self, alert: Alert):
        """Add a new alert"""
        # Check if similar alert already exists
        existing = self._find_similar_alert(alert)
        if existing:
            logger.debug(f"Alert {alert.name} already exists, updating...")
            existing.timestamp = alert.timestamp
            existing.metadata = alert.metadata
        else:
            logger.info(f"New alert: {alert.name} - {alert.severity.value} - {alert.message}")
            self.active_alerts.append(alert)
            self._notify_alert(alert)
    
    def _find_similar_alert(self, alert: Alert) -> Optional[Alert]:
        """Find existing similar alert"""
        for existing_alert in self.active_alerts:
            if (existing_alert.name == alert.name and 
                existing_alert.source == alert.source and
                not existing_alert.resolved):
                return existing_alert
        return None
    
    def resolve_alert(self, alert_name: str, source: str = ""):
        """Resolve an active alert"""
        for alert in self.active_alerts:
            if alert.name == alert_name and (not source or alert.source == source):
                if not alert.resolved:
                    alert.resolve()
                    logger.info(f"Resolved alert: {alert_name}")
                    self.alert_history.append(alert)
                    self.active_alerts.remove(alert)
                    return True
        return False
    
    def _notify_alert(self, alert: Alert):
        """Send alert notifications"""
        # TODO: Implement notification channels (email, slack, webhook, etc.)
        logger.warning(f"ALERT: [{alert.severity.value}] {alert.message}")
    
    def get_active_alerts(self, severity: AlertSeverity = None) -> List[Alert]:
        """Get all active alerts, optionally filtered by severity"""
        if severity:
            return [a for a in self.active_alerts if a.severity == severity]
        return self.active_alerts.copy()
    
    def get_alert_summary(self) -> Dict[str, int]:
        """Get summary of active alerts by severity"""
        summary = {
            "total": len(self.active_alerts),
            "critical": 0,
            "error": 0,
            "warning": 0,
            "info": 0
        }
        
        for alert in self.active_alerts:
            summary[alert.severity.value] += 1
        
        return summary
    
    def clear_resolved_alerts(self):
        """Move all resolved alerts to history"""
        resolved = [a for a in self.active_alerts if a.resolved]
        for alert in resolved:
            self.alert_history.append(alert)
            self.active_alerts.remove(alert)
        
        logger.info(f"Cleared {len(resolved)} resolved alerts")
