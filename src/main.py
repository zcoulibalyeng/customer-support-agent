"""
CLI entry point for the customer support agent.

Usage:
    python -m src.main                    # Interactive chat
    python -m src.main --message "..."    # Single message mode
"""

import argparse
from src.workflow.runner import run_interactive, send_message, create_session


def main():
    parser = argparse.ArgumentParser(description="TechGear Customer Support Agent")
    parser.add_argument("--message", "-m", type=str, help="Send a single message instead of interactive mode")
    parser.add_argument("--email", "-e", type=str, help="Customer email for identification")
    args = parser.parse_args()

    if args.message:
        thread_id = create_session()
        response = send_message(args.message, thread_id, args.email)
        print(f"\n{response}")
    else:
        run_interactive()


if __name__ == "__main__":
    main()
