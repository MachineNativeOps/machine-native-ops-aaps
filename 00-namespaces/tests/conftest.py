import asyncio
import inspect
import sys
from pathlib import Path

import pytest


# Ensure local packages are importable when tests are invoked from repository root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
root_str = str(PROJECT_ROOT)
if root_str not in sys.path:
    sys.path.insert(0, root_str)


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "asyncio: mark test to run with built-in asyncio event loop support",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem):
    """Minimal async test runner without external plugins."""
    test_obj = pyfuncitem.obj
    if inspect.iscoroutinefunction(test_obj):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(test_obj(**pyfuncitem.funcargs))
        finally:
            loop.close()
            asyncio.set_event_loop(None)
        return True
    return None
