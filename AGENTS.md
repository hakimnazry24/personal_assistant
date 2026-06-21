# AGENTS.md — AI Assistant Context for Personal Assistant Agent

> This file is read by the AI coding assistant at the start of every session. It provides everything needed to understand this project quickly and make informed changes.

---

## 1. Project Identity

**Name:** Personal Assistant Agent  
**Language:** Python 3.14  
**Model:** DeepSeek V4 Pro (`deepseek-chat`) via OpenAI-compatible SDK  
**Current Phase:** Scaffold — CLI-only chat, no external integrations yet  
**Goal:** A personal assistant agent that will eventually integrate with Google Calendar, Gmail, WhatsApp, Telegram, and other productivity apps.

---

## 2. Repository Layout

```
personal_assistant/
├── .env                          # API key + config (gitignored)
├── .env.example                  # Template for .env (committed)
├── .gitignore
├── requirements.txt              # openai, python-dotenv
├── main.py                       # CLI entry point (python main.py | python main.py --test)
├── AGENTS.md                     # This file
├── README.md                     # Human-facing docs
├── config/
│   ├── __init__.py
│   └── settings.py               # Loads .env via python-dotenv; Settings dataclass
└── agent/
    ├── __init__.py
    ├── core.py                    # Agent class — wraps OpenAI client pointed at DeepSeek
    ├── cli.py                     # Interactive CLI with /exit, /clear, /help commands
    └── tools/
        ├── __init__.py
        ├── base.py                # BaseTool (ABC) + ToolResult (dataclass)
        ├── calendar.py            # CalendarTool — stub
        ├── email.py               # EmailTool — stub
        └── messaging.py           # WhatsAppTool + TelegramTool — stubs
```

---

## 3. Architecture

### 3.1 Core Flow

```
User (CLI stdin) → cli.py → Agent.chat_with_history() → OpenAI SDK → DeepSeek API → Response → stdout
```

- `cli.py` manages the read-eval-print loop and conversation history (list of `{role, content}` dicts).
- `Agent` (in `core.py`) wraps the OpenAI SDK, prepends the system prompt, and calls `client.chat.completions.create()`.
- `config/settings.py` loads all configuration from `.env` via `python-dotenv`. It validates that `DEEPSEEK_API_KEY` is set on `Agent.__init__`.

### 3.2 Tool System (Planned)

All tools extend `BaseTool` (ABC) and return `ToolResult` dataclasses:
```python
@dataclass
class ToolResult:
    success: bool
    message: str
    data: dict
```

Current tools are **stubs only** — they return `success=False` with a "not yet implemented" message. The tool framework is designed but not wired into the agent's chat loop yet.

### 3.3 API Details

| Setting | Default | Description |
|---------|---------|-------------|
| `DEEPSEEK_API_KEY` | *(required)* | API key from DeepSeek |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com/v1` | OpenAI-compatible endpoint |
| `DEEPSEEK_MODEL` | `deepseek-chat` | Model name |
| `AGENT_MAX_TOKENS` | `4096` | Max tokens per response |
| `AGENT_TEMPERATURE` | `0.7` | Response creativity |

---

## 4. How to Run

```bash
# Install deps (already done in scaffold)
pip install -r requirements.txt

# Add your API key to .env
# DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx

# Test connectivity
python main.py --test

# Start interactive chat
python main.py
```

CLI commands during chat:
- `/exit` — Quit
- `/clear` — Reset conversation history
- `/help` — Show commands

---

## 5. Coding Conventions

- **Python version:** 3.14 (system interpreter at `C:/Python314/python.exe`)
- **Type hints:** Used everywhere (function signatures, class attributes)
- **Docstrings:** Every module, class, and public method has a docstring
- **Config:** All config lives in `.env`, loaded by `config/settings.py`; never hardcode secrets
- **Dependencies:** Minimal — `openai` and `python-dotenv` only; add new deps to `requirements.txt`
- **Naming:** snake_case for files/variables/functions, PascalCase for classes
- **Error handling:** `Agent.chat()` catches all exceptions and returns error strings rather than crashing the CLI loop

---

## 6. Current State & Limitations

| Feature | Status |
|---------|--------|
| CLI chat with DeepSeek | ✅ Working |
| Conversation history | ✅ Working |
| `--test` flag | ✅ Working |
| Tool framework (`BaseTool`) | ✅ Defined, not wired into agent |
| Google Calendar | 🔴 Stub only |
| Gmail | 🔴 Stub only |
| WhatsApp | 🔴 Stub only |
| Telegram | 🔴 Stub only |
| Function calling / tool use | 🔴 Not implemented |
| Multi-turn with tools | 🔴 Not implemented |

---

## 7. Future Roadmap (Planned by User)

1. **Wire up tool system** — allow the agent to actually call tools via DeepSeek's function calling
2. **Google Calendar integration** — `CalendarTool` full implementation using Google Calendar API
3. **Gmail integration** — `EmailTool` full implementation using Gmail API
4. **WhatsApp integration** — via Twilio or WhatsApp Business API
5. **Telegram integration** — via Telegram Bot API
6. **Bot interfaces** — replace CLI with WhatsApp bot and/or Telegram bot as entry points

---

## 8. Key Files to Modify by Task

| Task | Primary File(s) |
|------|-----------------|
| Change system prompt / agent personality | `agent/core.py` (`Agent.SYSTEM_PROMPT`) |
| Add a new tool | Create in `agent/tools/`, extend `BaseTool` |
| Wire tools into agent | `agent/core.py` (add tool-calling loop) |
| Change model parameters | `.env` or `config/settings.py` |
| Add new CLI commands | `agent/cli.py` |
| Switch to a different LLM provider | `agent/core.py` (change base_url/model) + `config/settings.py` |
| Add a new integration (e.g., Slack) | Create `agent/tools/slack.py` + add to `agent/core.py` |
| Create a Telegram bot entry point | New file (e.g., `agent/bots/telegram_bot.py`) |

---

## 9. Notes for the AI Assistant

- The user's OS is **Windows**. Use PowerShell commands with `;` separators (never `&&`).
- The Python interpreter is at `C:/Python314/python.exe`. Use this path or let the `configure_python_environment` tool set it up.
- The `.env` file is gitignored; never commit it. Always use `.env.example` as the template.
- When implementing new tools, follow the `BaseTool` pattern: extend the ABC, implement `async def execute(self, **kwargs) -> ToolResult`, set `name` and `description`.
- The OpenAI SDK is used only as an HTTP client — it is pointed at `https://api.deepseek.com/v1`, which is DeepSeek's OpenAI-compatible endpoint. This means OpenAI SDK features like streaming, function calling, etc. should work if DeepSeek supports them.
- Keep dependencies minimal. The user wants a lightweight scaffold.
- When the agent adds tool calling, the pattern would be: user message → agent decides to call tool → execute tool → send tool result back → agent formulates final response.
