"""
MachineNativeOps Auto-Monitor Package
自動監控套件

This package provides automated monitoring capabilities for the MachineNativeOps platform.
"""

__version__ = "0.1.0"
__author__ = "MachineNativeOps"

from .alerts import AlertManager, Alert, AlertSeverity
from .collectors import MetricCollector, SystemCollector, ServiceCollector
from .config import MonitorConfig, load_config
from .app import AutoMonitorApp

__all__ = [
    "AlertManager",
    "Alert",
    "AlertSeverity",
    "MetricCollector",
    "SystemCollector",
    "ServiceCollector",
    "MonitorConfig",
    "load_config",
    "AutoMonitorApp",
]
