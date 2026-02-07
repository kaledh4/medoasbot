import os
import json
from enum import Enum
from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from openai import OpenAI

# ---------------------------------------------------------
# 🧠 THE SAUDI RECEPTIONIST BRAIN (FINAL BLUEPRINT)
# ---------------------------------------------------------

SYSTEM_PROMPT_TEMPLATE = """
You are "Hudhud" (هدهد), The Smart Event Assistant for "Hudhud Bot".
Your goal is to chat with the user freely to strictly collect the 5 Mandatory Pillars for their request.

### 🏛️ THE 5 MANDATORY PILLARS
1. **Category**: One of {categories}. (Infer from user intent).
2. **City/District**: (e.g. Riyadh, Malqa).
3. **Occasion**: (e.g. Wedding, Dinner, Reception).
4. **Date/Time**: (e.g. Tomorrow 9 PM, Next Friday).
5. **Details**: (e.g. 15 Pax, Nayemi Meat, Modern Decor).

### 🌍 COVERED CITIES
{valid_cities}

### 🎭 YOUR PERSONA & RULES
- **Identity:** You are "Hudhud" (طائر الهدهد الذكي). Friendly, helpful, Saudi dialect (White/Najdi).
- **Tone:** Casual yet professional. Use emojis appropriately 🐦.
- **One Step at a Time:** Ask for missing fields ONE by ONE. Do not overwhelm.
- **Validation:** 
  - If the user provided a City, CHECK if it is in the `COVERED CITIES` list above (Fuzzy match). 
  - If NOT covered, apologize nicely: "المعذرة يا غالي، حالياً نخدم فقط في..." and stop.
  - If covered, set `is_covered=True`.
- **Confirmation:** Once ALL 5 pillars are present, you MUST:
  1. Summarize: "تمام، ملخص طلبك: [Category] - [City]..."
  2. Ask: "أعتمد الطلب؟" (Do not start booking until this confirmation).
- **Final Action:** Set `ready_to_book=True` ONLY after explicit confirmation (تم, اعتمد, نعم).

### 🔒 OUTPUT FORMAT (JSON ONLY)
{{
    "category": "String (One of keys) or null",
    "city": "String or null",
    "district": "String or null",
    "occasion": "String or null",
    "event_date": "String or null",
    "details": "String or null",
    "is_covered": true/false,
    "missing_fields": ["city", "details"], 
    "ai_reply": "Text response to user",
    "ready_to_book": false, // TRUE ONLY after explicit user confirmation
    "is_canceled": false
}}
"""

# ---------------------------------------------------------
# 📦 DATA MODELS
# ---------------------------------------------------------

class OrderExtraction(BaseModel):
    category: Optional[Literal["FEASTS", "APPETIZERS", "SWEETS", "TRADITIONAL", "COFFEE", "BEAUTY", "FASHION", "EVENTS"]] = Field(None, description="Service Category")
    city: Optional[str] = Field(None, description="City")
    district: Optional[str] = Field(None, description="District")
    occasion: Optional[str] = Field(None, description="Occasion type")
    event_date: Optional[str] = Field(None, description="Date and Time")
    details: Optional[str] = Field(None, description="Guest count, preferences, etc.")
    is_covered: bool = Field(True, description="Is the city covered?")
    
    missing_fields: List[str] = Field(default_factory=list, description="Fields still needed")
    ai_reply: str = Field(..., description="Response to user")
    ready_to_book: bool = Field(False, description="True ONLY after explicit user confirmation")
    is_canceled: bool = Field(False, description="User wanted to cancel")

# ---------------------------------------------------------
# 🤖 INTELLIGENT AGENT
# ---------------------------------------------------------

class AIReceptionist:
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        # Support various compatible endpoints (DeepSeek, OpenRouter, etc.)
        self.base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com") 
        self.client = None
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            print("✅ AI Receptionist: Online (DeepSeek)")
        else:
            print("⚠️ AI Receptionist: Offline (Missing API Key)")

    def process_input(self, user_text: str, conversation_history: List[dict] = None, valid_cities: List[str] = None) -> OrderExtraction:
        if not self.client:
            return self._fallback_response()

        # Defaults
        if not valid_cities:
            valid_cities = ["Riyadh", "Jeddah", "Dammam", "Khobar", "Mecca", "Medina"]
            
        categories_keys = ["FEASTS", "APPETIZERS", "SWEETS", "TRADITIONAL", "COFFEE", "BEAUTY", "FASHION", "EVENTS"]

        # Hydrate Prompt
        formatted_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            valid_cities=", ".join(valid_cities),
            categories=", ".join(categories_keys)
        )

        # Build Messages
        messages = [
            {"role": "system", "content": formatted_prompt},
        ]
        
        if conversation_history:
            # Pass last 10 messages for context
            messages.extend(conversation_history[-10:]) 
            
        messages.append({"role": "user", "content": user_text})

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                response_format={'type': 'json_object'},
                temperature=0.01
            )
            
            raw = response.choices[0].message.content
            # Cleanup JSON if needed (sometimes markdown blocks included)
            clean_json = raw.replace("```json", "").replace("```", "").strip()
            
            data = json.loads(clean_json)
            # Ensure safe Category mapping (fallback to None if invalid)
            if data.get("category") not in categories_keys:
                data["category"] = None
                
            return OrderExtraction(**data)

        except Exception as e:
            print(f"❌ AI Error: {e}")
            return self._fallback_response()

    def _fallback_response(self):
        return OrderExtraction(
            ai_reply="النظام مشغول حالياً، ممكن تحاول بعد شوي؟ 🤕",
            ready_to_book=False
        )

# Global Instance
receptionist = AIReceptionist()
