import streamlit as st
import json
import sqlite3
import pandas as pd
from datetime import datetime

# Page config
st.set_page_config(page_title="Daily Brief Dashboard", page_icon="🕵️", layout="wide")

# Paths
DB_PATH = "/root/daily_brief/data/briefs.db"
SOURCES_PATH = "/root/daily_brief/sources.json"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn

def load_sources():
    with open(SOURCES_PATH, 'r') as f:
        return json.load(f)

def save_sources(sources):
    with open(SOURCES_PATH, 'w') as f:
        json.dump(sources, f, indent=2)

st.title("🕵️ Daily Brief Intelligence Center")

# Sidebar for source management
st.sidebar.header("📡 Source Management")
sources = load_sources()

# Add new source
with st.sidebar.expander("➕ Add RSS Source"):
    new_name = st.text_input("Name")
    new_url = st.text_input("RSS URL")
    if st.button("Add"):
        if new_name and new_url:
            sources['rss'].append({"name": new_name, "url": new_url})
            save_sources(sources)
            st.success(f"Added {new_name}")
            st.rerun()

# List and remove sources
st.sidebar.subheader("Current RSS Sources")
for i, source in enumerate(sources.get('rss', [])):
    col1, col2 = st.sidebar.columns([4, 1])
    col1.text(source['name'])
    if col2.button("❌", key=f"del_{i}"):
        sources['rss'].pop(i)
        save_sources(sources)
        st.success("Removed source")
        st.rerun()

# Main Area - Intel Stream
st.header("📈 Intelligence Stream")

conn = get_db_connection()
query = "SELECT timestamp, source, analysis_toon_phrase FROM mentions ORDER BY timestamp DESC LIMIT 50"
df = pd.read_sql_query(query, conn)
conn.close()

if not df.empty:
    for _, row in df.iterrows():
        with st.container():
            st.markdown(f"**[{row['timestamp']}] {row['source']}**")
            st.info(row['analysis_toon_phrase'])
            st.divider()
else:
    st.write("No intelligence reports found yet.")

# Footer
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
