import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()

def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    update.message.reply_text("🤖 Hello! Bot is working!")

def main():
    """Main bot entry point"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not found!")
        return
    
    print("🚀 Starting simple bot...")
    
    application = Application.builder().token(token).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    
    print("✅ Bot is running!")
    print("📢 Try /start command")
    
    # Start the Bot
    application.run_polling()

if __name__ == "__main__":
    main()