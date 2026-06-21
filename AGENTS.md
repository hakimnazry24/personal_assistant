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

```json
personal_assistant/
├── .env                          # API key + config (gitignored)
├── .env.example                  # Template for .env (committed)
├── .gitignore
├── requirements.txt              # openai, python-dotenv, mcp
├── main.py                       # CLI entry point (python main.py | --test | --test-tools)
├── AGENTS.md                     # This file
├── README.md                     # Human-facing docs
├── mcp_servers.json              # MCP server registry (for external MCP servers)
├── config/
│   ├── __init__.py
│   └── settings.py               # Loads .env via python-dotenv; Settings dataclass
└── agent/
    ├── __init__.py
    ├── core.py                    # Agent class — chat-only + tool-calling loop
    ├── cli.py                     # Async CLI with tool support + /tools command
    ├── mcp/
    │   ├── __init__.py            # Exports MCPClient, MCPManager
    │   ├── client.py              # MCPClient — stdio transport for external MCP servers
    │   ├── manager.py             # MCPManager — multi-server lifecycle + tool registry
    │   ├── adapters.py            # InProcessMCPAdapter — no-subprocess tool calling
    │   └── servers/
    │       ├── __init__.py
    │       └── calendar_server.py # FastMCP server with mock calendar tools
    └── tools/
        ├── __init__.py
        ├── base.py                # BaseTool (ABC) + ToolResult (dataclass)
        ├── calendar.py            # CalendarTool — stub
        ├── email.py               # EmailTool — stub
        └── messaging.py           # WhatsAppTool + TelegramTool — stubs
```

---

## 3. Architecture

### 3.1 Core Flow (Chat Only)

```
User (CLI stdin) → cli.py → Agent.chat_with_history() → OpenAI SDK → DeepSeek API → Response → stdout
```

### 3.2 Tool-Calling Flow (Chat + Tools)

```
User: "What's on my calendar tomorrow?"
  │
  ▼
cli.py → Agent.chat_with_tools()
  │
  ▼
ToolProvider.list_all_tools() → builds OpenAI tool definitions
  │
  ▼
Agent sends [system prompt, history, tool defs] → DeepSeek API
  │
  ▼
DeepSeek responds: { tool_calls: [{ name: "list_events", args: { date: "..." } }] }
  │
  ▼
Agent calls ToolProvider.call_tool("list_events", { date: "..." })
  │
  ▼
InProcessMCPAdapter → calendar_server.list_events() → returns mock events
  │
  ▼
Tool result sent back to DeepSeek as a "tool" role message
  │
  ▼
DeepSeek formulates final text response with the event data
  │
  ▼
User sees: "Tomorrow you have 3 events: Morning Standup, Lunch, Project Review"
```

### 3.3 Tool Providers

The agent uses a `ToolProvider` protocol — any object with these methods works:
- `started: bool` — whether tools are available
- `list_all_tools() -> list[dict]` — get tool definitions
- `call_tool(name, args) -> Any` — execute a tool
- `shutdown_all()` — cleanup

Two implementations exist:
- **`MCPManager`** — connects to external MCP servers via stdio (for Node.js servers, etc.)
- **`InProcessMCPAdapter`** — runs tools directly in Python (no subprocess, more reliable)

The in-process adapter is the default (used when `mcp_servers.json` has no servers).

- `cli.py` manages the read-eval-print loop and conversation history (list of `{role, content}` dicts).
- `Agent` (in `core.py`) wraps the OpenAI SDK, prepends the system prompt, and calls `client.chat.completions.create()`.
- When tools are available, `Agent.chat_with_tools()` sends tool definitions alongside messages and handles the tool-calling loop (up to `AGENT_MAX_TOOL_ROUNDS` rounds).
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

# Test tool-calling (MCP + function calling)
python main.py --test-tools

# Start interactive chat
python main.py
```

CLI commands during chat:
- `/exit` — Quit
- `/clear` — Reset conversation history
- `/help` — Show commands
- `/tools` — List available tools (when tools are active)

---

## 5. Coding Conventions

- **Python version:** 3.14 (system interpreter at `C:/Python314/python.exe`)
- **Type hints:** Used everywhere (function signatures, class attributes)
- **Docstrings:** Every module, class, and public method has a docstring
- **Config:** All config lives in `.env`, loaded by `config/settings.py`; never hardcode secrets
- **Dependencies:** Minimal — `openai`, `python-dotenv`, and `mcp`; add new deps to `requirements.txt`
- **Naming:** snake_case for files/variables/functions, PascalCase for classes
- **Error handling:** `Agent.chat()` catches all exceptions and returns error strings rather than crashing the CLI loop

---

## 6. Current State & Limitations

| Feature | Status |
|---------|--------|
| CLI chat with DeepSeek | ✅ Working |
| Conversation history | ✅ Working |
| `--test` flag | ✅ Working |
| `--test-tools` flag | ✅ Working |
| Tool framework (`BaseTool`) | ✅ Defined |
| MCP client layer (`MCPClient`, `MCPManager`) | ✅ Implemented (Phase 1) |
| In-process tool adapter (`InProcessMCPAdapter`) | ✅ Implemented (Phase 2) |
| Mock calendar MCP server (Python) | ✅ Implemented (Phase 2) |
| Tool-calling loop in agent | ✅ Implemented (Phase 3) |
| `mcp_servers.json` config | ✅ Created |
| Google Calendar (real API) | 🔴 Mock only |
| Gmail | 🔴 Stub only |
| WhatsApp | 🔴 Stub only |
| Telegram | 🔴 Stub only |
| External MCP server (stdio) | ⚠️ anyio/Python 3.14 issue |

---

## 7. Future Roadmap (Planned by User)

1. ~~**Wire up tool system**~~ ✅ — agent can call tools via DeepSeek's function calling
2. ~~**Google Calendar integration (mock)**~~ ✅ — in-process mock calendar with CRUD
3. **Google Calendar (real API)** — swap mock handlers with Google Calendar API calls
4. **Gmail integration** — `EmailTool` using Gmail API
5. **WhatsApp integration** — via Twilio or WhatsApp Business API
6. **Telegram integration** — via Telegram Bot API
7. **Bot interfaces** — replace CLI with WhatsApp bot and/or Telegram bot as entry points

---

## 8. Key Files to Modify by Task

| Task | Primary File(s) |
|------|-----------------|
| Change system prompt / agent personality | `agent/core.py` (`Agent.SYSTEM_PROMPT`) |
| Add a new tool | Create in `agent/tools/`, extend `BaseTool` |
| Wire tools into agent | `agent/core.py` (add tool-calling loop) |
| Add a new MCP server | Add entry to `mcp_servers.json` |
| Change MCP client transport | `agent/mcp/client.py` |
| Add in-process tool | `agent/mcp/adapters.py` |
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

### MCP Architecture Notes

- **`MCPClient`** (`agent/mcp/client.py`) handles a single MCP server connection via stdio. It launches the server as a subprocess, initializes an MCP session, and exposes `list_tools()` / `call_tool()`.
- **`MCPManager`** (`agent/mcp/manager.py`) reads `mcp_servers.json`, starts all configured servers, and maintains a tool registry mapping tool names → servers.
- **`InProcessMCPAdapter`** (`agent/mcp/adapters.py`) provides the same interface without spawning subprocesses. Tools are registered directly and called as Python functions. This avoids the anyio/Python 3.14 stdio transport issue.
- **`mcp_servers.json`** is the single source of truth for which MCP servers the agent connects to. Each server entry needs `command`, optional `args`, and optional `env` (with `${VAR}` substitution).
- The MCP Python SDK (`mcp` on PyPI) provides `ClientSession`, `StdioServerParameters`, and `stdio_client`.
- In Phase 3, `Agent.chat_with_history()` will be extended to accept MCP tool definitions and handle tool-calling responses from the LLM.
- MCP servers run as separate OS processes — the agent does not bundle Google API logic directly.
