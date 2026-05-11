"""
Tests for Guardian safety layer module.
"""

import pytest
from aria.guardian import Guardian, RiskLevel


def test_guardian_initialization():
    """Test Guardian initialization."""
    guardian = Guardian(enabled=True)
    
    assert guardian.enabled is True


def test_guardian_safe_command():
    """Test analysis of safe command."""
    guardian = Guardian(enabled=True)
    
    risk_level, reason, requires_confirmation = guardian.analyze_command("echo hello")
    
    assert risk_level == RiskLevel.LOW
    assert not requires_confirmation


def test_guardian_dangerous_command():
    """Test analysis of dangerous command."""
    guardian = Guardian(enabled=True)
    
    risk_level, reason, requires_confirmation = guardian.analyze_command("rm -rf /")
    
    assert risk_level == RiskLevel.CRITICAL
    assert requires_confirmation


def test_guardian_risk_score():
    """Test risk score calculation."""
    guardian = Guardian(enabled=True)
    
    low_score = guardian.calculate_risk_score("echo hello")
    high_score = guardian.calculate_risk_score("rm -rf /")
    
    assert low_score < high_score
    assert low_score == 0
    assert high_score == 100


def test_guardian_disabled():
    """Test Guardian when disabled."""
    guardian = Guardian(enabled=False)
    
    risk_level, reason, requires_confirmation = guardian.analyze_command("rm -rf /")
    
    assert risk_level == RiskLevel.LOW
    assert not requires_confirmation


def test_guardian_toggle():
    """Test Guardian toggle."""
    guardian = Guardian(enabled=True)
    
    assert guardian.enabled is True
    guardian.toggle()
    assert guardian.enabled is False
    guardian.toggle()
    assert guardian.enabled is True


def test_guardian_risk_emoji():
    """Test risk emoji generation."""
    guardian = Guardian()
    
    assert guardian.get_risk_emoji(RiskLevel.LOW) == "✅"
    assert guardian.get_risk_emoji(RiskLevel.MEDIUM) == "⚠️"
    assert guardian.get_risk_emoji(RiskLevel.HIGH) == "🚨"
    assert guardian.get_risk_emoji(RiskLevel.CRITICAL) == "🔴"
