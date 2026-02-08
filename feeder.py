import feedparser
import json
import os
from database import Database

class Feeder:
    def __init__(self, sources_path="/root/daily_brief/sources.json"):
        self.sources_path = sources_path
        self.db = Database()

    def load_sources(self):
        with open(self.sources_path, 'r') as f:
            return json.load(f)

    def fetch_rss(self):
        sources = self.load_sources()
        articles = []
        for source in sources.get("rss", []):
            feed = feedparser.parse(source['url'])
            for entry in feed.entries[:5]: # Limit to 5 per source
                title = entry.title
                link = entry.link
                summary = getattr(entry, 'summary', '')
                
                title_hash = self.db.generate_hash(title)
                if not self.db.is_duplicate(title_hash):
                    articles.append({
                        "source": source['name'],
                        "title": title,
                        "link": link,
                        "text": f"{title}\n{summary}",
                        "hash": title_hash
                    })
        return articles

    def fetch_reddit(self):
        # Placeholder for PRAW logic
        # Requires REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
        return []

    def fetch_all(self):
        return self.fetch_rss() + self.fetch_reddit()
