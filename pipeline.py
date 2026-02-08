import os
import gc
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv
from feeder import Feeder
from logic_engine import LogicEngine
from database import Database
from telegram_util import send_telegram_message
import subprocess
from publish import generate_html


# Load environment variables
load_dotenv(dotenv_path="/root/daily_brief/.env")

# Configuration
LOG_FILE = "/root/daily_brief/logs/pipeline.log"
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(message)s')

def run_2hour_pulse():
    logging.info("Starting 2-hour pulse...")
    feeder = Feeder()
    engine = LogicEngine()
    db = Database()
    
    # 1. Fetch new articles
    articles = feeder.fetch_all()
    logging.info(f"Fetched {len(articles)} new articles.")
    
    new_toon_phrases = []
    
    # 2. Process each article
    for article in articles:
        # Generate hash and check deduplication (Feeder already does some, but double check)
        title_hash = article['hash']
        if db.is_duplicate(title_hash):
            continue
            
        # 3. New Filter Stage: The Bouncer
        # Only meaningful content gets past here.
        if not engine.assess_relevance(article['title'], article['text']):
            logging.info(f"Skipped low relevance: {article['title']}")
            continue

        # 4. Use Logic Engine to analyze (The Deep Dive)
        # Get recent context for "Talk-Through"
        context = db.get_recent_toon_phrases(limit=3)
        analysis = engine.analyze(article['text'], previous_context=context)
        
        if analysis:
            # 5. Save to Memory
            db.add_mention(article['source'], article['text'], analysis, title_hash, url=article.get('link'))
            new_toon_phrases.append(analysis)
            logging.info(f"Analyzed & Saved: {article['title']}")
        
    # 5. Send to Telegram
    if new_toon_phrases:
        # Combine 3-5 punchy toon phrases
        summary = "\n\n".join(new_toon_phrases[:5])
        message = f"📌 *2-Hour Intelligence Pulse*\n\n{summary}"
        send_telegram_message(message)
        logging.info("Sent pulse to Telegram.")
    else:
        logging.info("No new significant insights to report.")

def run_24hour_wrap():
    logging.info("Starting 24-hour wrap...")
    db = Database()
    engine = LogicEngine()
    
    # Get all toon phrases from today
    today = datetime.now().strftime('%Y-%m-%d')
    phrases = db.get_daily_phrases(today)
    
    if phrases:
        # Transform the raw toon phrases into a professional executive brief
        content = "\n\n".join(phrases)
        wrap = engine.generate_executive_brief(content)
        if wrap:
            # Send to Telegram
            message = f"📊 *Executive Brief: Daily Intelligence Summary*\n\n{wrap}"
            send_telegram_message(message)
            logging.info("Sent daily executive brief to Telegram.")
            
            # Save wrap
            db.save_daily_wrap(today, wrap)
    else:
        logging.info("No phrases found for today's wrap.")

def run_publish():
    logging.info("Generating and pushing dashboard...")
    try:
        # Run publish.py content generation directly
        generate_html()
        
        # Git push
        subprocess.run(["git", "add", "docs/index.html", ".nojekyll", "docs/.nojekyll"], check=True)
        # Commit if there are changes
        commit_result = subprocess.run(["git", "commit", "-m", "Auto-update intelligence dashboard"], capture_output=True, text=True)
        if "nothing to commit" not in commit_result.stdout:
            subprocess.run(["git", "push", "origin", "master"], check=True)
            logging.info("Dashboard pushed to GitHub.")
        else:
            logging.info("No changes to dashboard.")
    except Exception as e:
        logging.error(f"Publishing error: {e}")


def cleanup():
    logging.info("Running Janitor...")
    # Force Garbage Collection
    gc.collect()
    # Kill any stray OpenClaw/Chrome processes
    os.system("pkill -9 chrome || true")
    os.system("pkill -9 chromedriver || true")
    logging.info("Janitor finished.")

if __name__ == "__main__":
    try:
        # Check if it's midnight for the daily wrap
        now = datetime.now()
        
        # Always run the 2-hour pulse
        run_2hour_pulse()
        
        # If it's the 00:00 (or near it) run, do the daily wrap
        if now.hour == 0:
            run_24hour_wrap()
            
        # Always publish the latest stream
        run_publish()

            
    except Exception as e:
        logging.error(f"Pipeline error: {e}")
    finally:
        cleanup()
        sys.exit(0)
