import sqlite3
import os
from datetime import datetime
import markdown
import re

from dotenv import load_dotenv

# Load environment variables (for translation)
load_dotenv(dotenv_path="/root/daily_brief/.env")

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
    
    # Get mentions for the report date
    mentions = []
    if daily_wrap:
        report_date = daily_wrap[0]
        cursor.execute("SELECT source, analysis_toon_phrase, url, timestamp FROM mentions WHERE date(timestamp) = ? ORDER BY timestamp DESC", (report_date,))
        mentions = cursor.fetchall()
    
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
        brief_html_en = re.sub(r'propaganda', 'narrative control', brief_html_en, flags=re.IGNORECASE)
        
        # 3. Process Arabic
        if text_ar:
            # Strip markdown code fences if the LLM wrapped it
            text_ar_clean = text_ar.strip()
            if text_ar_clean.startswith('```markdown'):
                text_ar_clean = text_ar_clean[len('```markdown'):].strip()
            if text_ar_clean.startswith('```'):
                text_ar_clean = text_ar_clean[3:].strip()
            if text_ar_clean.endswith('```'):
                text_ar_clean = text_ar_clean[:-3].strip()
            
            brief_html_ar = markdown.markdown(text_ar_clean, extensions=['extra', 'smarty', 'tables'])
            # Post-process Arabic
            brief_html_ar = re.sub(source_pattern, r'<a href="\1" target="_blank" class="source-link">RESEARCH SOURCE</a>', brief_html_ar)
            brief_html_ar = re.sub(r'(<table>.*?</table>)', r'<div class="table-wrapper">\1</div>', brief_html_ar, flags=re.DOTALL)

        # 4. Generate Intelligence Stream HTML
        stream_html = ""
        for source, analysis, url, ts in mentions:
            # Convert analysis markdown to HTML first
            # Use 'extra' for better handling of specialized markdown if needed
            analysis_html = markdown.markdown(analysis, extensions=['extra', 'smarty'])
            
            # Robust tag replacement: handles naked [FACT], bolded **[FACT]**, and parsed <strong>[FACT]</strong>
            # Also clears trailing colons and ensures the labels are clean inside the dossier cards
            tag_patterns = {
                r'(\*\*|<strong>)?\s*\[FACT\]:?\s*(\*\*|</strong>)?': '<span class="intel-label fact">FACT</span>',
                r'(\*\*|<strong>)?\s*\[IMPLICATION\]:?\s*(\*\*|</strong>)?': '<span class="intel-label impl">IMPLICATION</span>',
                r'(\*\*|<strong>)?\s*\[SIGNAL\]:?\s*(\*\*|</strong>)?': '<span class="intel-label signal">SIGNAL</span>'
            }
            
            for pattern, replacement in tag_patterns.items():
                analysis_html = re.sub(pattern, replacement, analysis_html, flags=re.IGNORECASE)
            
            # Final cleanup of common LLM artifacts
            analysis_html = analysis_html.replace('**', '').replace('__', '')
            
            source_link = f' <a href="{url}" target="_blank" class="source-link">ORIGIN</a>' if url else ""
            
            stream_html += f"""
            <div class="intel-pulse">
                <div class="intel-header">
                    <div class="header-meta-group">
                        <span class="pulse-ts">{ts}</span>
                        <span class="pulse-source">REF: {source}</span>
                    </div>
                    {source_link}
                </div>
                <div class="intel-content dossier-style">{analysis_html}</div>
            </div>
            """
        
        # If no wrap but mentions exist, handle that (though wrap is priority)
        if not mentions:
            stream_html = '<div class="empty-state">No pulses captured for this reporting period.</div>'

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
            vertical-align: top;
        }}
        
        /* Force Rationale column to wrap */
        .brief-content td:last-child {{
            white-space: normal;
            min-width: 200px;
            max-width: 350px;
            word-wrap: break-word;
            line-height: 1.5;
        }}

        .brief-content tr:last-child td {{
            border-bottom: none;
        }}

        .brief-content tr:hover {{
            background: rgba(255, 255, 255, 0.03);
        }}

        /* Intelligence Stream Styling (Premium Dossier Look) */
        .intel-stream {{
            display: grid;
            gap: 24px;
            margin-top: 30px;
        }}

        .intel-pulse {{
            background: rgba(255, 255, 255, 0.02);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(0, 242, 255, 0.08);
            border-left: 4px solid var(--accent);
            padding: 24px;
            border-radius: 12px;
            position: relative;
            transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
        }}

        .intel-pulse:hover {{
            background: rgba(255, 255, 255, 0.04);
            border-color: rgba(0, 242, 255, 0.3);
            box-shadow: 0 15px 45px rgba(0, 0, 0, 0.5), 0 0 15px rgba(0, 242, 255, 0.1);
            transform: translateY(-4px);
        }}

        .intel-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            padding-bottom: 12px;
        }}

        .header-meta-group {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}

        .pulse-ts {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.65rem;
            color: var(--accent);
            letter-spacing: 0.1em;
            background: rgba(0, 242, 255, 0.05);
            padding: 2px 8px;
            border-radius: 4px;
        }}

        .pulse-source {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.65rem;
            color: var(--text-dim);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .intel-content {{
            line-height: 1.8;
            font-size: 1rem;
            color: rgba(255, 255, 255, 0.85);
        }}

        .intel-content p {{
            margin-bottom: 16px;
        }}

        .intel-content ul {{
            margin: 15px 0;
            padding-left: 0;
            list-style: none;
        }}

        .intel-content li {{
            margin-bottom: 12px;
            padding-left: 25px !important;
            position: relative;
            font-size: 0.95rem;
        }}

        .intel-content li::before {{
            content: "•";
            position: absolute;
            left: 5px;
            color: var(--accent);
            font-weight: bold;
        }}

        .intel-label {{
            font-weight: 900;
            font-size: 0.65rem;
            font-family: 'JetBrains Mono', monospace;
            padding: 2px 10px;
            border-radius: 4px;
            margin-right: 12px;
            display: inline-block;
            vertical-align: top;
            letter-spacing: 0.15em;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }}

        .fact {{ 
            background: linear-gradient(135deg, rgba(0, 242, 255, 0.1), rgba(0, 242, 255, 0.05)); 
            color: var(--accent); 
            border: 1px solid rgba(0, 242, 255, 0.3); 
        }}
        .impl {{ 
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02)); 
            color: #eee; 
            border: 1px solid rgba(255, 255, 255, 0.1); 
        }}
        .signal {{ background: rgba(255, 75, 75, 0.15); color: #ff4b4b; border: 1px solid rgba(255, 75, 75, 0.3); }}

        /* Collapsible Recon Log Styling */
        .recon-details {{
            margin-top: 60px;
            border: 1px dashed var(--border);
            border-radius: 12px;
            overflow: hidden;
        }}

        .recon-summary {{
            padding: 20px;
            background: rgba(255, 255, 255, 0.02);
            cursor: pointer;
            list-style: none;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            color: var(--accent);
            letter-spacing: 0.2em;
            transition: background 0.2s ease;
        }}

        .recon-summary:hover {{
            background: rgba(0, 242, 255, 0.05);
        }}

        .recon-summary::-webkit-details-marker {{
            display: none;
        }}

        .intel-stream {{
            padding: 24px;
            display: grid;
            gap: 24px;
        }}

        .empty-state {{
            text-align: center;
            padding: 60px 20px;
            color: var(--text-dim);
            font-style: italic;
            border: 1px dashed var(--border);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.01);
        }}

        /* Mobile Responsive Adjustments */
        @media (max-width: 768px) {{
            .container {{
                padding: 30px 16px;
            }}
            
            header {{
                flex-direction: column;
                align-items: flex-start;
            }}
            
            h1 {{
                font-size: 1.6rem;
            }}
            
            .lang-toggle {{
                margin-left: 0;
                margin-top: 20px;
                width: 100%;
                text-align: center;
            }}
            
            .brief-content {{
                padding: 20px 16px;
            }}
            
            .brief-content h3 {{
                font-size: 1rem;
            }}
            
            .brief-content p {{
                font-size: 0.9rem;
                word-wrap: break-word;
            }}

            /* Mobile Table Cards - Complete Overhaul */
            .table-wrapper {{
                border: none;
                background: transparent;
                overflow: visible;
                margin: 15px 0;
            }}

            .brief-content table {{
                min-width: auto;
                width: 100%;
            }}
            
            .brief-content table, 
            .brief-content thead, 
            .brief-content tbody, 
            .brief-content th, 
            .brief-content td, 
            .brief-content tr {{ 
                display: block;
                width: 100%;
            }}
            
            .brief-content thead tr {{ 
                position: absolute;
                top: -9999px;
                left: -9999px;
            }}
            
            .brief-content tbody tr {{ 
                border: 1px solid var(--border);
                margin-bottom: 16px;
                border-radius: 12px;
                background: rgba(255, 255, 255, 0.03);
                padding: 16px;
                display: block;
            }}
            
            .brief-content td {{ 
                border: none;
                position: relative;
                padding: 6px 0;
                padding-left: 0 !important;
                text-align: left !important;
                display: block;
                width: 100%;
                white-space: normal;
                word-wrap: break-word;
                max-width: 100%;
                min-width: auto;
            }}
            
            /* Asset Class Name - First Column */
            .brief-content td:nth-of-type(1) {{
                font-weight: 700;
                color: var(--accent);
                font-size: 1rem;
                border-bottom: 1px solid var(--border);
                margin-bottom: 10px;
                padding-bottom: 10px;
            }}
            
            /* Allocation - Second Column */
            .brief-content td:nth-of-type(2)::before {{ 
                content: "Allocation: "; 
                color: var(--text-dim); 
                font-size: 0.75rem;
                font-weight: 400;
                display: inline;
            }}
            .brief-content td:nth-of-type(2) {{
                font-weight: 600;
                color: #fff;
            }}
            
            /* Stance - Third Column */
            .brief-content td:nth-of-type(3)::before {{ 
                content: "Stance: "; 
                color: var(--text-dim); 
                font-size: 0.75rem;
                font-weight: 400;
                display: inline;
            }}
            .brief-content td:nth-of-type(3) {{
                color: #fff;
            }}
            
            /* Rationale - Fourth Column */
            .brief-content td:nth-of-type(4) {{ 
                color: var(--text-dim); 
                font-style: italic; 
                margin-top: 8px;
                padding-top: 8px;
                border-top: 1px dashed var(--border);
                font-size: 0.85rem;
                line-height: 1.5;
            }}
            .brief-content td:nth-of-type(4)::before {{
                content: "Rationale: ";
                color: var(--text-dim);
                font-size: 0.75rem;
                font-weight: 400;
                font-style: normal;
                display: block;
                margin-bottom: 4px;
            }}
            
            /* Arabic Labels (RTL) */
            .rtl .brief-content td:nth-of-type(2)::before {{ content: "التوزيع: "; }}
            .rtl .brief-content td:nth-of-type(3)::before {{ content: "الموقف: "; }}
            .rtl .brief-content td:nth-of-type(4)::before {{ content: "الأساس المنطقي: "; }}
            
            .rtl .brief-content td {{
                text-align: right !important;
            }}
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
                
                <details class="recon-details">
                    <summary class="recon-summary">
                        <span>OPEN RECON LOG (TACTICAL STREAM)</span>
                    </summary>
                    <div class="intel-stream">
                        {stream_html}
                    </div>
                </details>
            </div>
            
            <div class="brief-content ar-font" id="brief-ar">
                {brief_html_ar if brief_html_ar else '<div class="empty-state">جارٍ إعداد الترجمة... (Translation pending)</div>'}
                
                <details class="recon-details">
                    <summary class="recon-summary">
                        <span>فتح سجل الاستطلاع (موجز تكتيكي)</span>
                    </summary>
                    <div class="intel-stream">
                        {stream_html}
                    </div>
                </details>
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
            <p style="margin-top: 10px; font-size: 0.7rem; color: #444;">OBJECTIVE ANALYSIS. NO SPECULATION. NO BIAS.</p>
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
