"""Tests for the local repair agent."""

from types import SimpleNamespace

from aria.guardian import Guardian
from aria.knowledge_base import KnowledgeBase
from aria.repair_agent import RepairAgent


def make_agent() -> RepairAgent:
    return RepairAgent(Guardian(enabled=True), KnowledgeBase())


def test_missing_command_maps_to_termux_package():
    agent = make_agent()
    outcome = agent.attempt_auto_repair(
        hook={
            "cmd": "npm install -g yarn",
            "stderr": "bash: npm: command not found",
            "code": 127,
        }
    )

    assert outcome.matched
    assert outcome.steps[0].command[:3] == ["pkg", "install", "-y"]
    assert "nodejs" in outcome.steps[0].command


def test_missing_python_module_uses_pip_install():
    agent = make_agent()
    outcome = agent.attempt_auto_repair(
        log_error="ModuleNotFoundError: No module named 'yaml'"
    )

    assert outcome.matched
    assert outcome.steps[0].command[:4] == ["python", "-m", "pip", "install"]
    assert outcome.steps[1].command[-1] == "pyyaml"


def test_cryptography_build_gets_termux_prereqs():
    agent = make_agent()
    outcome = agent.attempt_auto_repair(
        hook={
            "cmd": "python -m pip install cryptography",
            "stderr": "error: can't find Rust compiler while building cryptography",
            "code": 1,
        }
    )

    assert outcome.matched
    first = outcome.steps[0].command
    assert first[:3] == ["pkg", "install", "-y"]
    assert "rust" in first and "openssl" in first and "libffi" in first
    assert outcome.steps[-1].command[:4] == ["python", "-m", "pip", "install"]


def test_auto_repair_executes_safe_steps(monkeypatch):
    agent = make_agent()
    calls = []

    def fake_run(command, capture_output, text, timeout):
        calls.append(command)
        return SimpleNamespace(returncode=0, stdout="done", stderr="")

    monkeypatch.setattr("aria.repair_agent.subprocess.run", fake_run)
    outcome = agent.attempt_auto_repair(
        log_error="ModuleNotFoundError: No module named 'yaml'",
        auto_apply=True
    )

    assert outcome.applied
    assert len(calls) == 2
    assert outcome.executions[0].returncode == 0
