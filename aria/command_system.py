"""
Command system for ARIA slash commands.

Handles parsing, registration, and execution of slash commands.
"""

import logging
from typing import Callable, Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Command:
    """Represents a slash command."""
    name: str
    description: str
    handler: Callable
    aliases: List[str] = None
    requires_args: bool = False


class CommandSystem:
    """Manages slash commands for ARIA."""
    
    def __init__(self):
        """Initialize command system."""
        self.commands: Dict[str, Command] = {}
        self.command_history: List[str] = []
    
    def register(
        self,
        name: str,
        handler: Callable,
        description: str = "",
        aliases: List[str] = None,
        requires_args: bool = False,
    ) -> None:
        """
        Register a new slash command.
        
        Args:
            name: Command name (without /)
            handler: Function to handle the command
            description: Command description
            aliases: Alternative command names
            requires_args: Whether command requires arguments
        """
        command = Command(
            name=name,
            handler=handler,
            description=description,
            aliases=aliases or [],
            requires_args=requires_args,
        )
        
        self.commands[name] = command
        
        # Register aliases
        for alias in (aliases or []):
            self.commands[alias] = command
        
        logger.info(f"Command registered: /{name}")
    
    def parse_command(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Parse user input into command and arguments.
        
        Args:
            user_input: Raw user input
            
        Returns:
            Dictionary with 'command' and 'args' keys, or None if invalid
        """
        user_input = user_input.strip()
        
        if not user_input.startswith("/"):
            return None
        
        # Remove leading slash
        command_str = user_input[1:].strip()
        
        # Split into command and arguments
        parts = command_str.split(None, 1)
        command_name = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if command_name not in self.commands:
            return None
        
        return {
            "command": command_name,
            "args": args,
            "raw_input": user_input,
        }
    
    def execute(self, parsed_command: Dict[str, Any], status_handler: Any = None) -> str:
        """
        Execute a parsed command.
        
        Args:
            parsed_command: Parsed command dictionary
            status_handler: Optional UI status handler for dynamic updates
            
        Returns:
            Command output
        """
        command_name = parsed_command["command"]
        args = parsed_command["args"]
        
        if command_name not in self.commands:
            return f"❌ Unknown command: /{command_name}"
        
        command = self.commands[command_name]
        
        # Check if command requires arguments
        if command.requires_args and not args:
            return f"❌ Command /{command_name} requires arguments"
        
        try:
            # Add to history
            self.command_history.append(parsed_command["raw_input"])
            
            # Execute handler (pass status_handler if provided)
            try:
                result = command.handler(args, status_handler=status_handler)
            except TypeError:
                # Fallback for handlers that don't accept status_handler
                result = command.handler(args)
                
            logger.info(f"Command executed: /{command_name}")
            return result
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return f"❌ Error executing command: {str(e)}"
    
    def get_help(self) -> str:
        """
        Get help text for all commands.
        
        Returns:
            Formatted help text
        """
        lines = ["# ARIA Commands", "", "Use `/help` anytime. Bare text is treated as `/ask`.", ""]
        seen = set()
        ordered = sorted(self.commands.values(), key=lambda c: c.name)
        for command in ordered:
            if command.name in seen:
                continue
            seen.add(command.name)
            suffix = " <args>" if command.requires_args else ""
            lines.append(f"- [bold]/{command.name}{suffix}[/bold]  {command.description}")
        lines.extend([
            "",
            "## Quick Start",
            "",
            "- [bold]/provider list[/bold]  inspect configured providers",
            "- [bold]/provider openrouter[/bold]  switch providers directly",
            "- [bold]/provider cycle[/bold]  rotate through saved providers",
            "- [bold]/model list[/bold]  browse models for the active provider",
            "- [bold]/ask <question>[/bold]  send a direct model prompt",
            "- [bold]/fix[/bold]  diagnose the latest failure",
        ])
        return "\n".join(lines)
    
    def get_command(self, name: str) -> Optional[Command]:
        """
        Get command by name or alias.
        
        Args:
            name: Command name
            
        Returns:
            Command object or None
        """
        return self.commands.get(name.lower())
    
    def list_commands(self) -> List[str]:
        """
        Get list of all command names.
        
        Returns:
            List of command names
        """
        # Return unique command names (exclude aliases)
        return list(set(cmd.name for cmd in self.commands.values()))
    
    def get_history(self, limit: int = 10) -> List[str]:
        """
        Get command history.
        
        Args:
            limit: Maximum number of history items to return
            
        Returns:
            List of recent commands
        """
        return self.command_history[-limit:]
