# Propaganda Pipeline Dashboard

A multi-source data collection and analysis pipeline for monitoring propaganda and disinformation campaigns.

## Features

- **Multi-Source Data Collection**: Gathers data from various social media platforms, news sources, and dark web forums
- **Real-Time Analysis**: Processes and analyzes incoming data streams for propaganda patterns
- **Automated Reporting**: Generates daily reports with findings and insights
- **Dashboard Integration**: Live dashboard displaying current campaigns and trends
- **Cron Job Integration**: Automated updates from scheduled tasks

## Quick Start

### Prerequisites

- Python 3.11+
- pip
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/kaledh4/medoasbot.git
cd medoasbot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the pipeline
python main.py
```

### Configuration

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

## Dashboard

The dashboard is available at: https://kaledh4.github.io/medoasbot/

### Features

- **Live Data Visualization**: Real-time charts and graphs
- **Campaign Tracking**: Monitor active propaganda campaigns
- **Daily Reports**: Automated daily summaries
- **Alert System**: Notifications for significant findings
- **Historical Data**: Access to past campaign data

## Cron Jobs

### Scheduled Tasks

The pipeline includes automated cron jobs for:

- **Data Collection**: Scheduled data gathering from sources
- **Analysis**: Regular analysis of collected data
- **Report Generation**: Automated daily report creation
- **Dashboard Updates**: Real-time dashboard refreshes

### Adding New Cron Jobs

1. Add your job to `scripts/` directory
2. Configure in `crontab` or `cron.yaml`
3. Dashboard will automatically display results

## API Endpoints

### Data Collection
- `GET /api/v1/data/collect` - Trigger data collection
- `GET /api/v1/data/status` - Check collection status

### Analysis
- `GET /api/v1/analysis/start` - Start analysis
- `GET /api/v1/analysis/status` - Check analysis status

### Reports
- `GET /api/v1/reports/daily` - Get daily report
- `GET /api/v1/reports/weekly` - Get weekly report

## Development

### Project Structure

```
medoasbot/
├── main.py              # Main entry point
├── services/            # Backend services
│   ├── ai_agent.py     # AI analysis service
│   ├── aggregation.py  # Data aggregation
│   ├── deepseek.py     # DeepSeek integration
│   ├── gemini.py       # Google Gemini integration
│   ├── ranking.py      # Content ranking
│   └── store.py        # Data storage
├── scripts/            # Utility scripts
├── static/             # Static assets
├── data/               # Data files
├── tests/              # Test files
└── docs/               # Documentation
```

### Testing

```bash
# Run all tests
python -m pytest

# Run specific test
python -m pytest tests/test_security.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the [documentation](docs/)
- Join our Discord community

---

**Built with ❤️ for monitoring and analyzing propaganda campaigns**
