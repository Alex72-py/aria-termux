"""
Utility functions for ARIA.
"""

import os
import subprocess
from typing import Tuple, Optional


def is_termux() -> bool:
    """
    Check if running in Termux environment.
    
    Returns:
        True if running in Termux, False otherwise
    """
    return os.path.exists("/data/data/com.termux")


def get_termux_prefix() -> Optional[str]:
    """
    Get Termux installation prefix.
    
    Returns:
        Prefix path or None
    """
    if not is_termux():
        return None
    
    try:
        result = subprocess.run(
            ["echo", "$PREFIX"],
            shell=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return None


def get_termux_home() -> Optional[str]:
    """
    Get Termux home directory.
    
    Returns:
        Home path or None
    """
    if not is_termux():
        return None
    
    return os.path.expanduser("~")


def run_command(command: str, timeout: int = 30) -> Tuple[bool, str]:
    """
    Run shell command and return output.
    
    Args:
        command: Command to run
        timeout: Timeout in seconds
        
    Returns:
        Tuple of (success, output)
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        
        output = result.stdout or result.stderr
        success = result.returncode == 0
        
        return success, output
    except subprocess.TimeoutExpired:
        return False, "Command timeout"
    except Exception as e:
        return False, str(e)


def format_code_block(code: str, language: str = "python") -> str:
    """
    Format code block for display.
    
    Args:
        code: Code to format
        language: Programming language
        
    Returns:
        Formatted code block
    """
    return f"```{language}\n{code}\n```"


def truncate_string(text: str, max_length: int = 100) -> str:
    """
    Truncate string to max length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."
