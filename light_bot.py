import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()

def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    update.message.reply_text("🤖 MedoasBot is running!")

def main():
    """Main bot entry point"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not found!")
        return
    
    print("🚀 Starting lightweight bot...")
    
    # Create application with proper configuration
    application = Application.builder().token(token).build()
    
    # Register only essential handlers
    application.add_handler(CommandHandler("start", start))
    
    print("✅ Bot running with minimal memory footprint")
    print("📢 Try /start command")
    
    # Start the Bot with proper configuration
    application.run_polling(
        allowed_updates=["message"],
        timeout=30,
        clean=True
    )

if __name__ == "__main__":
    main()