# Water Reminder Bot 💧

A personal Telegram bot that reminds you to drink water every hour, logs your intake, and tracks daily progress.

## Features

- Hourly reminders during waking hours (configurable)
- Natural text logging: just type "drank 200 ml"
- Daily summary with total and hourly breakdown
- Tells you how much you're lagging behind your target
- Single-user: locked to your Telegram account only

## Requirements

- Python 3.10+
- A Telegram account
- A bot token from [@BotFather](https://t.me/BotFather)

## Setup

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd Telegram_bot

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file with your secrets
cp .env.example .env
# Edit .env and fill in your BOT_TOKEN and CHAT_ID
```

## Configuration (.env)

| Variable | Description | Example |
|----------|-------------|---------|
| `BOT_TOKEN` | Token from @BotFather | `123456:ABC-DEF...` |
| `CHAT_ID` | Your numeric Telegram user ID (get from @userinfobot) | `987654321` |
| `DAILY_TARGET_ML` | Daily water intake goal in ml | `2500` |
| `WAKE_HOUR` | Hour to start sending reminders (24h format) | `7` |
| `SLEEP_HOUR` | Hour to stop sending reminders (24h format) | `23` |

## Running

```bash
# Make sure venv is activated
source venv/bin/activate

# Run the bot
python bot.py
```

The bot runs until you press `Ctrl+C`. It must stay running to send reminders and receive messages.

## Usage (in Telegram)

| Input | What it does |
|-------|------|
| `/start` | Welcome message |
| `/summary` | Today's water intake breakdown |
| `/help` | List all commands |
| `drank 200 ml` | Logs 200 ml at current time |
| `250ml` | Logs 250 ml |
| `how much today` | Shows today's total |

## Network Note

This bot requires unrestricted internet access to `api.telegram.org`. Corporate networks with proxy/firewall (e.g., Cisco Umbrella) will block it. Use a personal network.

## Project Structure

```
├── bot.py              ← Main bot logic
├── database.py         ← SQLite helpers
├── .env                ← Your secrets (not in git)
├── .gitignore          ← Ignores .env, venv/, *.db
├── requirements.txt    ← Pinned dependencies
└── implementation.md   ← Detailed implementation plan
```
