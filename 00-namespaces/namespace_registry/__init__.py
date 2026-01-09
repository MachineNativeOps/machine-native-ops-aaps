"""
Namespace Registry Module

Provides centralized registry management for all namespace modules with
taxonomy-compliant naming and instant execution capabilities.

Components:
- PlatformRegistryManager: Main registry management
- PlatformRegistryValidator: Registry validation
- PlatformRegistryCache: High-performance caching

Compliance:
- Taxonomy: All names follow taxonomy standards
- INSTANT: <100ms operations, 64-256 parallel support
"""

from .registry_manager import PlatformRegistryManager
from .validator import RegistryValidator, ValidationResult, ValidationStatus
from .cache import CacheEntry, CacheLevel, MultiLayerCache
from .schema_validator import (
    SchemaValidationResult,
    SchemaValidationStatus,
    SchemaValidator,
)
from .registry_instant import NamespaceEntry, RegistryManagerInstant

__all__ = [
    'PlatformRegistryManager',
    'RegistryValidator',
    'ValidationResult',
    'ValidationStatus',
    'CacheEntry',
    'CacheLevel',
    'MultiLayerCache',
    'SchemaValidationResult',
    'SchemaValidationStatus',
    'SchemaValidator',
    'NamespaceEntry',
    'RegistryManagerInstant',
]

__version__ = '1.0.0'
