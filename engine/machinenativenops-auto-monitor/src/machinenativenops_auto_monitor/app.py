"""
Auto-Monitor Application
自動監控應用程式

Main application logic for the auto-monitor system.
"""

import logging
import time
from typing import Any, Dict

from .alerts import AlertManager, AlertSeverity
from .collectors import SystemCollector, ServiceCollector, MetricCollector
from .config import MonitorConfig

logger = logging.getLogger(__name__)


class AutoMonitorApp:
    """Main auto-monitor application"""
    
    def __init__(self, config: MonitorConfig):
        """Initialize auto-monitor app"""
        self.config = config
        self.alert_manager = AlertManager(config.get("alerts", {}))
        
        # Initialize collectors
        self.system_collector = SystemCollector(config.get("system", {}))
        self.service_collector = ServiceCollector(config.get("services", {}))
        self.metric_collector = MetricCollector(config.get("metrics", {}))
        
        self.running = False
        logger.info("Auto-monitor initialized")
    
    def collect_once(self):
        """Perform one collection cycle"""
        logger.info("Starting collection cycle...")
        
        try:
            # Collect system metrics
            system_metrics = self.system_collector.collect()
            logger.debug(f"Collected system metrics: {system_metrics}")
            
            # Collect service status
            service_metrics = self.service_collector.collect()
            logger.debug(f"Collected service metrics: {service_metrics}")
            
            # Collect custom metrics
            custom_metrics = self.metric_collector.collect()
            logger.debug(f"Collected custom metrics: {custom_metrics}")
            
            # Store metrics
            self._store_metrics({
                "system": system_metrics,
                "services": service_metrics,
                "custom": custom_metrics
            })
            
            logger.info("Collection cycle complete")
            
        except Exception as e:
            logger.error(f"Error during collection: {e}", exc_info=True)
    
    def check_alerts_once(self):
        """Perform one alert checking cycle"""
        logger.info("Checking alerts...")
        
        try:
            # Collect current metrics
            system_metrics = self.system_collector.collect()
            service_metrics = self.service_collector.collect()
            
            # Check system metrics against thresholds
            self._check_system_alerts(system_metrics)
            
            # Check service health
            self._check_service_alerts(service_metrics)
            
            # Log alert summary
            summary = self.alert_manager.get_alert_summary()
            if summary["total"] > 0:
                logger.warning(f"Active alerts: {summary}")
            else:
                logger.info("No active alerts")
            
        except Exception as e:
            logger.error(f"Error checking alerts: {e}", exc_info=True)
    
    def _check_system_alerts(self, metrics: Dict[str, Any]):
        """Check system metrics and create alerts if needed"""
        # Check CPU usage
        if "cpu_percent" in metrics:
            alert = self.alert_manager.check_metric(
                "cpu", 
                metrics["cpu_percent"]
            )
            if alert:
                self.alert_manager.add_alert(alert)
            else:
                self.alert_manager.resolve_alert("cpu_high", "auto-monitor")
        
        # Check memory usage
        if "memory_percent" in metrics:
            alert = self.alert_manager.check_metric(
                "memory",
                metrics["memory_percent"]
            )
            if alert:
                self.alert_manager.add_alert(alert)
            else:
                self.alert_manager.resolve_alert("memory_high", "auto-monitor")
        
        # Check disk usage
        if "disk_percent" in metrics:
            alert = self.alert_manager.check_metric(
                "disk",
                metrics["disk_percent"]
            )
            if alert:
                self.alert_manager.add_alert(alert)
            else:
                self.alert_manager.resolve_alert("disk_high", "auto-monitor")
    
    def _check_service_alerts(self, metrics: Dict[str, Any]):
        """Check service health and create alerts if needed"""
        services = metrics.get("services", {})
        
        for service_name, service_data in services.items():
            if not service_data.get("healthy", True):
                from .alerts import Alert
                alert = Alert(
                    name=f"service_{service_name}_down",
                    severity=AlertSeverity.ERROR,
                    message=f"Service {service_name} is unhealthy",
                    source="auto-monitor",
                    metadata={
                        "service": service_name,
                        "status": service_data.get("status", "unknown")
                    }
                )
                self.alert_manager.add_alert(alert)
            else:
                self.alert_manager.resolve_alert(
                    f"service_{service_name}_down",
                    "auto-monitor"
                )
    
    def _store_metrics(self, metrics: Dict[str, Any]):
        """Store collected metrics"""
        # TODO: Implement metric storage (e.g., to database, time-series DB, etc.)
        storage_config = self.config.get("storage", {})
        storage_type = storage_config.get("type", "memory")
        
        if storage_type == "memory":
            # Just log for now
            logger.debug(f"Storing metrics (memory): {len(metrics)} categories")
        else:
            logger.warning(f"Storage type {storage_type} not implemented")
    
    def run(self, interval: int = 60, daemon: bool = False):
        """
        Run auto-monitor continuously
        
        Args:
            interval: Collection interval in seconds
            daemon: Run as daemon (background process)
        """
        self.running = True
        logger.info(f"Starting auto-monitor (interval: {interval}s, daemon: {daemon})")
        
        iteration = 0
        
        try:
            while self.running:
                iteration += 1
                logger.info(f"Starting iteration {iteration}")
                
                # Collect metrics
                self.collect_once()
                
                # Check alerts
                self.check_alerts_once()
                
                # Clean up resolved alerts
                self.alert_manager.clear_resolved_alerts()
                
                # Wait for next interval
                if self.running:
                    logger.debug(f"Sleeping for {interval}s...")
                    time.sleep(interval)
        
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
            self.stop()
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            self.stop()
            raise
    
    def stop(self):
        """Stop the auto-monitor"""
        logger.info("Stopping auto-monitor...")
        self.running = False
        
        # Final alert summary
        summary = self.alert_manager.get_alert_summary()
        if summary["total"] > 0:
            logger.warning(f"Shutting down with {summary['total']} active alerts")
            for alert in self.alert_manager.get_active_alerts():
                logger.warning(f"  - {alert.name}: {alert.message}")
