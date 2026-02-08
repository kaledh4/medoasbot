import sqlite3
import os
from datetime import datetime
import markdown
import re

DB_PATH = "/root/daily_brief/data/briefs.db"
OUTPUT_PATH = "/root/daily_brief/docs/index.html"


from logic_engine import LogicEngine

# ... imports ...

def generate_html():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get latest daily wrap
    cursor.execute("SELECT date, wrap_text FROM daily_wraps ORDER BY date DESC LIMIT 1")
    daily_wrap = cursor.fetchone()
    
    conn.close()

    # Convert Markdown to HTML if wrap exists
    brief_html_en = ""
    brief_html_ar = ""
    report_date = datetime.now().strftime('%Y-%m-%d')
    
    if daily_wrap:
        report_date = daily_wrap[0]
        text_en = daily_wrap[1]
        
        # 1. Generate Arabic Translation
        engine = LogicEngine()
        print("Generating Arabic translation...")
        text_ar = engine.translate_to_arabic(text_en)
        
        # 2. Process English
        brief_html_en = markdown.markdown(text_en, extensions=['extra', 'smarty'])
        # Post-process English
        source_pattern = r'\[Source:\s*(https?://[^\s\]]+)\]'
        brief_html_en = re.sub(source_pattern, r'<a href="\1" target="_blank" class="source-link">RESEARCH SOURCE</a>', brief_html_en)
        brief_html_en = re.sub(r'(<table>.*?</table>)', r'<div class="table-wrapper">\1</div>', brief_html_en, flags=re.DOTALL)
        brief_html_en = brief_html_en.replace('[ACTION NEEDED]', '<span class="action-needed">[ACTION NEEDED]</span>')
        
        # 3. Process Arabic
        if text_ar:
            brief_html_ar = markdown.markdown(text_ar, extensions=['extra', 'smarty'])
            # Post-process Arabic (Same patterns, adapted if needed, but keeping simple for now)
            brief_html_ar = re.sub(source_pattern, r'<a href="\1" target="_blank" class="source-link">RESEARCH SOURCE</a>', brief_html_ar)
            brief_html_ar = re.sub(r'(<table>.*?</table>)', r'<div class="table-wrapper">\1</div>', brief_html_ar, flags=re.DOTALL)
            # Arabic Action Needed might be different if translated, but let's assume specific tag if consistent or rely on span class if regex matches
            # Ideally the translator acts on [ACTION NEEDED], but let's leave colorization for standard tag or specific Arabic phrase if known.
            # For now, we apply standard highlighting to the English tag if present, or we can update regex to catch Arabic equivalent if we knew it.
            # Assuming translator keeps [ACTION NEEDED] or translates it. Let's just wrap tables and links.

    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Medoas Executive Intelligence | {report_date}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=JetBrains+Mono:wght@400;700&family=Noto+Kufi+Arabic:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #0d0d0f;
            --card-bg: #16161a;
            --accent: #00f2ff;
            --text-main: #e1e1e6;
            --text-dim: #a1a1aa;
            --border: #2a2a2e;
            --h-color: #ffffff;
            --link-hover: #70f9ff;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            background-color: var(--bg);
            color: var(--text-main);
            font-family: 'Inter', sans-serif;
            line-height: 1.7;
            overflow-x: hidden;
        }}
        
        .ar-font {{
            font-family: 'Noto Kufi Arabic', sans-serif !important;
        }}

        .container {{
            max-width: 850px;
            margin: 0 auto;
            padding: 60px 24px;
        }}

        header {{
            text-align: left;
            margin-bottom: 60px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }}
        
        .header-content {{
            flex: 1;
        }}
        
        .lang-toggle {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border);
            color: var(--accent);
            padding: 8px 16px;
            border-radius: 8px;
            font-family: 'JetBrains Mono', monospace;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 0.8rem;
            margin-left: 20px;
        }}
        
        .lang-toggle:hover {{
            background: rgba(0, 242, 255, 0.1);
            border-color: var(--accent);
        }}

        h1 {{
            font-weight: 800;
            font-size: 2.2rem;
            letter-spacing: -0.04em;
            text-transform: uppercase;
            color: var(--h-color);
            margin-bottom: 8px;
        }}

        .status-line {{
            display: flex;
            align-items: center;
            gap: 15px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            color: var(--accent);
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }}

        .report-meta {{
            margin-top: 20px;
            font-size: 0.9rem;
            color: var(--text-dim);
        }}

        .brief-content {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            display: none; /* Hidden by default, toggled via JS */
        }}
        
        .brief-content.active {{
            display: block;
        }}
        
        /* RTL Support */
        .rtl {{
            direction: rtl;
            text-align: right;
        }}
        
        .rtl .brief-content li {{
            padding-left: 0;
            padding-right: 20px;
        }}
        
        .rtl .brief-content li::before {{
            left: auto;
            right: 0;
            content: "←"; 
        }}
        
        .rtl th {{
            text-align: right;
        }}

        /* Markdown Styling */
        .brief-content h2 {{
            color: var(--accent);
            font-size: 1.4rem;
            margin: 35px 0 15px 0;
            border-bottom: 1px solid #333;
            padding-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .brief-content h2:first-child {{
            margin-top: 0;
        }}

        .brief-content h3 {{
            color: #fff;
            font-size: 1.1rem;
            margin: 25px 0 10px 0;
        }}

        .brief-content p {{
            margin-bottom: 15px;
            color: var(--text-main);
        }}

        .brief-content ul {{
            margin-bottom: 25px;
            list-style-type: none;
        }}

        .brief-content li {{
            margin-bottom: 12px;
            padding-left: 20px;
            position: relative;
        }}

        .brief-content li::before {{
            content: "→";
            position: absolute;
            left: 0;
            color: var(--accent);
            font-weight: bold;
        }}

        .brief-content strong {{
            color: #fff;
            font-weight: 600;
        }}

        .action-needed {{
            color: #ff4b4b !important;
            font-weight: 700 !important;
            background: rgba(255, 75, 75, 0.1);
            padding: 2px 4px;
            border-radius: 4px;
        }}

        .source-link {{
            display: inline-block;
            margin-left: 10px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.65rem;
            color: var(--accent);
            text-decoration: none;
            border: 1px solid var(--accent);
            padding: 1px 10px;
            border-radius: 4px;
            transition: all 0.2s ease;
            vertical-align: middle;
        }}

        .source-link:hover {{
            background: var(--accent);
            color: var(--bg);
            box-shadow: 0 0 10px var(--accent);
        }}

        .copy-btn {{
            cursor: pointer;
            margin-left: 8px;
            background: #222;
            border: 1px solid #444;
            color: #888;
            font-size: 0.6rem;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'JetBrains Mono', monospace;
            transition: all 0.2s ease;
            vertical-align: middle;
        }}

        .copy-btn:hover {{
            background: #444;
            color: #fff;
        }}

        .brief-content li {{
            margin-bottom: 12px;
            padding-left: 20px;
            position: relative;
            cursor: default;
        }}
        
        /* Highlight focus when hovering over a list item */
        .brief-content li:hover {{
            background: rgba(255, 255, 255, 0.02);
            border-radius: 4px;
        }}

        /* Table Styling */
        .table-wrapper {{
            width: 100%;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            margin: 25px 0;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border);
        }}

        .brief-content table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
            min-width: 600px; /* Force scroll on small screens */
        }}

        .brief-content th {{
            background: rgba(0, 242, 255, 0.1);
            color: var(--accent);
            text-align: left;
            padding: 12px 15px;
            font-family: 'JetBrains Mono', monospace;
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
            border-bottom: 1px solid var(--border);
            white-space: nowrap;
        }}

        .brief-content td {{
            padding: 12px 15px;
            border-bottom: 1px solid var(--border);
            color: var(--text-main);
        }}

        .brief-content tr:last-child td {{
            border-bottom: none;
        }}

        .brief-content tr:hover {{
            background: rgba(255, 255, 255, 0.03);
        }}

        footer {{
            text-align: center;
            margin-top: 80px;
            padding-top: 40px;
            border-top: 1px solid var(--border);
            color: var(--text-dim);
            font-size: 0.8rem;
            font-family: 'JetBrains Mono', monospace;
        }}

    </style>
    <script>
        function copyText(btn, text) {{
            navigator.clipboard.writeText(text).then(() => {{
                const original = btn.innerText;
                btn.innerText = 'COPIED!';
                btn.style.color = '#00ff00';
                setTimeout(() => {{
                    btn.innerText = original;
                    btn.style.color = '#888';
                }}, 2000);
            }});
        }}
        
        function toggleLanguage() {{
            const enDiv = document.getElementById('brief-en');
            const arDiv = document.getElementById('brief-ar');
            const btn = document.getElementById('lang-btn');
            const header = document.querySelector('header');
            
            if (enDiv.classList.contains('active')) {{
                // Switch to Arabic
                enDiv.classList.remove('active');
                arDiv.classList.add('active');
                btn.innerText = 'SWITCH TO ENGLISH';
                document.body.classList.add('rtl');
                header.classList.add('rtl');
            }} else {{
                // Switch to English
                enDiv.classList.add('active');
                arDiv.classList.remove('active');
                btn.innerText = 'النسخة العربية (ARABIC)';
                document.body.classList.remove('rtl');
                header.classList.remove('rtl');
            }}
        }}
    </script>
</head>
<body>
    <div class="container">
        <header>
            <div class="header-content">
                <div class="status-line">
                    <span style="display: flex; align-items: center;"><span style="width: 8px; height: 8px; background: #00ff00; border-radius: 50%; display: inline-block; margin-right: 8px;"></span> SYSTEM ACTIVE</span>
                    <span>// EXECUTIVE BRIEFING MODE</span>
                </div>
                <h1>Medoas Intelligence</h1>
                <p class="report-meta">Factual synthesis of Markets, Technology, and Macroeconomics for <strong>{report_date}</strong>.</p>
            </div>
            <button id="lang-btn" class="lang-toggle" onclick="toggleLanguage()">النسخة العربية (ARABIC)</button>
        </header>

        <main>
            <div class="brief-content active" id="brief-en">
                {brief_html_en if brief_html_en else '<div class="empty-state">No executive intelligence generated for today yet. Waiting for end-of-day synthesis...</div>'}
            </div>
            
            <div class="brief-content ar-font" id="brief-ar">
                {brief_html_ar if brief_html_ar else '<div class="empty-state">جارٍ إعداد الترجمة... (Translation pending)</div>'}
            </div>
            
            <script>
                // Add copy buttons to all list items after Markdown rendering (English)
                document.querySelectorAll('#brief-en li').forEach(li => {{
                    const btn = document.createElement('button');
                    btn.className = 'copy-btn';
                    btn.innerText = 'COPY';
                    const cleanText = li.innerText.replace('COPIED!', '').replace('COPY', '').trim();
                    btn.onclick = (e) => {{
                        e.stopPropagation();
                        copyText(btn, cleanText);
                    }};
                    li.appendChild(btn);
                }});
            </script>
        </main>

        <footer>
            <p>GENERATED BY MEDOAS PIPELINE v2.0 // {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
            <p style="margin-top: 10px; font-size: 0.7rem; color: #444;">OBJECTIVE ANALYSIS. NO SPECULATION. NO PROPAGANDA.</p>
        </footer>
    </div>
</body>
</html>
    """
    
    with open(OUTPUT_PATH, "w") as f:
        f.write(html_template)
    print(f"Successfully generated {OUTPUT_PATH}")

if __name__ == "__main__":
    generate_html()
