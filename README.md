# MedoasBot - Propaganda Analysis Pipeline

Automated data collection and analysis pipeline for propaganda detection and distribution.

## Features

- **Multi-source data aggregation** - Collects from various propaganda sources
- **Telegram bot interface** - Real-time updates via @medoasbot
- **Automated content analysis** - AI-powered propaganda detection
- **Real-time monitoring** - Live dashboard and notifications
- **Pipeline orchestration** - Coordinated data processing workflow

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/kaledh4/medoasbot.git
cd medoasbot
```

### 2. Set up virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 5. Run the bot

```bash
python bot.py
```

## Environment Variables

Create a `.env` file with:

```
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

## Project Structure

```
.
├── bot.py              # Telegram bot entry point
├── main.py             # Pipeline orchestrator
├── src/
│   └── pipeline/       # Data pipeline modules
├── tests/              # Test files and cron jobs
├── requirements.txt    # Python dependencies
├── .env               # Configuration (not committed)
├── .gitignore         # Git ignore rules
└── README.md          # This file
```

## Telegram Bot

Access the bot at: https://t.me/medoasbot

### Available Commands

- `/start` - Initialize bot and get started
- `/help` - Show help message
- `/status` - Check pipeline status
- `/stats` - View analytics and metrics
- `/report` - Generate analysis report

## Security

⚠️ **Never commit `.env` files or API tokens to version control.**

The `.gitignore` file protects your sensitive credentials from being pushed to GitHub.

## Development

### Running the pipeline

```bash
python main.py
```

### Testing

```bash
python -m pytest tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Contact the development team

---

**Built with ❤️ for propaganda analysis and detection**