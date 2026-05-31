# Telegram Water Reminder Bot — Implementation Plan

## Overview

A personal Telegram bot that:
1. Reminds you to drink water every hour (during waking hours)
2. Logs water intake from natural text messages (e.g., "drank 200 ml")
3. Gives daily summaries and tells you how much you're lagging behind

## Tech Stack

| Component | Choice | Reason |
|-----------|--------|--------|
| Language | Python 3.10+ | Simple, great library support |
| Bot Library | `python-telegram-bot` v21+ | Mature, secure, built-in scheduler |
| Database | SQLite (via Python's `sqlite3`) | Zero config, file-based, persistent |
| Secrets | `.env` file + `python-dotenv` | Keeps token out of code |
| Scheduler | `JobQueue` (built into the bot library) | No extra setup needed |
| Hosting | Local machine first → GCP/AWS free tier later | Learn locally, deploy when ready |

## Architecture

```
You (Telegram app)
    ↕ (HTTPS, encrypted)
Telegram servers
    ↕ (Polling — bot asks "any new messages?")
bot.py (your machine)
    ├── Handlers: /start, /summary, /help, natural text parsing
    ├── JobQueue: hourly reminders (7 AM – 11 PM)
    └── database.py → water.db (SQLite file)
```

## File Structure

```
Telegram_bot/
├── bot.py              ← Main bot logic (handlers, scheduler, entry point)
├── database.py         ← SQLite helper functions (log, query, summarize)
├── .env                ← BOT_TOKEN and CHAT_ID (never committed to git)
├── .gitignore          ← Excludes .env, venv/, *.db, __pycache__/, *.log
├── requirements.txt    ← Pinned dependencies
├── implementation.md   ← This file
└── venv/               ← Python virtual environment (not committed)
```

## Configuration (in .env)

```
BOT_TOKEN=your-token-from-botfather
CHAT_ID=your-numeric-chat-id
DAILY_TARGET_ML=2500
WAKE_HOUR=7
SLEEP_HOUR=23
```

---

## Implementation Steps

### Phase 1: Project Setup (no bot code yet)

- [x] **Step 1** — Create bot via @BotFather on Telegram, get API token
- [x] **Step 2** — Get your Chat ID via @userinfobot
- [x] **Step 3** — Set up project folder structure (.env, .gitignore, requirements.txt)
- [x] **Step 4** — Create Python virtual environment (Python 3.14.5)
- [x] **Step 5** — Install dependencies (python-telegram-bot 22.7, python-dotenv 1.2.2)

### Phase 2: Minimal Working Bot

- [ ] **Step 6** — Write bot.py with /start handler (proves token works)
- [ ] **Step 7** — Add chat ID restriction (only YOU can use the bot)

### Phase 3: Water Intake Logging

- [ ] **Step 8** — Create database.py with SQLite schema and helper functions
- [ ] **Step 9** — Add natural text parser for intake messages ("drank 200 ml")
- [ ] **Step 10** — Add /summary command and natural query support

### Phase 4: Hourly Reminders

- [ ] **Step 11** — Set up JobQueue for hourly reminders during waking hours
- [ ] **Step 12** — Add "lagging behind" calculation (actual vs expected)

### Phase 5: Polish

- [ ] **Step 13** — Add /help command
- [ ] **Step 14** — Add error handling and file logging
- [ ] **Step 15** — End-to-end test on local machine

### Phase 6: Cloud Deployment (separate effort)

- [ ] **Step 16** — Deploy to GCP e2-micro or AWS free tier

---

## Verification Checklist

1. `/start` → bot responds with welcome message
2. "drank 200 ml" → bot confirms logging + shows running total
3. Hourly reminder arrives during waking hours with today's total
4. `/summary` → shows full day breakdown
5. Restart the bot → `/summary` still shows old data (persistence works)
6. Message from a different Telegram account → bot ignores it

---

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| Polling mode (not webhooks) | Simpler, no public URL or HTTPS cert needed |
| SQLite (not Postgres/Redis) | One user, tiny data, zero infrastructure |
| Single-user restriction | Security without complexity |
| `python-telegram-bot` (not DIY) | Battle-tested, more secure than hand-rolled HTTP |
| `.env` for secrets | Industry standard, works locally and on servers |
| Waking hours only | Don't want 3 AM buzzes |
