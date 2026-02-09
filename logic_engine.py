import os
import requests
import json
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="/root/daily_brief/.env")

class LogicEngine:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def assess_relevance(self, title, summary):
        """
        The Bouncer: Filter out news irrelevant to the portfolio.
        """
        system_prompt = """
You are the Gatekeeper for a high-level intelligence briefing.
Your job: Filter out noise, clickbait, and irrelevant news.
Keep ONLY items related to:
1. Breakthrough Battery Tech (Solid State, Sodium-Ion, Anode/Cathode physics).
2. AGI/ASI milestones & significant AI architectural shifts (OAI, Anthropic, xAI, Meta).
3. Crypto Market Structure shifts (ETF flows, sovereign adoption, major regulatory moves).
4. Geopolitical events DIRECTLY impacting supply chains or energy (Oil, TASI, US/China).
5. Data Centers & AI Infrastructure.

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
            # Fail closed on errors to save tokens/processing
            return False 

    def analyze(self, text, previous_context=None):
        """
        The Deep Dive: Extract signal from noise for individual items.
        """
        system_prompt = """
You are a Deep Intelligence Analyst.
Goal: Extract signal from noise. MAXIMUM DENSITY.
Do not summarize. ANALYZE.

Directives:
1. STRIP the Narrative. What actually happened?
2. SECOND-ORDER EFFECTS: If X happened, what breaks?
3. DENSITY: Use compressed language. No fluff.

Output Format (Bullet points):
* [FACT]: The raw, unadorned event.
* [IMPLICATION]: The immediate result.
* [SIGNAL]: The deep market/strategic key.
"""
        messages = [
            {"role": "system", "content": system_prompt},
        ]
        
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
        """
        The Commander: Global synthesis for the daily wrap.
        """
        system_prompt = """
# SYSTEM: EXECUTIVE BRIEFING MODE // THE COMMANDER
# IDENTITY: Medoas Intelligence Senior Strategic Analyst.
# GOAL: Factual synthesis of Markets, Technology, and Macroeconomics. 
# GUIDELINE: Provide 500-1000 words of COLD, USEFUL intelligence. No fluff. No bias.

## OUTPUT STRUCTURE (STRICT ADHERENCE):

1. **EXECUTIVE SYNTHESIS**
   - 150-200 words summarizing the exact state of the environment.
   - Define the "Regime" (e.g., High-Entropy, Power Player Volatility). 
   - Identify the core Macro Driver.
   - Define CURRENT RISK POSTURE: [Defensive / Cautious / Aggressive]

2. **PORTFOLIO GUIDANCE (V6)**
   Generate a specific Markdown table based on the signals:
   | Asset Class | Allocation % | Stance | Rationale |
   | :--- | :--- | :--- | :--- |
   (Include Crypto, Equities, Energy, Cash, Frontier Tech)

3. **BEST RETURN-TO-RISK SECTOR ALLOCATION**
   List 5 specific sectors with [XX%] weights.
   Format: **Sector Name [XX%]**: [Rationale explaining the edge].

4. **“OLD STAND” VERDICT**
   Mark as: Fully Valid / Partially Valid / Invalidated
   - Note what changed and why since the previous assessment.

5. **ACTIONABLE IF/THEN LOOP**
   - List 5-7 strictly conditional triggers.
   - Format: - IF [Specific Event] THEN [Specific Action].

6. **AI ANALYSIS (DEEP DIVE)**
   - 300-500 words of cross-asset analysis. 
   - Explain how the breakthroughs (e.g., Sodium-Ion, OAI models) are disrupting the macro landscape.
   - Identify "Black Swan" vulnerabilities.
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Synthesize today's recon pulses into the Commander Brief:\n{content}"}
        ]

        payload = {
            "model": "google/gemini-2.0-flash-001",
            "messages": messages,
            "temperature": 0.2
        }

        try:
            response = requests.post(self.url, headers=self.headers, data=json.dumps(payload))
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"Error generating wrap: {e}")
            return None

    def translate_to_arabic(self, text):
        """
        High-fidelity translation for the Arabic dashboard section.
        """
        system_prompt = """
You are a top-tier Arabic translator specialized in financial and geopolitical intelligence.
Translate the following executive brief into formal, professional Arabic (MSA).
Ensure technical terms (e.g., "High-Entropy", "Frontier Tech", "If/Then Loop") are translated accurately for a senior executive.
Preserve the Markdown structure (tables, headers, bold text).
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Translate this brief:\n{text}"}
        ]
        
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
            print(f"Error in translation: {e}")
            return None
