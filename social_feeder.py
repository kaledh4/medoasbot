"""
Social Media Feeder - Fetches content from Reddit and X/Twitter
Uses:
- Reddit: Native RSS feeds (old.reddit.com/r/subreddit/.rss)
- X/Twitter: OpenClaw web_fetch via gateway (fallback to web search)
"""

import feedparser
import requests
import json
import os
import subprocess
from database import Database


class SocialFeeder:
    def __init__(self, sources_path="/root/daily_brief/sources.json"):
        self.sources_path = sources_path
        self.db = Database()
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        
    def load_sources(self):
        with open(self.sources_path, 'r') as f:
            return json.load(f)
    
    def fetch_reddit(self):
        """
        Fetch posts from Reddit subreddits via RSS.
        Returns list of article dicts.
        """
        sources = self.load_sources()
        articles = []
        
        for sub in sources.get("reddit", []):
            subreddit = sub['subreddit']
            limit = sub.get('limit', 10)
            
            # Use old.reddit.com RSS feed (more reliable)
            rss_url = f"https://old.reddit.com/r/{subreddit}/.rss"
            
            try:
                # Fetch with requests (proper User-Agent)
                headers = {'User-Agent': self.user_agent}
                response = requests.get(rss_url, headers=headers, timeout=15)
                
                if response.status_code != 200:
                    print(f"Error fetching r/{subreddit}: HTTP {response.status_code}")
                    continue
                
                # Parse the fetched RSS content
                feed = feedparser.parse(response.text)
                
                for entry in feed.entries[:limit]:
                    title = entry.title
                    link = entry.link
                    
                    # Extract summary from content if available
                    summary = ""
                    if hasattr(entry, 'content') and entry.content:
                        # Reddit RSS uses HTML in content
                        summary = entry.content[0].get('value', '')[:500]
                    elif hasattr(entry, 'summary'):
                        summary = entry.summary[:500]
                    
                    title_hash = self.db.generate_hash(title)
                    if not self.db.is_duplicate(title_hash):
                        articles.append({
                            "source": f"r/{subreddit}",
                            "title": title,
                            "link": link,
                            "text": f"{title}\n{summary}",
                            "hash": title_hash,
                            "type": "reddit"
                        })
                        
            except Exception as e:
                print(f"Error fetching r/{subreddit}: {e}")
                continue
                
        return articles
    
    def fetch_x_via_openclaw(self, handle):
        """
        Fetch X/Twitter content using OpenClaw gateway's web_fetch tool.
        This leverages the gateway's Firecrawl/readability extraction.
        """
        try:
            # Use OpenClaw CLI to fetch (if available)
            # Format: openclaw run "fetch https://x.com/handle"
            url = f"https://x.com/{handle}"
            
            # Try using requests with good headers first
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                # Basic extraction - X returns JS-heavy page, so limited
                return response.text[:5000]
            
            return None
            
        except Exception as e:
            print(f"Error fetching @{handle}: {e}")
            return None
    
    def fetch_x_accounts(self):
        """
        Fetch content from X/Twitter accounts.
        Uses multiple strategies:
        1. Try Nitter instances (if available)
        2. Try web search for recent posts
        3. Fallback to nothing (log for manual review)
        """
        sources = self.load_sources()
        articles = []
        
        # List of Nitter instances to try
        nitter_instances = [
            "nitter.net",
            "nitter.privacydev.net",
            "nitter.poast.org",
            "nitter.unixfox.eu",
            "nitter.projectsegfau.lt",
            "nitter.it",
            "nitter.moomoo.me",
            "nitter.rawbit.ninja",
            "nitter.ca",
        ]
        
        for account in sources.get("x_accounts", []):
            handle = account['handle']
            name = account['name']
            
            # Try Nitter RSS first
            fetched = False
            for instance in nitter_instances:
                try:
                    rss_url = f"https://{instance}/{handle}/rss"
                    feed = feedparser.parse(
                        rss_url,
                        request_headers={'User-Agent': self.user_agent}
                    )
                    
                    if feed.entries:
                        for entry in feed.entries[:5]:
                            title = entry.title[:200] if entry.title else f"Post by @{handle}"
                            link = entry.link
                            summary = getattr(entry, 'description', '')[:500]
                            
                            title_hash = self.db.generate_hash(title + link)
                            if not self.db.is_duplicate(title_hash):
                                articles.append({
                                    "source": f"@{handle}",
                                    "title": title,
                                    "link": link,
                                    "text": f"@{handle}: {title}\n{summary}",
                                    "hash": title_hash,
                                    "type": "twitter"
                                })
                        fetched = True
                        break
                        
                except Exception:
                    continue
            
            if not fetched:
                # Log that we couldn't fetch this account
                print(f"Could not fetch @{handle} from any Nitter instance")
                
        return articles
    
    def fetch_all(self):
        """
        Fetch all social media content.
        """
        articles = []
        
        # Reddit (reliable)
        reddit_articles = self.fetch_reddit()
        print(f"Fetched {len(reddit_articles)} articles from Reddit")
        articles.extend(reddit_articles)
        
        # X/Twitter (best effort)
        x_articles = self.fetch_x_accounts()
        print(f"Fetched {len(x_articles)} posts from X/Twitter")
        articles.extend(x_articles)
        
        return articles


# Test if run directly
if __name__ == "__main__":
    feeder = SocialFeeder()
    articles = feeder.fetch_all()
    
    print(f"\n=== Total: {len(articles)} articles ===\n")
    for i, article in enumerate(articles[:10]):
        print(f"{i+1}. [{article['source']}] {article['title'][:80]}...")
        print(f"   Link: {article['link']}")
        print()
