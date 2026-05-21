"""
Tests for ARIA Watch Mode.
"""

import unittest
import json
import os
import time
from pathlib import Path
from unittest.mock import MagicMock
from aria.watch_mode import WatchMode
from aria.knowledge_base import KnowledgeBase

class TestWatchMode(unittest.TestCase):
    def setUp(self):
        self.kb = MagicMock(spec=KnowledgeBase)
        self.wm = WatchMode(self.kb)
        self.aria_dir = Path.home() / ".aria"
        self.aria_dir.mkdir(parents=True, exist_ok=True)
        self.hook_file = self.aria_dir / "last_fail.json"
        self.watch_log = self.aria_dir / "watch.log"

    def tearDown(self):
        self.wm.disable()
        if self.hook_file.exists():
            self.hook_file.unlink()
        if self.watch_log.exists():
            self.watch_log.unlink()

    def test_enable_disable(self):
        self.wm.enable()
        self.assertTrue(self.wm.enabled)
        self.assertIsNotNone(self.wm._thread)
        self.assertTrue(self.wm._thread.is_alive())
        
        self.wm.disable()
        self.assertFalse(self.wm.enabled)
        self.assertIsNone(self.wm._thread)

    def test_detect_shell_failure(self):
        self.wm.enable()
        
        # Simulate a shell failure
        failure_data = {
            "cmd": "ls non_existent_file",
            "code": 2,
            "cwd": "/root",
            "ts": "2026-05-13T12:00:00"
        }
        self.hook_file.write_text(json.dumps(failure_data))
        
        # Give the thread time to poll
        time.sleep(3.0)
        
        # Check if it detected it
        with self.wm._lock:
            self.assertIsNotNone(self.wm._pending_failure)
            self.assertEqual(self.wm._pending_failure["cmd"], "ls non_existent_file")
            self.assertEqual(self.wm._pending_failure["type"], "shell_hook")

    def test_detect_log_error(self):
        self.wm.enable()
        
        # Simulate a log error
        error_msg = "Traceback (most recent call last):\n  File \"test.py\", line 1\n    import non_existent_module\nModuleNotFoundError: No module named 'non_existent_module'\n"
        with open(self.watch_log, "a") as f:
            f.write(error_msg)
        
        # Give the thread time to poll
        time.sleep(3.0)
        
        # Check if it detected it
        with self.wm._lock:
            self.assertIsNotNone(self.wm._pending_failure)
            self.assertEqual(self.wm._pending_failure["type"], "log_watch")
            self.assertIn("Python Exception", self.wm._pending_failure["description"])

    def test_check_and_notify_clears_pending(self):
        self.wm.enable()
        with self.wm._lock:
            self.wm._pending_failure = {"type": "shell_hook", "cmd": "test", "code": 1, "cwd": ".", "stderr": ""}
        
        # Mocking _show_shell_notification to avoid UI issues in tests
        self.wm._show_shell_notification = MagicMock()
        
        result = self.wm.check_and_notify()
        self.assertTrue(result)
        self.assertIsNone(self.wm._pending_failure)
        self.wm._show_shell_notification.assert_called_once()

if __name__ == "__main__":
    unittest.main()
