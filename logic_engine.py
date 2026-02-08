import os
import requests
import json

class LogicEngine:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/OpenClaw/OpenClaw",
            "X-Title": "Daily Brief Analyst"
        }

    def assess_relevance(self, title, summary):
        """
        Stage 1: The Bouncer.
        Cheap, fast check to see if this is even worth processing.
        Returns: Boolean (True/False)
        """
        system_prompt = """
You are the Gatekeeper for a high-level intelligence briefing.
Your job: Filter out noise, clickbait, and irrelevant news.
Keep ONLY items related to:
1. Breakthrough Battery Tech (Solid State, Na-Ion) in production/scaling.
2. AGI/ASI milestones & significant LLM architectural shifts (no random app releases).
3. Crypto Market Structure shifts (ETF flows, sovereign adoption, major regulatory moves).
4. Geopolitical events DIRECTLY impacting supply chains or energy.

Input: Title + Summary
Output: JSON {"keep": true/false, "reason": "short reason"}
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Title: {title}\nSummary: {summary}"}
        ]
        
        try:
            payload = {
                "model": "google/gemini-2.0-flash-001",
                "messages": messages,
                "response_format": {"type": "json_object"}
            }
            response = requests.post(self.url, headers=self.headers, data=json.dumps(payload))
            response.raise_for_status()
            result = response.json()
            content = json.loads(result['choices'][0]['message']['content'])
            return content.get("keep", False)
        except Exception:
            # Fallback: keep it if we can't decide (fail open) or log error
            return False 

    def analyze(self, text, previous_context=None):
        """
        Stage 2: The Deep Dive.
        Analyze the 'kept' items for deep implications.
        """
        system_prompt = """
You are a Deep/Covert Intelligence Analyst.
Goal: Extract signal from noise. MAXIMUM DENSITY.
Do not summarize. ANALYZE.

Directives:
1. STRIP the Narrative: Ignore "groundbreaking", "shocking". What actually happened?
2. SECOND-ORDER EFFECTS: If X happened, what breaks? Who loses?
3. FOLLOW THE MONEY: Who benefits?
4. DENSITY: Use compressed language. No fluff.

Output Format (Bullet points):
* [FACT]: The raw, unadorned event.
* [IMPLICATION]: The immediate result.
* [SIGNAL]: The deep market/strategic key.
"""

        if previous_context:
            context_str = "\n".join(previous_context)
            messages.append({"role": "user", "content": f"Context/History:\n{context_str}\n\nNew Intel to Analyze:\n{text}"})
        else:
            messages.append({"role": "user", "content": f"Analyze this intel:\n{text}"})

        payload = {
            "model": "google/gemini-2.0-flash-001",
            "messages": messages
        }

        try:
            response = requests.post(self.url, headers=self.headers, data=json.dumps(payload))
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"Error in LogicEngine: {e}")
            return None

    def generate_executive_brief(self, content):
        system_prompt = """
You are Medoas Intelligence's senior analyst. Transform the raw intelligence brief (containing [FACT], [IMPLICATION], and [SIGNAL] bullets) into "The Commander" executive decision format.

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
