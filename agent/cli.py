"""CLI interface for the Personal Assistant agent."""

import sys
from agent.core import Agent


def run_cli() -> None:
    """Run the interactive CLI loop."""
    print("=" * 50)
    print("  🤖  Personal Assistant Agent")
    print("  Powered by DeepSeek V4 Pro")
    print("=" * 50)
    print()
    print("Type your message and press Enter to chat.")
    print("Commands:")
    print("  /exit  - Exit the assistant")
    print("  /clear - Clear conversation history")
    print("  /help  - Show this help message")
    print()

    try:
        agent = Agent()
        print("✅ Agent initialized successfully.\n")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("Please set your DEEPSEEK_API_KEY in the .env file.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        sys.exit(1)

    messages: list[dict[str, str]] = []

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye! 👋")
            break

        if not user_input:
            continue

        # Handle commands
        if user_input.startswith("/"):
            command = user_input.lower()
            if command == "/exit":
                print("Goodbye! 👋")
                break
            elif command == "/clear":
                messages.clear()
                print("🔄 Conversation history cleared.\n")
                continue
            elif command == "/help":
                print("\nCommands:")
                print("  /exit  - Exit the assistant")
                print("  /clear - Clear conversation history")
                print("  /help  - Show this help message\n")
                continue
            else:
                print(f"Unknown command: {user_input}")
                print("Type /help for available commands.\n")
                continue

        # Send message to agent
        messages.append({"role": "user", "content": user_input})
        print("Assistant: ", end="", flush=True)

        response = agent.chat_with_history(messages)
        print(response)
        print()

        messages.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    run_cli()
