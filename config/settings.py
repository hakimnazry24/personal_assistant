"""Configuration loader for the Personal Assistant agent."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    # DeepSeek API
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    # Agent
    AGENT_NAME: str = os.getenv("AGENT_NAME", "PersonalAssistant")
    AGENT_MAX_TOKENS: int = int(os.getenv("AGENT_MAX_TOKENS", "4096"))
    AGENT_TEMPERATURE: float = float(os.getenv("AGENT_TEMPERATURE", "0.7"))
    AGENT_MAX_TOOL_ROUNDS: int = int(os.getenv("AGENT_MAX_TOOL_ROUNDS", "5"))

    # Google OAuth (for Calendar, Gmail — not required for mock mode)
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv(
        "GOOGLE_REDIRECT_URI", "http://localhost:3000/oauth/callback"
    )

    # MCP
    MCP_CONFIG_PATH: Path = Path(
        os.getenv("MCP_CONFIG_PATH", "mcp_servers.json")
    )

    @classmethod
    def validate(cls) -> bool:
        """Validate that the required settings are present."""
        if not cls.DEEPSEEK_API_KEY or cls.DEEPSEEK_API_KEY == "your_deepseek_api_key_here":
            raise ValueError(
                "DEEPSEEK_API_KEY is not set. Please add your API key to the .env file."
            )
        return True


settings = Settings()
