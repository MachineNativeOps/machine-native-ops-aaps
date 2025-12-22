"""
Storage Module (儲存模組)
數據儲存模組

Handles metric and alert data storage.
處理指標和告警數據的儲存。
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MetricStorage:
    """Base class for metric storage"""
    
    def store_metric(self, metric_name: str, value: Any, timestamp: datetime = None):
        """Store a metric value"""
        raise NotImplementedError
    
    def retrieve_metrics(
        self,
        metric_name: str,
        start_time: datetime = None,
        end_time: datetime = None
    ) -> List[Dict[str, Any]]:
        """Retrieve metric values"""
        raise NotImplementedError
    
    def delete_old_metrics(self, older_than: datetime):
        """Delete metrics older than specified time"""
        raise NotImplementedError


class MemoryStorage(MetricStorage):
    """In-memory metric storage (for development/testing)"""
    
    def __init__(self, max_size: int = 10000):
        """Initialize memory storage"""
        self.metrics: Dict[str, List[Dict[str, Any]]] = {}
        self.max_size = max_size
    
    def store_metric(self, metric_name: str, value: Any, timestamp: datetime = None):
        """Store a metric value in memory"""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        
        self.metrics[metric_name].append({
            "value": value,
            "timestamp": timestamp.isoformat()
        })
        
        # Trim if exceeds max size
        if len(self.metrics[metric_name]) > self.max_size:
            self.metrics[metric_name] = self.metrics[metric_name][-self.max_size:]
        
        logger.debug(f"Stored metric {metric_name} = {value}")
    
    def retrieve_metrics(
        self,
        metric_name: str,
        start_time: datetime = None,
        end_time: datetime = None
    ) -> List[Dict[str, Any]]:
        """Retrieve metric values from memory"""
        if metric_name not in self.metrics:
            return []
        
        metrics = self.metrics[metric_name]
        
        if start_time or end_time:
            filtered_metrics = []
            for metric in metrics:
                metric_time = datetime.fromisoformat(metric["timestamp"])
                
                if start_time and metric_time < start_time:
                    continue
                if end_time and metric_time > end_time:
                    continue
                
                filtered_metrics.append(metric)
            
            return filtered_metrics
        
        return metrics.copy()
    
    def delete_old_metrics(self, older_than: datetime):
        """Delete metrics older than specified time"""
        deleted_count = 0
        
        for metric_name in list(self.metrics.keys()):
            original_count = len(self.metrics[metric_name])
            
            self.metrics[metric_name] = [
                m for m in self.metrics[metric_name]
                if datetime.fromisoformat(m["timestamp"]) >= older_than
            ]
            
            deleted = original_count - len(self.metrics[metric_name])
            deleted_count += deleted
            
            # Remove empty metric lists
            if not self.metrics[metric_name]:
                del self.metrics[metric_name]
        
        logger.info(f"Deleted {deleted_count} old metrics")
        return deleted_count


class FileStorage(MetricStorage):
    """File-based metric storage"""
    
    def __init__(self, storage_dir: Path = Path("/var/lib/machinenativeops/metrics")):
        """Initialize file storage"""
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized file storage at {self.storage_dir}")
    
    def _get_metric_file(self, metric_name: str, date: datetime = None) -> Path:
        """Get file path for a metric"""
        if date is None:
            date = datetime.utcnow()
        
        # Store metrics by date (one file per metric per day)
        date_str = date.strftime("%Y-%m-%d")
        return self.storage_dir / f"{metric_name}_{date_str}.json"
    
    def store_metric(self, metric_name: str, value: Any, timestamp: datetime = None):
        """Store a metric value to file"""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        metric_file = self._get_metric_file(metric_name, timestamp)
        
        try:
            # Load existing metrics
            if metric_file.exists():
                with open(metric_file, 'r') as f:
                    metrics = json.load(f)
            else:
                metrics = []
            
            # Append new metric
            metrics.append({
                "value": value,
                "timestamp": timestamp.isoformat()
            })
            
            # Save back to file
            with open(metric_file, 'w') as f:
                json.dump(metrics, f, indent=2)
            
            logger.debug(f"Stored metric {metric_name} to {metric_file}")
        
        except Exception as e:
            logger.error(f"Error storing metric to file: {e}")
    
    def retrieve_metrics(
        self,
        metric_name: str,
        start_time: datetime = None,
        end_time: datetime = None
    ) -> List[Dict[str, Any]]:
        """Retrieve metric values from files"""
        all_metrics = []
        
        # Determine date range
        if start_time is None:
            start_time = datetime.utcnow() - timedelta(days=7)
        if end_time is None:
            end_time = datetime.utcnow()
        
        # Read metrics from each day in range
        current_date = start_time.date()
        end_date = end_time.date()
        
        while current_date <= end_date:
            metric_file = self._get_metric_file(
                metric_name,
                datetime.combine(current_date, datetime.min.time())
            )
            
            if metric_file.exists():
                try:
                    with open(metric_file, 'r') as f:
                        daily_metrics = json.load(f)
                    
                    # Filter by time range
                    for metric in daily_metrics:
                        metric_time = datetime.fromisoformat(metric["timestamp"])
                        
                        if start_time <= metric_time <= end_time:
                            all_metrics.append(metric)
                
                except Exception as e:
                    logger.error(f"Error reading metric file {metric_file}: {e}")
            
            current_date += timedelta(days=1)
        
        return all_metrics
    
    def delete_old_metrics(self, older_than: datetime):
        """Delete metric files older than specified time"""
        deleted_count = 0
        cutoff_date = older_than.date()
        
        for metric_file in self.storage_dir.glob("*.json"):
            try:
                # Extract date from filename
                # Format: metric_name_YYYY-MM-DD.json
                date_str = metric_file.stem.split('_')[-1]
                file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                
                if file_date < cutoff_date:
                    metric_file.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted old metric file: {metric_file}")
            
            except Exception as e:
                logger.error(f"Error deleting metric file {metric_file}: {e}")
        
        logger.info(f"Deleted {deleted_count} old metric files")
        return deleted_count


def create_storage(storage_type: str = "memory", **kwargs) -> MetricStorage:
    """
    Factory function to create storage instance
    
    Args:
        storage_type: Type of storage ('memory' or 'file')
        **kwargs: Additional arguments for storage initialization
    
    Returns:
        MetricStorage instance
    """
    if storage_type == "memory":
        return MemoryStorage(**kwargs)
    elif storage_type == "file":
        return FileStorage(**kwargs)
    else:
        logger.warning(f"Unknown storage type: {storage_type}, using memory")
        return MemoryStorage()
