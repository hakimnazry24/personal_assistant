"""Core agent implementation using OpenAI SDK for DeepSeek."""

from openai import OpenAI
from config.settings import settings


class Agent:
    """Personal Assistant Agent powered by DeepSeek V4 Pro."""

    SYSTEM_PROMPT = """You are a helpful personal assistant. Your name is {name}.
You can help with:
- Managing schedules and calendars (Google Calendar integration)
- Sending and reading emails (Gmail integration)
- Sending messages via WhatsApp and Telegram
- General productivity tasks

Be concise, friendly, and proactive. When you cannot perform an action directly,
explain what you would need to do it and suggest alternatives.

Current capabilities: You are in CLI mode and can only chat with the user.
Integrations with external services will be added in future updates."""

    def __init__(self) -> None:
        settings.validate()

        self.client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
        )
        self.model = settings.DEEPSEEK_MODEL
        self.system_prompt = self.SYSTEM_PROMPT.format(name=settings.AGENT_NAME)

    def chat(self, user_message: str) -> str:
        """Send a message to the agent and get a response."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=settings.AGENT_MAX_TOKENS,
                temperature=settings.AGENT_TEMPERATURE,
            )

            return response.choices[0].message.content or "(no response)"

        except Exception as e:
            return f"Error communicating with DeepSeek API: {e}"

    def chat_with_history(self, messages: list[dict[str, str]]) -> str:
        """Send a conversation with history and get a response."""
        try:
            full_messages = [
                {"role": "system", "content": self.system_prompt},
                *messages,
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                max_tokens=settings.AGENT_MAX_TOKENS,
                temperature=settings.AGENT_TEMPERATURE,
            )

            return response.choices[0].message.content or "(no response)"

        except Exception as e:
            return f"Error communicating with DeepSeek API: {e}"


def test_agent() -> bool:
    """Quick test to verify the agent can communicate with DeepSeek."""
    agent = Agent()
    response = agent.chat("Hello! Please respond with just: 'I am working.'")
    print(f"Agent response: {response}")
    return "working" in response.lower() or "I am" in response
