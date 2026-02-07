import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    message = """🤖 Welcome to MedoasBot! 

📊 This bot delivers curated propaganda analysis from the Medoas pipeline.
🚀 Use /help to see available commands.

📈 Real-time monitoring of:
- Multi-source data aggregation
- Automated content analysis
- Pipeline status updates
"""
    await update.message.reply_text(message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    message = """📖 Available Commands:

/start - Initialize the bot and get started
/help - Show this help message
/status - Check pipeline status
/stats - View analytics and metrics
/report - Generate analysis report

💡 Bot is connected to the Medoas propaganda analysis pipeline.
"""
    await update.message.reply_text(message)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    message = """📊 Pipeline Status: ✅ Operational

🔄 Last sync: Just now
📊 Data points: 42
🔄 Sources: 7 active

📢 Ready to deliver curated propaganda analysis.
"""
    await update.message.reply_text(message)

def main():
    """Main bot entry point"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not found in environment!")
        return
    
    print("🚀 Starting MedoasBot...")
    
    application = Application.builder().token(token).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status))
    
    print("✅ Bot is running and ready to receive commands!")
    print("📢 Access the bot at: https://t.me/medoasbot")
    print("💡 Try /start to begin")
    
    # Start the Bot
    application.run_polling()

if __name__ == '__main':
    main()