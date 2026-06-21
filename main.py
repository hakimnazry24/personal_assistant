#!/usr/bin/env python3
"""Personal Assistant Agent - Main Entry Point.

Usage:
    python main.py          # Start interactive CLI mode
    python main.py --test   # Run a quick test to verify the agent works
"""

import sys
from agent.cli import run_cli


def main() -> None:
    args = sys.argv[1:]

    if "--test" in args:
        from agent.core import test_agent
        print("Running agent test...\n")
        success = test_agent()
        if success:
            print("\n✅ Agent is working correctly!")
        else:
            print("\n⚠️  Agent test completed but response was unexpected.")
            print("   Check your API key and network connection.")
    else:
        run_cli()


if __name__ == "__main__":
    main()
