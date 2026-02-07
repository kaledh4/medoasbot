## Quick Start - Telegram Bot

### Prerequisites

1. **Telegram Bot Token**: You already have this configured in `.env`
2. **Python 3.8+**: Required for async/await syntax
3. **Virtual Environment** (recommended): For dependency isolation

### Setup Instructions

#### 1. Activate Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 3. Verify Environment

```bash
python tests/test_environment.py
```

#### 4. Run the Bot

```bash
python bot.py
```

### Expected Output

When you run the bot, you should see:

```
🚀 Starting MedoasBot...
✅ Bot is running and ready to receive commands!
📢 Access the bot at: https://t.me/medoasbot
💡 Try /start to begin
```

### Testing Bot Commands

Once the bot is running, open Telegram and message `@medoasbot` with:

- `/start` - Initialize the bot
- `/help` - Show available commands
- `/status` - Check pipeline status

### Common Issues

#### Permission Denied

Make sure your SSH key is properly configured:
```bash
ssh-add ~/.ssh/id_ed25519_new
```

#### Missing Dependencies

If you get import errors, reinstall dependencies:
```bash
pip install -r requirements.txt
```

#### Environment Variables

Ensure `.env` file exists with:
```bash
TELEGRAM_BOT_TOKEN=your_token_here
```

## Development

### Adding New Commands

1. Create async function in `bot.py`
2. Register with `application.add_handler(CommandHandler("command_name", function_name))`
3. Test locally

### Testing

Use the test files in `/tests/` directory:
- `test_environment.py` - Environment validation
- `test_bot_init.py` - Bot initialization test

## Security

- ✅ Bot token is protected in `.env`
- ✅ `.gitignore` prevents token commits
- ✅ SSH key authentication for GitHub

---

**Bot is ready to deploy!** 🚀