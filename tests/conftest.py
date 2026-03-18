"""
Pytest configuration file for CIAF-LCM Agentic AI tests.

This file automatically sets up the Python path for all tests.
"""

import sys
from pathlib import Path
import pytest

# Add parent directory to path so ciaf_agents.* imports work
test_dir = Path(__file__).parent
project_root = test_dir.parent.parent
sys.path.insert(0, str(project_root))

# Register custom pytest markers
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "performance: mark test as a performance benchmark"
    )
