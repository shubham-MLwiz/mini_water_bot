# Water Reminder Bot 💧

A personal Telegram bot that reminds you to drink water every hour, logs your intake, and tracks daily progress.

## Features

- Hourly reminders during waking hours (configurable)
- Custom on-demand reminders ("remind me in 10 mins")
- Natural text logging: just type "drank 200 ml"
- Daily summary with total and hourly breakdown
- Tells you how much you're lagging behind your target
- Single-user: locked to your Telegram account only

## Requirements

- Python 3.10+
- A Telegram account
- A bot token from [@BotFather](https://t.me/BotFather)

## Full Setup Guide

### Step 1: Create the bot on Telegram

1. Open Telegram → search for `@BotFather` → start a chat
2. Send `/newbot`
3. Choose a display name (e.g., "Water Reminder Bot")
4. Choose a username (must end in `bot`, e.g., `my_water_reminder_bot`)
5. BotFather replies with your **API token** — copy it (looks like `123456:ABC-DEF1234...`)

### Step 2: Get your Chat ID

1. Open Telegram → search for `@userinfobot` → start it
2. It replies with your numeric ID (e.g., `987654321`) — copy it

### Step 3: Register bot commands (enables slash menu)

1. Open `@BotFather` again
2. Send `/setcommands`
3. Select your bot
4. Send this exact text:
```
start - Welcome message
help - List all commands and usage
summary - Today's water intake breakdown
testreminder - Send a test reminder now
```
5. Now typing `/` in your bot's chat will show an autocomplete menu

### Step 4: Clone and configure

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd mini_water_bot

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file with your secrets
cp .env.example .env
```

Edit `.env` and fill in your values:

```
BOT_TOKEN=paste-your-token-here
CHAT_ID=paste-your-chat-id-here
DAILY_TARGET_ML=2500
WAKE_HOUR=7
SLEEP_HOUR=23
TIMEZONE=Asia/Kolkata
```

### Step 5: Run

```bash
# Make sure venv is activated
source venv/bin/activate

# Run the bot
python bot.py
```

Open your bot in Telegram and send `/start`. You should get a welcome message.

### Step 6: Keep it running

The bot must stay running to send reminders. Options:
- **Local machine:** Leave terminal open (or use `nohup python bot.py &`)
- **Cloud VM:** Deploy to GCP/AWS free tier as a systemd service

## Configuration (.env)

| Variable | Description | Default |
|----------|-------------|---------|
| `BOT_TOKEN` | Token from @BotFather | (required) |
| `CHAT_ID` | Your numeric Telegram user ID | (required) |
| `DAILY_TARGET_ML` | Daily water intake goal in ml | `2500` |
| `WAKE_HOUR` | Hour to start reminders (24h, local time) | `7` |
| `SLEEP_HOUR` | Hour to stop reminders (24h, local time) | `23` |
| `TIMEZONE` | Your IANA timezone | `Asia/Kolkata` |

## Usage (in Telegram)

| Input | What it does |
|-------|------|
| `/start` | Welcome message |
| `/help` | List all commands and input formats |
| `/summary` | Today's water intake breakdown + pace |
| `/testreminder` | Fire a test reminder immediately |
| `drank 200 ml` | Logs 200 ml at current time |
| `250ml` or `250` | Logs 250 ml |
| `how much today` | Shows today's total + pace |
| `remind me in 10 mins` | Schedules a one-time reminder |
| `remind me at 3:15 pm` | Schedules reminder at specific time |

## Running Tests

```bash
python test_bot.py
```

Tests database operations, message parsing, and keyword detection without needing Telegram.

## Network Note

Requires unrestricted internet access to `api.telegram.org`. Corporate networks with firewalls (e.g., Cisco Umbrella) will block it. Use a personal network.

## Project Structure

```
├── bot.py              ← Main bot logic (handlers, scheduler)
├── database.py         ← SQLite helpers (log, query, summarize)
├── test_bot.py         ← Automated test suite
├── .env                ← Your secrets (not in git)
├── .env.example        ← Template for .env
├── .gitignore          ← Ignores .env, venv/, *.db, *.log
├── requirements.txt    ← Pinned dependencies
├── implementation.md   ← Detailed build plan + architecture
└── README.md           ← This file
```
