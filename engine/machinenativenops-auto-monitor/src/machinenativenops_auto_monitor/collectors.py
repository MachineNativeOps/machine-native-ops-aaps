"""
Metric Collectors
指標收集器

Collects various metrics from the system and services.
"""

import logging
import platform
import psutil
import subprocess
from abc import ABC, abstractmethod
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class MetricCollector(ABC):
    """Base class for metric collectors"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize collector"""
        self.config = config or {}
    
    @abstractmethod
    def collect(self) -> Dict[str, Any]:
        """Collect metrics"""
        pass


class SystemCollector(MetricCollector):
    """Collects system-level metrics"""
    
    def collect(self) -> Dict[str, Any]:
        """Collect system metrics"""
        try:
            metrics = {
                "timestamp": psutil.time.time(),
                "hostname": platform.node(),
                "platform": platform.system(),
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory": self._collect_memory(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk": self._collect_disk(),
                "disk_percent": psutil.disk_usage('/').percent,
                "network": self._collect_network(),
                "load_average": self._collect_load_average(),
            }
            return metrics
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {}
    
    def _collect_memory(self) -> Dict[str, Any]:
        """Collect memory metrics"""
        mem = psutil.virtual_memory()
        return {
            "total": mem.total,
            "available": mem.available,
            "used": mem.used,
            "percent": mem.percent,
        }
    
    def _collect_disk(self) -> Dict[str, Any]:
        """Collect disk metrics"""
        disk = psutil.disk_usage('/')
        return {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent,
        }
    
    def _collect_network(self) -> Dict[str, Any]:
        """Collect network metrics"""
        net = psutil.net_io_counters()
        return {
            "bytes_sent": net.bytes_sent,
            "bytes_recv": net.bytes_recv,
            "packets_sent": net.packets_sent,
            "packets_recv": net.packets_recv,
            "errin": net.errin,
            "errout": net.errout,
            "dropin": net.dropin,
            "dropout": net.dropout,
        }
    
    def _collect_load_average(self) -> List[float]:
        """Collect system load average"""
        try:
            return list(psutil.getloadavg())
        except (AttributeError, OSError):
            # getloadavg() may not be available on all platforms
            return [0.0, 0.0, 0.0]


class ServiceCollector(MetricCollector):
    """Collects service health metrics"""
    
    def collect(self) -> Dict[str, Any]:
        """Collect service metrics"""
        services = self.config.get("monitored_services", [])
        
        service_metrics = {
            "timestamp": psutil.time.time(),
            "services": {}
        }
        
        for service in services:
            if isinstance(service, str):
                service_name = service
                service_config = {}
            else:
                service_name = service.get("name", "unknown")
                service_config = service
            
            service_metrics["services"][service_name] = self._check_service(
                service_name,
                service_config
            )
        
        return service_metrics
    
    def _check_service(self, service_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Check individual service health"""
        check_type = config.get("type", "process")
        
        if check_type == "process":
            return self._check_process(service_name, config)
        elif check_type == "http":
            return self._check_http_endpoint(service_name, config)
        elif check_type == "port":
            return self._check_port(service_name, config)
        else:
            logger.warning(f"Unknown service check type: {check_type}")
            return {"healthy": False, "error": "unknown check type"}
    
    def _check_process(self, service_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Check if a process is running"""
        process_name = config.get("process_name", service_name)
        
        try:
            for proc in psutil.process_iter(['name', 'status']):
                if proc.info['name'] == process_name:
                    return {
                        "healthy": True,
                        "status": "running",
                        "pid": proc.pid,
                        "memory_percent": proc.memory_percent(),
                        "cpu_percent": proc.cpu_percent(interval=0.1),
                    }
            
            return {
                "healthy": False,
                "status": "not_found",
                "error": f"Process {process_name} not found"
            }
        
        except Exception as e:
            logger.error(f"Error checking process {process_name}: {e}")
            return {
                "healthy": False,
                "status": "error",
                "error": str(e)
            }
    
    def _check_http_endpoint(self, service_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Check HTTP endpoint health"""
        # TODO: Implement HTTP health check
        logger.warning(f"HTTP health check not implemented for {service_name}")
        return {"healthy": True, "status": "unknown"}
    
    def _check_port(self, service_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Check if a port is listening"""
        port = config.get("port")
        if not port:
            return {"healthy": False, "error": "No port specified"}
        
        try:
            connections = psutil.net_connections(kind='inet')
            for conn in connections:
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    return {
                        "healthy": True,
                        "status": "listening",
                        "port": port
                    }
            
            return {
                "healthy": False,
                "status": "not_listening",
                "port": port
            }
        
        except Exception as e:
            logger.error(f"Error checking port {port}: {e}")
            return {
                "healthy": False,
                "status": "error",
                "error": str(e)
            }


class ApplicationMetricCollector(MetricCollector):
    """Collects application-specific metrics"""
    
    def collect(self) -> Dict[str, Any]:
        """Collect application metrics"""
        metrics = {
            "timestamp": psutil.time.time(),
            "applications": {}
        }
        
        # Collect metrics for each configured application
        apps = self.config.get("applications", [])
        for app in apps:
            app_name = app.get("name", "unknown")
            metrics["applications"][app_name] = self._collect_app_metrics(app)
        
        return metrics
    
    def _collect_app_metrics(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        """Collect metrics for a specific application"""
        # TODO: Implement application-specific metric collection
        # This could query application APIs, parse log files, etc.
        return {
            "status": "unknown",
            "message": "Application metrics not implemented"
        }
