"""
Guardian safety layer for ARIA.

Analyzes commands for risk and prompts user confirmation for dangerous operations.
"""

import logging
import re
from typing import Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk levels for operations."""
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


class Guardian:
    """Safety layer for ARIA."""
    
    # Dangerous patterns
    DANGEROUS_PATTERNS = {
        r"rm\s+-rf": (RiskLevel.CRITICAL, "Recursive deletion"),
        r"rm\s+/": (RiskLevel.CRITICAL, "Root directory deletion"),
        r":\(\)\s*{": (RiskLevel.CRITICAL, "Fork bomb"),
        r"dd\s+if=": (RiskLevel.CRITICAL, "Disk write operation"),
        r"mkfs": (RiskLevel.CRITICAL, "Filesystem format"),
        r"chmod\s+777": (RiskLevel.HIGH, "Unrestricted permissions"),
        r"sudo": (RiskLevel.HIGH, "Sudo command"),
        r"su\s+": (RiskLevel.HIGH, "Switch user"),
        r"tsu": (RiskLevel.HIGH, "Termux sudo"),
        r"chown": (RiskLevel.HIGH, "Change ownership"),
        r"passwd": (RiskLevel.HIGH, "Password modification"),
        r"userdel": (RiskLevel.HIGH, "User deletion"),
        r"iptables": (RiskLevel.MEDIUM, "Firewall modification"),
        r"curl\s+\|\s+sh": (RiskLevel.MEDIUM, "Pipe to shell"),
        r"wget\s+\|\s+sh": (RiskLevel.MEDIUM, "Pipe to shell"),
        r"eval": (RiskLevel.MEDIUM, "Code evaluation"),
        r"exec": (RiskLevel.MEDIUM, "Process replacement"),
    }
    
    # Safe patterns (whitelist)
    SAFE_PATTERNS = {
        r"echo",
        r"ls",
        r"pwd",
        r"cd",
        r"cat",
        r"grep",
        r"find",
        r"which",
        r"man",
        r"help",
        r"pkg\s+search",
        r"pkg\s+list",
        r"pkg\s+show",
    }
    
    def __init__(self, enabled: bool = True):
        """
        Initialize Guardian.
        
        Args:
            enabled: Whether Guardian is enabled
        """
        self.enabled = enabled
        logger.info(f"Guardian initialized (enabled={enabled})")
    
    def analyze_command(self, command: str) -> Tuple[RiskLevel, str, bool]:
        """
        Analyze command for risk.
        
        Args:
            command: Command to analyze
            
        Returns:
            Tuple of (risk_level, reason, requires_confirmation)
        """
        if not self.enabled:
            return RiskLevel.LOW, "Guardian disabled", False
        
        command_lower = command.lower()
        
        # Check safe patterns first
        for pattern in self.SAFE_PATTERNS:
            if re.search(pattern, command_lower):
                return RiskLevel.LOW, "Safe command", False
        
        # Check dangerous patterns
        max_risk = RiskLevel.LOW
        reason = "Unknown command"
        
        for pattern, (risk_level, description) in self.DANGEROUS_PATTERNS.items():
            if re.search(pattern, command_lower):
                if risk_level.value > max_risk.value:
                    max_risk = risk_level
                    reason = description
        
        # Determine if confirmation is required
        requires_confirmation = max_risk.value >= RiskLevel.MEDIUM.value
        
        return max_risk, reason, requires_confirmation
    
    def calculate_risk_score(self, command: str) -> int:
        """
        Calculate risk score (0-100).
        
        Args:
            command: Command to analyze
            
        Returns:
            Risk score
        """
        risk_level, _, _ = self.analyze_command(command)
        
        risk_scores = {
            RiskLevel.LOW: 0,
            RiskLevel.MEDIUM: 40,
            RiskLevel.HIGH: 70,
            RiskLevel.CRITICAL: 100,
        }
        
        return risk_scores.get(risk_level, 0)
    
    def get_risk_emoji(self, risk_level: RiskLevel) -> str:
        """
        Get emoji for risk level.
        
        Args:
            risk_level: Risk level
            
        Returns:
            Emoji string
        """
        emojis = {
            RiskLevel.LOW: "✅",
            RiskLevel.MEDIUM: "⚠️",
            RiskLevel.HIGH: "🚨",
            RiskLevel.CRITICAL: "🔴",
        }
        return emojis.get(risk_level, "❓")
    
    def get_risk_color(self, risk_level: RiskLevel) -> str:
        """
        Get color for risk level.
        
        Args:
            risk_level: Risk level
            
        Returns:
            Rich color name
        """
        colors = {
            RiskLevel.LOW: "green",
            RiskLevel.MEDIUM: "yellow",
            RiskLevel.HIGH: "red",
            RiskLevel.CRITICAL: "dark_red",
        }
        return colors.get(risk_level, "white")
    
    def format_analysis(self, command: str) -> str:
        """
        Format risk analysis for display.
        
        Args:
            command: Command to analyze
            
        Returns:
            Formatted analysis string
        """
        risk_level, reason, requires_confirmation = self.analyze_command(command)
        score = self.calculate_risk_score(command)
        risk_tag = risk_level.name
        
        lines = [
            f"[{risk_tag}] Risk Analysis",
            f"Command: {command}",
            f"Risk Level: {risk_level.name}",
            f"Risk Score: {score}/100",
            f"Reason: {reason}",
        ]
        
        if requires_confirmation:
            lines.append("WARNING: Confirmation required before execution")
        
        return "\n".join(lines)
    
    def should_prompt(self, command: str) -> bool:
        """
        Check if user should be prompted for confirmation.
        
        Args:
            command: Command to check
            
        Returns:
            True if confirmation should be requested
        """
        _, _, requires_confirmation = self.analyze_command(command)
        return requires_confirmation and self.enabled
    
    def enable(self) -> None:
        """Enable Guardian."""
        self.enabled = True
        logger.info("Guardian enabled")
    
    def disable(self) -> None:
        """Disable Guardian."""
        self.enabled = False
        logger.warning("Guardian disabled")
    
    def toggle(self) -> bool:
        """
        Toggle Guardian state.
        
        Returns:
            New enabled state
        """
        self.enabled = not self.enabled
        logger.info(f"Guardian toggled (enabled={self.enabled})")
        return self.enabled
