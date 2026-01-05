"""
MachineNativeOps Auto-Monitor - Main Entry Point
自動監控主程式入口

Command-line interface for the MachineNativeOps Auto-Monitor.

Usage:
    python -m machinenativenops_auto_monitor [options]
    python -m machinenativenops_auto_monitor --config config.yaml
    python -m machinenativenops_auto_monitor serve
    
Examples:
    # Start with default configuration
    python -m machinenativenops_auto_monitor
    
Examples:
    python -m machinenativenops_auto_monitor --config config.yaml
    python -m machinenativenops_auto_monitor --daemon --verbose
    # Start with custom config file
    python -m machinenativenops_auto_monitor --config /path/to/config.yaml
    
    # Run monitoring service in daemon mode
    python -m machinenativenops_auto_monitor serve
    
    # Run collection once
    python -m machinenativenops_auto_monitor once --output results.json
"""

import argparse
import json
import logging
import signal
import sys
from pathlib import Path

from .app import AutoMonitorApp
from .config import AutoMonitorConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the auto-monitor application."""
    parser = argparse.ArgumentParser(
        description="MachineNativeOps Auto-Monitor - 自動監控系統",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start with default configuration
  python -m machinenativenops_auto_monitor
  
  # Start with custom config file
  python -m machinenativenops_auto_monitor --config /path/to/config.yaml
  
  # Start with verbose logging
  python -m machinenativenops_auto_monitor --verbose
  
  # Run in dry-run mode
  python -m machinenativenops_auto_monitor --dry-run
        """
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='/etc/machinenativeops/auto-monitor.yaml',
        help='Configuration file path (YAML)'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without actually sending alerts or storing data'
    )
    parser.add_argument(
        '--daemon',
        '-d',
        action='store_true',
        help='Run as daemon process'
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
    
    # Parse arguments
    args = parser.parse_args()
    
    # Setup logging
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Load configuration
        config_path = Path(args.config)
        if not config_path.exists():
            logger.warning(f"Configuration file not found: {config_path}, using defaults")
            config = AutoMonitorConfig()
        else:
            logger.info(f"Loading configuration from: {config_path}")
            config = AutoMonitorConfig.from_file(config_path)
        
        # Override with command-line options
        if args.dry_run:
            config.dry_run = True
            logger.info("Running in DRY-RUN mode")
        
        if args.verbose:
            config.log_level = "DEBUG"
        
        # Create and start application
        app = AutoMonitorApp(config)
        
        logger.info("Starting MachineNativeOps Auto-Monitor...")
        logger.info(f"Version: {config.version}")
        logger.info(f"Namespace: {config.namespace}")
        
def setup_logging(verbose: bool = False):
    """Configure logging for the application."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        force=True
    )


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)


def cmd_serve(args):
    """Start monitoring service in daemon mode"""
    setup_logging(args.verbose)
    
    config = load_config(args.config)
    app = AutoMonitorApp(config)
    
    print(f"🚀 Starting MachineNativeOps Auto Monitor service...")
    print(f"📊 Monitoring interval: {config.get('interval', 60)}s")
    
    try:
        if args.daemon:
            logger.info("Running in daemon mode")
            app.run_daemon()
        else:
            logger.info("Running in foreground mode")
            app.run()
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user, shutting down...")
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    except KeyboardInterrupt:
        print("\n👋 Service stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Service error: {e}", exc_info=True)
        sys.exit(1)


def cmd_once(args):
    """Run monitoring collection once"""
    setup_logging(args.verbose)
    
    config = load_config(args.config)
    app = AutoMonitorApp(config)
    
    print("🔄 Running one-time monitoring collection...")
    
    try:
        metrics = app.collect_once()
        print(f"✅ Collection complete")
        
        if args.output:
            output_path = Path(args.output)
            with open(output_path, 'w') as f:
                json.dump(metrics, f, indent=2, default=str)
            print(f"💾 Results saved to: {output_path}")
        else:
            print("📈 Metrics Summary:")
            if isinstance(metrics, dict):
                for key, value in metrics.items():
                    print(f"  {key}: {value}")
            else:
                print(f"  Collected {len(metrics)} metrics")
                
    except Exception as e:
        logger.error(f"❌ Collection error: {e}", exc_info=True)
        sys.exit(1)


def cmd_validate_config(args):
    """Validate configuration file"""
    try:
        config = load_config(args.config)
        print(f"✅ Configuration file '{args.config}' is valid")
        
        # Print key configuration values
        if isinstance(config, dict):
            if 'monitoring' in config:
                print(f"📊 Monitoring settings: {config['monitoring']}")
            if 'interval' in config:
                print(f"🔍 Monitoring interval: {config['interval']}s")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point"""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    parser = argparse.ArgumentParser(
        prog="machinenativenops-auto-monitor",
        description="MachineNativeOps Auto-Monitor - Autonomous Monitoring System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Global arguments
    parser.add_argument(
        "--config", "-c",
        default="/etc/machinenativeops/auto-monitor.yaml",
        help="Configuration file path (default: /etc/machinenativeops/auto-monitor.yaml)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start monitoring service")
    serve_parser.add_argument(
        "--daemon", "-d",
        action="store_true",
        help="Run as daemon process"
    )
    serve_parser.set_defaults(func=cmd_serve)
    
    # Once command
    once_parser = subparsers.add_parser("once", help="Run collection once")
    once_parser.add_argument(
        "--output", "-o",
        help="Output file for results (JSON format)"
    )
    once_parser.set_defaults(func=cmd_once)
    
    # Validate config command
    validate_parser = subparsers.add_parser(
        "validate-config",
        help="Validate configuration file"
    )
    validate_parser.set_defaults(func=cmd_validate_config)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # If no command specified, default to serve
    if not args.command:
        args.command = "serve"
        args.daemon = False
        args.func = cmd_serve
    
    # Execute command
    try:
        args.func(args)
    except AttributeError:
        parser.print_help()
        sys.exit(1)

        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration
    try:
        config = AutoMonitorConfig.from_file(args.config)
    except FileNotFoundError:
        logger.warning(f"Config file not found: {args.config}, using defaults")
        config = AutoMonitorConfig()
    
    # Create and run application
    app = AutoMonitorApp(config)
    
    try:
        if args.daemon:
            logger.info("Running in daemon mode...")
            # TODO: Implement daemon mode
            return
        app.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
