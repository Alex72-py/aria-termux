"""
ARIA — Autonomous Repair and Intelligence Agent
A terminal-native AI co-pilot for Termux/Android development.

Version: 1.0.0
Author: Alex72-py
License: MIT
"""

__version__ = "1.0.0"
__author__ = "Alex72-py"
__license__ = "MIT"

__all__ = ["ARIA"]


def __getattr__(name):
    if name == "ARIA":
        from .main import ARIA
        return ARIA
    raise AttributeError(name)
