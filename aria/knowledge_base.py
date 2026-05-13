"""
Termux Knowledge Base for ARIA.

Contains comprehensive information about Termux, Android, and common development issues.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
import difflib

logger = logging.getLogger(__name__)


@dataclass
class KBEntry:
    """Represents a knowledge base entry."""
    pattern: str
    solution: str
    auto_fixable: bool = False
    fix_command: Optional[str] = None
    category: str = "general"


class KnowledgeBase:
    """Manages Termux knowledge base."""
    
    def __init__(self):
        """Initialize knowledge base."""
        self.entries: Dict[str, KBEntry] = {}
        self._load_entries()
    
    def _load_entries(self) -> None:
        """Load all knowledge base entries."""
        
        # Error Patterns
        error_patterns = {
            "command_not_found": KBEntry(
                pattern="command not found",
                solution="Install the required package with `pkg install <package>`. Common packages: python, git, clang, nodejs, rust, golang, ruby",
                category="errors"
            ),
            "permission_denied": KBEntry(
                pattern="permission denied",
                solution="Termux runs without root by default. Use `termux-setup-storage` for file access or `tsu` for temporary root. Some operations require `pkg install root-repo` first.",
                category="errors"
            ),
            "no_such_file": KBEntry(
                pattern="no such file or directory",
                solution="Check $PREFIX paths. Termux HOME is /data/data/com.termux/files/home. Use `echo $PREFIX` to check installation prefix. Files may be in $HOME or $PREFIX/bin",
                category="errors"
            ),
            "port_in_use": KBEntry(
                pattern="port already in use",
                solution="Termux blocks ports below 1024 for non-root. Use ports >= 1024. Check with `lsof -i :PORT` or `netstat -tuln | grep PORT`",
                category="errors"
            ),
            "gcc_error": KBEntry(
                pattern="gcc: error",
                solution="Termux uses clang instead of gcc. Install clang with `pkg install clang`. Some packages may need `pkg install build-essential`",
                auto_fixable=True,
                fix_command="pkg install clang",
                category="errors"
            ),
            "python_no_module": KBEntry(
                pattern="No module named",
                solution="Install the Python module with `pip install --user <module>` or use a virtual environment with `python -m venv venv`",
                category="errors"
            ),
            "npm_not_found": KBEntry(
                pattern="npm: command not found",
                solution="Install Node.js with `pkg install nodejs`. Configure npm prefix: `npm config set prefix $HOME/.local`",
                auto_fixable=True,
                fix_command="pkg install nodejs",
                category="errors"
            ),
            "cargo_not_found": KBEntry(
                pattern="cargo: command not found",
                solution="Install Rust with `pkg install rust`. Cargo is included with Rust.",
                auto_fixable=True,
                fix_command="pkg install rust",
                category="errors"
            ),
            "go_not_found": KBEntry(
                pattern="go: command not found",
                solution="Install Go with `pkg install golang`. Set GOPATH: `export GOPATH=$HOME/go`",
                auto_fixable=True,
                fix_command="pkg install golang",
                category="errors"
            ),
            "ruby_not_found": KBEntry(
                pattern="ruby: command not found",
                solution="Install Ruby with `pkg install ruby`. Gem is included with Ruby.",
                auto_fixable=True,
                fix_command="pkg install ruby",
                category="errors"
            ),
            "clang_error": KBEntry(
                pattern="clang: error",
                solution="Check compilation flags. Termux may need `-fPIC` for position-independent code. Try `pkg install build-essential` for common build tools.",
                category="errors"
            ),
        }
        
        # Package Management
        package_patterns = {
            "pkg_update": KBEntry(
                pattern="update packages",
                solution="Run `pkg update && pkg upgrade` to update all packages",
                category="package_management"
            ),
            "pkg_search": KBEntry(
                pattern="search package",
                solution="Use `pkg search <query>` to search for packages",
                category="package_management"
            ),
            "pkg_clean": KBEntry(
                pattern="clean packages",
                solution="Run `pkg autoclean` to remove cached package files",
                category="package_management"
            ),
            "pkg_mirror": KBEntry(
                pattern="404 not found",
                solution="Change package mirror with `termux-change-repo` if getting 404 errors",
                category="package_management"
            ),
        }
        
        # Proot-Distro
        proot_patterns = {
            "proot_install": KBEntry(
                pattern="install ubuntu",
                solution="Install Ubuntu in proot with `pkg install proot-distro` then `proot-distro install ubuntu`",
                category="proot"
            ),
            "proot_login": KBEntry(
                pattern="login ubuntu",
                solution="Login to proot Ubuntu with `proot-distro login ubuntu`",
                category="proot"
            ),
            "proot_backup": KBEntry(
                pattern="backup proot",
                solution="Backup your home directory with `tar -czf backup.tar.gz ~/`",
                category="proot"
            ),
        }
        
        # Android Bridge (Termux:API)
        android_patterns = {
            "battery": KBEntry(
                pattern="battery status",
                solution="Check battery with `termux-battery-status`. Requires Termux:API app.",
                category="android_bridge"
            ),
            "clipboard": KBEntry(
                pattern="clipboard",
                solution="Get clipboard: `termux-clipboard-get`. Set clipboard: `echo 'text' | termux-clipboard-set`",
                category="android_bridge"
            ),
            "notification": KBEntry(
                pattern="notification",
                solution="Send notification: `termux-notification --title 'Title' --content 'Message'`",
                category="android_bridge"
            ),
            "share": KBEntry(
                pattern="share file",
                solution="Share file: `termux-share <file>`",
                category="android_bridge"
            ),
            "camera": KBEntry(
                pattern="camera",
                solution="Take photo: `termux-camera-photo -c 0 output.jpg`",
                category="android_bridge"
            ),
            "tts": KBEntry(
                pattern="text to speech",
                solution="Speak text: `termux-tts-speak 'Hello World'`",
                category="android_bridge"
            ),
        }
        
        # Development Tips
        dev_patterns = {
            "python_venv": KBEntry(
                pattern="virtual environment",
                solution="Create Python venv: `python -m venv myenv`. Activate: `source myenv/bin/activate`",
                category="development"
            ),
            "git_config": KBEntry(
                pattern="git configuration",
                solution="Configure git: `git config --global user.name 'Name'` and `git config --global user.email 'email@example.com'`",
                category="development"
            ),
            "ssh_key": KBEntry(
                pattern="ssh key",
                solution="Generate SSH key: `ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519`. Add to GitHub/GitLab.",
                category="development"
            ),
            "port_forward": KBEntry(
                pattern="port forward",
                solution="Forward port: `ssh -L 8080:localhost:8080 user@host`. Or use `socat TCP-LISTEN:8080,reuseaddr,fork TCP:localhost:8080`",
                category="development"
            ),
        }
        
        # Combine all entries
        all_entries = {
            **error_patterns,
            **package_patterns,
            **proot_patterns,
            **android_patterns,
            **dev_patterns,
        }
        
        self.entries = all_entries
        logger.info(f"Loaded {len(self.entries)} knowledge base entries")
    
    def search(self, query: str, threshold: float = 0.6) -> List[KBEntry]:
        """
        Search knowledge base using fuzzy matching.
        
        Args:
            query: Search query
            threshold: Similarity threshold (0-1)
            
        Returns:
            List of matching entries
        """
        query_lower = query.lower()
        matches = []
        
        for entry in self.entries.values():
            # Check pattern match
            if query_lower in entry.pattern.lower():
                matches.append(entry)
            # Check solution match
            elif query_lower in entry.solution.lower():
                matches.append(entry)
            # Fuzzy match
            else:
                similarity = difflib.SequenceMatcher(None, query_lower, entry.pattern.lower()).ratio()
                if similarity >= threshold:
                    matches.append(entry)
        
        return matches
    
    def get_by_pattern(self, pattern: str) -> Optional[KBEntry]:
        """
        Get entry by pattern.
        
        Args:
            pattern: Pattern to search
            
        Returns:
            KBEntry or None
        """
        for entry in self.entries.values():
            if pattern.lower() in entry.pattern.lower():
                return entry
        return None
    
    def get_by_category(self, category: str) -> List[KBEntry]:
        """
        Get entries by category.
        
        Args:
            category: Category name
            
        Returns:
            List of entries in category
        """
        return [e for e in self.entries.values() if e.category == category]
    
    def list_categories(self) -> List[str]:
        """
        Get list of all categories.
        
        Returns:
            List of category names
        """
        return list(set(e.category for e in self.entries.values()))
    
    def get_all_entries(self) -> List[KBEntry]:
        """
        Get all knowledge base entries.
        
        Returns:
            List of all entries
        """
        return list(self.entries.values())
