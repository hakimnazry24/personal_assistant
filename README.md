# 🤖 Personal Assistant Agent

An AI-powered personal assistant powered by **DeepSeek V4 Pro**. Currently in the scaffold phase with CLI-only chat. Integrations with Google Calendar, Gmail, WhatsApp, and Telegram are planned for future releases.

---

## ✨ Features

- **CLI Chat** — Interactive command-line interface to chat with your personal assistant
- **Conversation History** — Multi-turn conversations with `/clear` to reset
- **DeepSeek V4 Pro** — Powered by DeepSeek's latest model via the OpenAI-compatible API
- **Extensible Tool System** — Ready-made framework for adding integrations
- **Planned Integrations:** Google Calendar, Gmail, WhatsApp, Telegram

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- A [DeepSeek API key](https://platform.deepseek.com/)

### Setup

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd personal_assistant

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your API key
cp .env.example .env
# Edit .env and replace your_deepseek_api_key_here with your actual key

# 4. Test the connection
python main.py --test

# 5. Start chatting
python main.py
```

### CLI Commands

| Command | Description |
|---------|-------------|
| `/exit` | Exit the assistant |
| `/clear` | Clear conversation history |
| `/help` | Show available commands |

---

## 📁 Project Structure

```
personal_assistant/
├── main.py                       # Entry point
├── config/
│   └── settings.py               # Configuration from .env
├── agent/
│   ├── core.py                   # Agent using OpenAI SDK → DeepSeek
│   ├── cli.py                    # Interactive CLI loop
│   └── tools/
│       ├── base.py               # Base tool class
│       ├── calendar.py           # Google Calendar (stub)
│       ├── email.py              # Gmail (stub)
│       └── messaging.py          # WhatsApp + Telegram (stubs)
├── .env.example                  # Environment template
├── requirements.txt              # Dependencies
└── README.md
```

---

## ⚙️ Configuration

All settings are in the `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `DEEPSEEK_API_KEY` | *(required)* | Your DeepSeek API key |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com/v1` | API endpoint |
| `DEEPSEEK_MODEL` | `deepseek-chat` | Model to use |
| `AGENT_NAME` | `PersonalAssistant` | Name the agent uses |
| `AGENT_MAX_TOKENS` | `4096` | Max tokens per response |
| `AGENT_TEMPERATURE` | `0.7` | Response creativity (0-2) |

---

## 🔮 Roadmap

- [ ] Wire up tool-calling loop in the agent
- [ ] Google Calendar integration
- [ ] Gmail integration
- [ ] WhatsApp bot interface
- [ ] Telegram bot interface
- [ ] Additional integrations (Slack, Notion, etc.)

---

## 🛠️ Tech Stack

- **Python 3.14**
- **OpenAI Python SDK** (pointed at DeepSeek's compatible endpoint)
- **python-dotenv** for configuration

---

## 📄 License

MIT
