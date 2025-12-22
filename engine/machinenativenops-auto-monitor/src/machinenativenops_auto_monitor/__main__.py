#!/usr/bin/env python3
"""
Auto-Monitor Main Entry Point
自動監控主程式入口

Command-line interface for the MachineNativeOps Auto-Monitor.
"""

import argparse
import logging
import sys
from pathlib import Path

from .app import AutoMonitorApp
from .config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="MachineNativeOps Auto-Monitor"
    )
    parser.add_argument(
        "--config",
        default="config/auto-monitor.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--mode",
        choices=["collect", "alert", "monitor"],
        default="monitor",
        help="Operation mode"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Collection interval in seconds"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run as daemon"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    try:
        # Load configuration
        config_path = Path(args.config)
        if config_path.exists():
            config = load_config(config_path)
        else:
            logger.warning(f"Config file {config_path} not found, using defaults")
            config = load_config()
        
        # Create and run app
        app = AutoMonitorApp(config)
        
        if args.mode == "collect":
            logger.info("Running in collect-only mode")
            app.collect_once()
        elif args.mode == "alert":
            logger.info("Running in alert-only mode")
            app.check_alerts_once()
        else:
            logger.info(f"Starting auto-monitor (interval: {args.interval}s)")
            app.run(interval=args.interval, daemon=args.daemon)
    
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
