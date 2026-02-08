import os
import requests
import json

class LogicEngine:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.url = "https://openrouter.ai/api/v1/chat/completions"
        self.system_prompt = """
You are a Media Analyst with a 100% cynicism setting. Your job is to strip away the 'Narrative Layer.'
* Identify the 'Linguistic Trap': Point out emotional adjectives (e.g., 'stunning', 'dark') used to manipulate.
* Omission Check: Note what isn't being said (e.g., historical context or opposing viewpoints).
* The 'Who Benefits' Test: Identify the likely entity funding or benefiting from this specific framing.
* Tone: Output ONLY in 'Toon Phrases'—snappy, character-driven, street-smart dialogue. No JSON, no formal reports.
"""

    def analyze(self, text, previous_context=None):
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        if previous_context:
            context_str = "\n".join(previous_context)
            messages.append({"role": "user", "content": f"Here is what we said earlier:\n{context_str}\n\nHow does this new info change the story?"})
        
        messages.append({"role": "user", "content": f"Analyze this:\n{text}"})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/OpenClaw/OpenClaw", # Required by OpenRouter
            "X-Title": "Daily Brief Analyst"
        }
        
        payload = {
            "model": "google/gemini-2.0-flash-001", # GLM-4 is not ubiquitous, Gemini 2.0 Flash is fast and cheap
            "messages": messages
        }

        try:
            response = requests.post(self.url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"Error in LogicEngine: {e}")
            return None

    def generate_executive_brief(self, content):
        system_prompt = """
You are Medoas Intelligence's senior analyst. Transform the raw intelligence brief into "The Commander" executive decision format.

OUTPUT REQUIREMENTS:

1. EXECUTIVE SYNTHESIS (top of page)
   - 2-3 sentence market state assessment
   - Clear risk posture: Defensive/Cautious/Transitional/Aggressive
   - Key macro driver (rate path, geopolitics, liquidity, volatility)

2. PORTFOLIO GUIDANCE (V6)
   Generate specific allocation percentages based on:
   - Crypto signals: BTC dominance, ETH strength, accumulation patterns
   - Metals: Gold stability, inflation signals
   - Equities: Sector rotation signals, VIX levels
   - Frontier: AI breakthrough frequency, tech disruption pace
   
   Format as a Markdown table:
   | Asset Class | Allocation | Stance | Rationale |
   | :--- | :--- | :--- | :--- |

3. BEST RETURN-TO-RISK SECTOR ALLOCATION
   Rank top 4-5 sectors with percentages based on:
   - TASI data (Saudi regional strength)
   - Oil/energy signals
   - Banking (rate path sensitivity)
   - Crypto dominance patterns
   - AI/tech breakthrough pace

4. "OLD STAND" VERDICT
   Compare today's guidance to previous day's allocation (if context provided)
   - Mark as: Fully Valid / Partially Valid / Invalidated
   - Note what changed and why

5. ACTIONABLE IF/THEN LOOP
   Extract 4-6 conditional triggers from the brief:
   IF [market condition] THEN [specific action]
   Examples:
   - IF VIX >= 20 THEN maintain defensive posture
   - IF BTC.D < 55% THEN rotate to BTC-heavy
   - IF oil strength + TASI outperformance THEN overweight energy

6. AI ANALYSIS (2-3 paragraphs)
   Synthesize the brief into:
   - Current market regime
   - Cross-asset implications
   - Tactical positioning logic
   - Key risks to watch

ANALYSIS RULES:
- Be decisive, not speculative
- Every allocation must trace to data points in the brief
- Flag [ACTION NEEDED] items as "under surveillance"
- Ignore incomplete data points (don't guess)
- Use military/tactical language (hold, rotate, overweight, defensive)
- Default to "no change" if data is insufficient

TONE: Confident. Operational. No hedging language like "may" or "could". This is command guidance.
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the raw intelligence feed for today:\n\n{content}"}
        ]
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "google/gemini-2.0-flash-001",
            "messages": messages
        }

        try:
            response = requests.post(self.url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"Error in Executive Brief generation: {e}")
            return None

    def translate_to_arabic(self, text):
        system_prompt = """
You are a senior translator for Medoas Intelligence. Translate the following "Commander" Executive Brief into professional Arabic.

REQUIREMENTS:
1. **RTL Format**: Ensure the output is optimized for Right-to-Left reading.
2. **Tone**: Maintain the "Command/Military" tone. Use decisive, high-level business/military Arabic (e.g., instead of "cautious", use "حذر استراتيجي"; for "overweight", use "زيادة الوزن الاستثماري").
3. **Accuracy**: Keep all numbers, percentages, and financial terms accurate.
4. **Structure**: Preserve the exact Markdown structure (Headings, Tables, Lists).
5. **Terminology**:
    - "Executive Synthesis" -> "الموجز التنفيذي"
    - "Portfolio Guidance" -> "توجيهات المحفظة الاستثمارية"
    - "Risk Posture" -> "موقف المخاطر"
    - "Actionable IF/THEN Loop" -> "حلقة الاشتراطات التنفيذية (إذا/ثم)"
    - "Old Stand Verdict" -> "حكم الموقف السابق"
    
Output ONLY the Arabic translation in Markdown.
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Translate this brief:\n\n{text}"}
        ]
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "google/gemini-2.0-flash-001",
            "messages": messages
        }

        try:
            response = requests.post(self.url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"Error in Arabic translation: {e}")
            return None
