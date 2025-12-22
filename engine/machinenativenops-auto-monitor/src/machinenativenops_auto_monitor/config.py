"""
Configuration Module
配置模組

Manages configuration for the auto-monitor system.
"""

import logging
from pathlib import Path
from typing import Any, Dict
import yaml

logger = logging.getLogger(__name__)


# Type alias for configuration
MonitorConfig = Dict[str, Any]


def load_config(config_path: Path = None) -> MonitorConfig:
    """
    Load monitoring configuration from YAML file
    
    Args:
        config_path: Path to configuration file
    
    Returns:
        Configuration dictionary
    """
    if config_path and config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {e}")
            logger.info("Using default configuration")
    
    return get_default_config()


def get_default_config() -> MonitorConfig:
    """Get default monitoring configuration"""
    return {
        "version": "1.0.0",
        "system": {
            "enabled": True,
            "interval": 60,
        },
        "services": {
            "enabled": True,
            "monitored_services": [
                {
                    "name": "synergymesh-core",
                    "type": "process",
                    "process_name": "python",
                },
                {
                    "name": "contract-service",
                    "type": "process",
                    "process_name": "node",
                },
            ]
        },
        "metrics": {
            "enabled": True,
            "applications": []
        },
        "alerts": {
            "enabled": True,
            "alert_rules": {
                "cpu_threshold": 80.0,
                "memory_threshold": 85.0,
                "disk_threshold": 90.0,
                "service_down_threshold": 1
            },
            "notifications": {
                "enabled": False,
                "channels": []
            }
        },
        "storage": {
            "type": "memory",
            "retention_days": 7
        }
    }


def validate_config(config: MonitorConfig) -> bool:
    """
    Validate configuration
    
    Args:
        config: Configuration to validate
    
    Returns:
        True if valid, False otherwise
    """
    required_keys = ["version", "system", "services", "metrics", "alerts"]
    
    for key in required_keys:
        if key not in config:
            logger.error(f"Missing required config key: {key}")
            return False
    
    # Validate alert thresholds
    alert_rules = config.get("alerts", {}).get("alert_rules", {})
    for threshold_name, threshold_value in alert_rules.items():
        if not isinstance(threshold_value, (int, float)):
            logger.error(f"Invalid threshold value for {threshold_name}: {threshold_value}")
            return False
        if threshold_value < 0 or threshold_value > 100:
            logger.warning(f"Threshold {threshold_name} = {threshold_value} is outside normal range [0-100]")
    
    logger.info("Configuration validation passed")
    return True


def save_config(config: MonitorConfig, config_path: Path):
    """
    Save configuration to YAML file
    
    Args:
        config: Configuration to save
        config_path: Path to save configuration
    """
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        logger.info(f"Saved configuration to {config_path}")
    except Exception as e:
        logger.error(f"Error saving config to {config_path}: {e}")
        raise
