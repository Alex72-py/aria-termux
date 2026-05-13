"""
Tests for command system module.
"""

import pytest
from aria.command_system import CommandSystem, Command


def test_command_registration():
    """Test command registration."""
    cs = CommandSystem()
    
    def test_handler(args):
        return "test response"
    
    cs.register(
        name="test",
        handler=test_handler,
        description="Test command",
    )
    
    assert "test" in cs.commands
    assert cs.commands["test"].name == "test"


def test_command_parsing():
    """Test command parsing."""
    cs = CommandSystem()
    
    def test_handler(args):
        return "test response"
    
    cs.register(name="test", handler=test_handler)
    
    # Valid command
    parsed = cs.parse_command("/test hello world")
    assert parsed is not None
    assert parsed["command"] == "test"
    assert parsed["args"] == "hello world"
    
    # Invalid command
    parsed = cs.parse_command("not a command")
    assert parsed is None


def test_command_execution():
    """Test command execution."""
    cs = CommandSystem()
    
    def test_handler(args):
        return f"Response: {args}"
    
    cs.register(name="test", handler=test_handler)
    
    parsed = cs.parse_command("/test hello")
    result = cs.execute(parsed)
    
    assert "Response: hello" in result


def test_command_aliases():
    """Test command aliases."""
    cs = CommandSystem()
    
    def test_handler(args):
        return "test response"
    
    cs.register(
        name="test",
        handler=test_handler,
        aliases=["t", "tst"],
    )
    
    assert "test" in cs.commands
    assert "t" in cs.commands
    assert "tst" in cs.commands


def test_command_history():
    """Test command history."""
    cs = CommandSystem()
    
    def test_handler(args):
        return "response"
    
    cs.register(name="test", handler=test_handler)
    
    cs.execute(cs.parse_command("/test arg1"))
    cs.execute(cs.parse_command("/test arg2"))
    
    history = cs.get_history()
    assert len(history) >= 2
