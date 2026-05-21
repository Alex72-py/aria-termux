"""
ARIA — Autonomous Repair and Intelligence Agent
A terminal-native AI co-pilot for Termux/Android development.

Version: 1.0.0
Author: ARIA Development Team
License: MIT
"""

__version__ = "1.0.0"
__author__ = "ARIA Development Team"
__license__ = "MIT"

__all__ = ["ARIA"]


def __getattr__(name):
    if name == "ARIA":
        from .main import ARIA
        return ARIA
    raise AttributeError(name)
