#!/usr/bin/env python3
"""
Standalone ARIA runner - No package installation required!

Run this directly with: python3 run_aria.py
"""

import sys
from pathlib import Path

# Add the project root to Python path so imports work
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now import ARIA
from aria.main import ARIA


def main():
    """Main entry point."""
    try:
        aria = ARIA()
        aria.run()
    except KeyboardInterrupt:
        print("\n\nGoodbye.")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
