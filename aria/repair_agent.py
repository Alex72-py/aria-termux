"""Bounded local repair agent for fast Termux auto-fixes."""

from __future__ import annotations

import re
import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from .guardian import Guardian
from .knowledge_base import KnowledgeBase


@dataclass
class RepairStep:
    command: List[str]
    reason: str
    source: str = "local"
    auto_run: bool = True

    @property
    def display_command(self) -> str:
        return shlex.join(self.command)


@dataclass
class RepairExecution:
    command: str
    reason: str
    returncode: int
    output: str


@dataclass
class RepairOutcome:
    matched: bool = False
    applied: bool = False
    used_api: bool = False
    requires_model: bool = False
    summary: str = ""
    steps: List[RepairStep] = field(default_factory=list)
    executions: List[RepairExecution] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def render(self) -> str:
        lines: List[str] = []
        if self.summary:
            lines.append(self.summary)
        if self.steps:
            lines.append("")
            lines.append("Planned steps:")
            for step in self.steps:
                lines.append(f"- `{step.display_command}`  {step.reason}")
        if self.executions:
            lines.append("")
            lines.append("Executed:")
            for item in self.executions:
                status = "ok" if item.returncode == 0 else f"exit {item.returncode}"
                lines.append(f"- `{item.command}`  {status}  {item.reason}")
                if item.output:
                    lines.append("```text")
                    lines.append(item.output[:600].rstrip())
                    lines.append("```")
        if self.notes:
            lines.append("")
            lines.append("Notes:")
            for note in self.notes:
                lines.append(f"- {note}")
        return "\n".join(lines).strip()


class RepairAgent:
    """Local-first repair planner/executor for common Termux failures."""

    COMMAND_PACKAGE_MAP = {
        "gcc": "clang",
        "g++": "clang",
        "cc": "clang",
        "clang": "clang",
        "make": "make",
        "cmake": "cmake",
        "cargo": "rust",
        "rustc": "rust",
        "go": "golang",
        "npm": "nodejs",
        "node": "nodejs",
        "ruby": "ruby",
        "gem": "ruby",
        "git": "git",
        "python": "python",
        "python3": "python",
        "pip": "python",
        "pip3": "python",
        "pkg-config": "pkg-config",
        "curl": "curl",
        "wget": "wget",
    }

    PYTHON_MODULE_PACKAGE_MAP = {
        "yaml": "pyyaml",
        "pil": "pillow",
        "cv2": "opencv-python",
        "sklearn": "scikit-learn",
        "crypto": "pycryptodome",
        "openssl": "pyopenssl",
    }

    TERMUX_BUILD_PREREQS = ["clang", "make", "pkg-config"]
    RUST_BUILD_PREREQS = ["rust", "clang", "make", "pkg-config"]
    CRYPTOGRAPHY_PREREQS = ["rust", "clang", "openssl", "libffi", "pkg-config", "make"]
    TORCH_PREREQS = ["python", "clang", "cmake", "make", "pkg-config"]

    def __init__(self, guardian: Guardian, kb: KnowledgeBase):
        self.guardian = guardian
        self.kb = kb

    def plan_install(self, package_name: str) -> RepairOutcome:
        """Plan a complex installation with Termux-specific prerequisites."""
        pkg = package_name.lower().strip()
        outcome = RepairOutcome(matched=True, summary=f"Planning install for `{pkg}`")
        steps: List[RepairStep] = []
        notes: List[str] = []

        if pkg == "rust":
            steps.append(self._pkg_install_step(["rust"], "install Rust toolchain"))
            outcome.summary = "Planned Rust installation."
        
        elif pkg == "cryptography":
            steps.append(self._pkg_install_step(self.CRYPTOGRAPHY_PREREQS, "install native build prerequisites for cryptography"))
            steps.append(self._pip_upgrade_step())
            steps.append(self._pip_install_step("cryptography", "install cryptography"))
            outcome.summary = "Planned cryptography installation with all native prerequisites."

        elif pkg == "torch":
            steps.append(self._pkg_install_step(self.TORCH_PREREQS, "install native build prerequisites for torch"))
            steps.append(self._pip_upgrade_step())
            # For torch on Termux, we often need a specific wheel. 
            # We'll try to use a common community wheel or just the name if no specific one is known.
            torch_url = "https://github.com/its-pointless/its-pointless.github.io/raw/master/python311/torch-2.0.0-cp311-cp311-linux_aarch64.whl"
            notes.append("Using a community-maintained torch wheel for Termux (aarch64).")
            steps.append(self._pip_install_step(torch_url, "install torch from community wheel"))
            outcome.summary = "Planned torch installation using community CPU wheels."

        elif pkg == "numpy":
            steps.append(self._pkg_install_step(["clang", "python", "fftw", "libflame", "liblapack"], "install numpy build dependencies"))
            steps.append(self._pip_install_step("numpy", "install numpy"))
            outcome.summary = "Planned numpy installation with BLAS/LAPACK support."

        else:
            # Generic package
            if pkg in self.COMMAND_PACKAGE_MAP.values():
                 steps.append(self._pkg_install_step([pkg], f"install `{pkg}` via pkg"))
            else:
                 steps.append(self._pip_install_step(pkg, f"install `{pkg}` via pip"))
            outcome.summary = f"Planned installation for `{pkg}`."

        outcome.steps = steps
        outcome.notes = notes
        return outcome

    def execute_plan(self, plan: RepairOutcome) -> RepairOutcome:
        """Execute a planned outcome."""
        for step in plan.steps:
            execution = self._run_step(step)
            plan.executions.append(execution)
            if execution.returncode != 0:
                plan.notes.append(f"Execution failed at step: {step.display_command}")
                plan.applied = False
                return plan
        
        plan.applied = True
        return plan

    def plan_from_ai_text(self, text: str) -> RepairOutcome:
        """Parse AI response text for bash blocks and convert them into a RepairOutcome."""
        import re
        import shlex
        
        outcome = RepairOutcome(matched=False, summary="AI-generated plan")
        # Extract bash/sh/shell blocks
        blocks = re.findall(r"```(?:bash|sh|shell)?\n(.*?)```", text, re.DOTALL)
        if not blocks:
            return outcome
            
        steps: List[RepairStep] = []
        for block in blocks:
            # Each non-empty, non-comment line is a step
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            for line in lines:
                if line.startswith("#"):
                    continue
                try:
                    cmd_list = shlex.split(line)
                    if cmd_list:
                        steps.append(RepairStep(
                            command=cmd_list,
                            reason="AI suggested step",
                            auto_run=True
                        ))
                except Exception:
                    # If shlex fails (e.g. unclosed quotes), treat as a single string shell command
                    steps.append(RepairStep(
                        command=[line],
                        reason="AI suggested step (complex)",
                        auto_run=True
                    ))
        
        if steps:
            outcome.matched = True
            outcome.steps = steps
            outcome.summary = f"Plan extracted: {len(steps)} AI-suggested steps."
        
        return outcome

    def attempt_auto_repair(
        self,
        *,
        hook: Optional[dict] = None,
        log_error: str = "",
        user_note: str = "",
        auto_apply: bool = False,
    ) -> RepairOutcome:
        context, failed_command = self._build_context(
            hook=hook,
            log_error=log_error,
            user_note=user_note,
        )
        plan = self._build_plan(context=context, failed_command=failed_command)
        if not plan.steps:
            return plan

        plan.matched = True
        
        if not auto_apply:
            plan.notes.append("Auto-apply is disabled. Plan generated but not executed.")
            return plan

        runnable = [step for step in plan.steps if step.auto_run and self._is_safe_to_run(step.command)]
        blocked = [step for step in plan.steps if step.auto_run and not self._is_safe_to_run(step.command)]

        if blocked:
            plan.notes.append("Some planned commands were withheld because they were not in the safe local auto-run set.")

        for step in runnable[:4]:
            execution = self._run_step(step)
            plan.executions.append(execution)
            if execution.returncode != 0:
                plan.notes.append("Local auto-repair stopped after the first failing step.")
                plan.applied = False
                return plan

        plan.applied = bool(runnable)
        if plan.applied:
            plan.notes.append("Local repair path was used; no model request was sent.")
        else:
            plan.notes.append("A local plan was found, but nothing met the auto-run safety policy.")
        return plan

    def _build_context(self, *, hook: Optional[dict], log_error: str, user_note: str) -> Tuple[str, str]:
        parts: List[str] = []
        failed_command = ""
        if hook:
            failed_command = str(hook.get("cmd") or "").strip()
            if failed_command:
                parts.append(f"Failed command: {failed_command}")
            if hook.get("stderr"):
                parts.append(str(hook.get("stderr")))
            if hook.get("code") not in (None, ""):
                parts.append(f"Exit code: {hook.get('code')}")
        if log_error:
            parts.append(log_error)
        if user_note:
            parts.append(user_note)
        return "\n".join(parts), failed_command

    def _build_plan(self, *, context: str, failed_command: str) -> RepairOutcome:
        ctx = context.lower()
        outcome = RepairOutcome(matched=False, summary="No confident local repair plan was found.")

        if not context.strip():
            outcome.notes.append("No failure context was available for local auto-repair.")
            return outcome

        steps: List[RepairStep] = []
        notes: List[str] = []

        missing_cmd = self._detect_missing_command(context, failed_command)
        if missing_cmd:
            pkg = self.COMMAND_PACKAGE_MAP.get(missing_cmd.lower())
            if pkg:
                steps.append(self._pkg_install_step([pkg], f"install missing command `{missing_cmd}`"))
                rerun = self._rerun_failed_command_step(
                    failed_command,
                    f"retry `{failed_command}` after installing `{pkg}`",
                )
                if rerun:
                    steps.append(rerun)
                return self._finalize_plan(
                    "Detected a missing Termux command and prepared a local repair.",
                    steps,
                    notes,
                )

        module_name = self._detect_missing_python_module(context)
        if module_name:
            pip_name = self.PYTHON_MODULE_PACKAGE_MAP.get(module_name.lower(), module_name)
            steps.append(self._pip_upgrade_step())
            steps.append(self._pip_install_step(pip_name, f"install missing Python module `{module_name}`"))
            return self._finalize_plan(
                f"Detected a missing Python module: `{module_name}`.",
                steps,
                notes,
            )

        if "cryptography" in ctx:
            steps.append(self._pkg_install_step(self.CRYPTOGRAPHY_PREREQS, "install native build prerequisites for cryptography"))
            steps.append(self._pip_upgrade_step())
            rerun = self._rerun_or_default_pip_step(failed_command, "cryptography")
            if rerun:
                steps.append(rerun)
            return self._finalize_plan("Detected a cryptography install/build failure.", steps, notes)

        if "torch" in ctx:
            steps.append(self._pkg_install_step(self.TORCH_PREREQS, "install common Termux prerequisites for torch builds"))
            steps.append(self._pip_upgrade_step())
            rerun = self._rerun_or_default_pip_step(failed_command, "torch")
            if rerun:
                steps.append(rerun)
            notes.append("Torch on Termux can still depend on upstream wheel availability for your Python and CPU combination.")
            return self._finalize_plan("Detected a torch install/build failure.", steps, notes)

        if self._needs_rust_toolchain(ctx):
            steps.append(self._pkg_install_step(self.RUST_BUILD_PREREQS, "install Rust-based build prerequisites"))
            rerun = self._rerun_if_safe(failed_command, "retry the original build/install command")
            if rerun:
                steps.append(rerun)
            return self._finalize_plan("Detected a Rust toolchain build failure.", steps, notes)

        if self._needs_c_toolchain(ctx):
            steps.append(self._pkg_install_step(self.TERMUX_BUILD_PREREQS, "install C/C++ build prerequisites"))
            rerun = self._rerun_if_safe(failed_command, "retry the original build/install command")
            if rerun:
                steps.append(rerun)
            return self._finalize_plan("Detected a native build failure.", steps, notes)

        kb_matches = self.kb.search(context, threshold=0.75)
        for entry in kb_matches:
            if entry.auto_fixable and entry.fix_command:
                cmd = self._split_command(entry.fix_command)
                if cmd:
                    steps.append(RepairStep(command=cmd, reason=f"offline KB match: {entry.pattern}"))
                    return self._finalize_plan(f"Matched offline KB entry: `{entry.pattern}`.", steps, notes)

        return outcome

    def _finalize_plan(self, summary: str, steps: List[RepairStep], notes: List[str]) -> RepairOutcome:
        deduped: List[RepairStep] = []
        seen = set()
        for step in steps:
            key = tuple(step.command)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(step)
        return RepairOutcome(matched=True, summary=summary, steps=deduped, notes=notes)

    def _detect_missing_command(self, context: str, failed_command: str) -> Optional[str]:
        patterns = [
            r"(?:bash|sh|zsh)?:?\s*([a-zA-Z0-9+_.-]+): command not found",
            r"command not found:?\s*([a-zA-Z0-9+_.-]+)",
        ]
        for pat in patterns:
            match = re.search(pat, context, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _detect_missing_python_module(self, context: str) -> Optional[str]:
        patterns = [
            r"No module named ['\"]([^'\"]+)['\"]",
            r"ModuleNotFoundError: No module named ['\"]([^'\"]+)['\"]",
        ]
        for pat in patterns:
            match = re.search(pat, context)
            if match:
                return match.group(1).split(".")[0]
        return None

    def _needs_rust_toolchain(self, ctx: str) -> bool:
        needles = [
            "cargo: command not found",
            "rustc: command not found",
            "can't find rust compiler",
            "requires rust",
            "maturin",
            "pyo3",
        ]
        return any(needle in ctx for needle in needles)

    def _needs_c_toolchain(self, ctx: str) -> bool:
        needles = [
            "gcc: error",
            "clang: error",
            "failed building wheel",
            "unable to execute 'gcc'",
            "command 'clang' failed",
            "fatal error:",
        ]
        return any(needle in ctx for needle in needles)

    def _pkg_install_step(self, packages: List[str], reason: str) -> RepairStep:
        unique: List[str] = []
        for item in packages:
            if item not in unique:
                unique.append(item)
        return RepairStep(command=["pkg", "install", "-y", *unique], reason=reason)

    def _pip_upgrade_step(self) -> RepairStep:
        return RepairStep(
            command=["python", "-m", "pip", "install", "--break-system-packages", "--upgrade", "pip", "setuptools", "wheel"],
            reason="refresh pip build tooling",
        )

    def _pip_install_step(self, package: str, reason: str) -> RepairStep:
        return RepairStep(
            command=["python", "-m", "pip", "install", "--break-system-packages", "--prefer-binary", package],
            reason=reason,
        )

    def _rerun_or_default_pip_step(self, failed_command: str, package: str) -> Optional[RepairStep]:
        rerun = self._rerun_if_safe(failed_command, "retry the original install command")
        if rerun:
            return rerun
        return self._pip_install_step(package, f"install `{package}` with pip after preparing prerequisites")

    def _rerun_failed_command_step(self, failed_command: str, reason: str) -> Optional[RepairStep]:
        return self._rerun_if_safe(failed_command, reason)

    def _rerun_if_safe(self, failed_command: str, reason: str) -> Optional[RepairStep]:
        cmd = self._split_command(failed_command)
        if not cmd:
            return None
        if not self._is_safe_to_run(cmd):
            return RepairStep(command=cmd, reason=reason, auto_run=False)
        return RepairStep(command=cmd, reason=reason)

    def _split_command(self, command: str) -> Optional[List[str]]:
        if not command.strip():
            return None
        if re.search(r"[|;&><`$]", command):
            return None
        try:
            return shlex.split(command)
        except ValueError:
            return None

    def _is_safe_to_run(self, command: List[str]) -> bool:
        if not command:
            return False
        display = shlex.join(command)
        _, _, requires_confirmation = self.guardian.analyze_command(display)
        if requires_confirmation:
            return False
        safe_prefixes = [
            ["pkg", "install"],
            ["python", "-m", "pip", "install", "--break-system-packages"],
            ["python", "-m", "pip", "install"],
            ["pip", "install"],
            ["pip3", "install"],
        ]
        for prefix in safe_prefixes:
            if command[: len(prefix)] == prefix:
                return True
        return False

    def _run_step(self, step: RepairStep) -> RepairExecution:
        result = subprocess.run(
            step.command,
            capture_output=True,
            text=True,
            timeout=900,
        )
        output = (result.stdout or "") + (("\n" + result.stderr) if result.stderr else "")
        return RepairExecution(
            command=step.display_command,
            reason=step.reason,
            returncode=result.returncode,
            output=output.strip(),
        )
