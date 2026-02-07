import os
import json
import asyncio
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# THE "BRAIN" SYSTEM PROMPT (Real) - Defined at module level
SYSTEM_PROMPT = """
You are "Eventak Core," an advanced AI agent for a Saudi event marketplace.

YOUR GOAL:
Analyze incoming messages, extract specific entities (Slots), and ensure the request is COMPLETE before processing.

### 1. CORE SLOTS (The 5 Pillars)
Extract these strict fields:

| Slot | Description | Critical? |
| :--- | :--- | :--- |
| `service_category` | [CATERING, PHOTOGRAPHY, VENUES, BEAUTY, ENTERTAINMENT, ORGANIZATION] | YES |
| `location` | City and Neighborhood (e.g., Riyadh, Al-Malqa) | YES |
| `date` | Date/Time (e.g., Next Friday, 8 PM) | YES |
| `scope` | Quantity (e.g., 50 people, 3 sheep) | NO |
| `budget` | Price range | NO |

### 2. OUTPUT JSON STRUCTURE (Strict)
{
  "intent": "NEW_REQUEST", 
  "service_category": "CATERING",
  "location": "Riyadh",
  "date": "Unknown",
  "details": "User message...",
  "missing_info": ["date"], 
  "reply_message": "أبشر! بس متى المناسبة؟" 
}

### 3. BEHAVIOR RULES
1. **SLOT FILLING MODE (Critical)**:
   - **User Input:** "الرياض" -> **Output:** `{"location": "Riyadh"}`
   - **User Input:** "يوم الجمعة" -> **Output:** `{"date": "Next Friday"}`
   - **User Input:** "الرياض يوم الجمعة" -> **Output:** `{"location": "Riyadh", "date": "Next Friday"}`
   - **User Input:** "ابغى قهوجي" -> **Output:** `{"service_category": "CATERING"}` (plus blanks)
2. If `missing_info` is NOT empty:
   - `reply_message` MUST ask specifically for the missing pieces.
   - **CRITICAL**: Append the missing slots to the message for debugging. e.g. "وين المكان؟ (Missing: location)".
3. If `missing_info` is EMPTY:
   - `reply_message`: "تم استلام الطلب! (All Slots Filled)"

### 4. OUTPUT FORMAT
Strict JSON only.
"""



class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = None
        
        if not self.api_key:
            print("⚠️ GEMINI_API_KEY not found. AI will fail.")
        else:
            genai.configure(api_key=self.api_key)
            print("✅ Gemini AI Configured. Detecting Best Model...")
            self.model_name = self._discover_best_model()

        # Configuration
        self.generation_config = {
            "temperature": 0.3, 
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 1024,
            "response_mime_type": "application/json",
        }

    def _discover_best_model(self):
        """
        PRODUCTION GRADE DISCOVERY
        Active test of models to ensure they work.
        """
        candidates = [
            "models/gemini-1.5-flash",
            "models/gemini-1.5-pro",
            "models/gemini-pro"
        ]

        print("🔎 Testing AI Models...")
        for model_id in candidates:
            try:
                # Live Fire Test
                model = genai.GenerativeModel(model_id)
                response = model.generate_content("hi")
                if response:
                    print(f"🚀 LOCKED WORKING MODEL: {model_id}")
                    return model_id
            except Exception as e:
                print(f"⚠️ Test Failed {model_id}: {e}")
        
        print("❌ ALL MODELS FAILED. AI will be disabled.")
        return None


    async def classify_intent(self, text: str) -> dict:
        return {"intent": "NEW_REQUEST", "confidence": 1.0} 

    async def extract_entities(self, text: str) -> dict:
        if not self.api_key:
            return self._mock_fallback(text, "MISSING_API_KEY")

        # Use the ONE determined production model
        print(f"🤖 Processing with Locked Model: {self.model_name}")

        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=SYSTEM_PROMPT
            )
            
            response = await model.generate_content_async(
                text, 
                generation_config=self.generation_config
            )

            raw_json = response.text
            try:
                data = json.loads(raw_json)
                print(f"🧠 Gemini Output: {data}")
                
                # Production Debug Tag
                debug_str = f"\n(AI Valid: {data.get('location')}/{data.get('date')} | M: {self.model_name.split('/')[-1]})"
                # if data.get("reply_message"):
                #     data["reply_message"] += debug_str
                
                return data
            except json.JSONDecodeError:
                print(f"⚠️ Failed to parse Gemini JSON: {raw_json}")
                return self._mock_fallback(text, f"JSON_ERROR")
                
        except Exception as e:
            print(f"❌ Gemini Fatal Error: {e}")
            return self._mock_fallback(text, f"FATAL_ERROR: {str(e)[:50]}")

    # EVENTAK CONSTITUTION (The Brain)
    EVENTAK_BRAIN = """
    ### الهوية والدور:
    أنت "مساعد إيفنتك" (Eventak AI)، المسؤول الذكي عن التحقق من طلبات العملاء في منصة تربط "الأسر المنتجة" بالعملاء في السعودية.
    أنت لست مجرد مدقق بيانات، أنت مساعد خبير، لبق، وتتحدث باللهجة السعودية البيضاء (نبرة ودودة، محترمة، وخدومة).

    ### المهمة الأساسية:
    ستستقبل مدخلات من العميل (مثل: الموقع، التاريخ، تفاصيل الطلب)، وعليك تحليلها:
    1. هل هي مفهومة؟
    2. هل هي منطقية؟
    3. هل هي كاملة وتسمح للأسرة المنتجة بتقديم عرض سعر؟

    ### قواعد التحقق الصارمة (Business Rules):

    1. **الموقع (Location):**
    - مقبول: أي مدينة أو حي أو معلم معروف داخل السعودية (مثال: الرياض حي الملقا، جدة شارع التحلية، الدمام).
    - مرفوض: الكلمات العامة جداً (البيت، عندي، موقعي، هنا)، أو الأسماء الوهمية، أو أماكن خارج السعودية.

    2. **التاريخ والوقت (Date/Time):**
    - مقبول: أي توقيت في المستقبل (مثال: بكرة العشاء، الخميس الجاي، 15 رمضان).
    - مرفوض: التواريخ الماضية، أو العبارات غير الزمنية (مثال: "بسرعة"، "الآن" إذا لم يحدد الوقت).

    3. **تفاصيل الطلب (Order Details):**
    - السياق: تذكر أننا نخدم (ولائم، أسر منتجة، توزيعات، ضيافة).
    - مقبول: وصف واضح للكمية والنوع (مثال: "ذبيحتين نعيمي"، "بوكس ورق عنب 50 حبة"، "قهوجيات عدد 2").
    - مرفوض:
        - الكلام العشوائي (نوم، تجربة، .، هلا).
        - الطلبات المستحيلة أو الممنوعة (خمور، شيشة، تعارف).
        - الطلبات الناقصة جداً (كلمة "أكل" فقط، أو "ذبيحة" بدون عدد أو نوع).

    ### أسلوب الرد (في حالة الرفض):
    - لا تقل "خطأ" أو "غير صحيح".
    - استخدم أسلوب "التوضيح اللطيف".
    - مثال للرفض: "معليش يا غالي، ما فهمت وين الموقع بالضبط؟ ياليت تزودني باسم الحي والمدينة عشان نخدمك صح 🌹".

    ### صيغة المخرجات (Output Format):
    يجب أن ترد دائماً بصيغة JSON فقط، بدون أي مقدمات:
    {
    "valid": true | false,
    "reason": "رسالة الرد المقترحة للعميل (تترك فارغة إذا كان الطلب صحيحاً)",
    "corrected_value": " (اختياري) إذا قام العميل بكتابة التاريخ بشكل عام، قم بتنسيقه هنا (مثال: إذا قال العميل 'بكرة' صححها لـ 'غداً')"
    }
    """

    async def validate_input_guard(self, text: str, field_type: str) -> dict:
        """
        Validates user input using Gemini 1.5 Flash with the Eventak Constitution.
        field_type: 'LOCATION', 'DATE', 'DETAILS'
        Returns: {"valid": bool, "reason": str | None, "corrected_value": str | None}
        """
        if not self.api_key or not self.model_name:
            print("⚠️ GUARD SKIPPED: Missing API Key or Model Name. Allowing input.")
            # Fail open if AI is down (don't block user)
            return {"valid": True, "reason": None}

        full_prompt = f"""
        {self.EVENTAK_BRAIN}
        
        --- طلب فحص جديد ---
        نوع الحقل: {field_type}
        مدخل العميل: "{text}"
        
        النتيجة (JSON):
        """

        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={"response_mime_type": "application/json"}
            )
            
            response = await model.generate_content_async(full_prompt)
            data = json.loads(response.text)
            print(f"🛡️ Guard Check ({field_type}): {data}")
            return data

        except Exception as e:
            print(f"⚠️ Guard Check Failed: {e}")
            return {"valid": True, "reason": None}

    def _mock_fallback(self, text: str, debug_error=""):
        return {
            "intent": "NEW_REQUEST",
            "service_category": "Unknown",
            "location": "Unknown",
            "date": "Unknown",
            "missing_info": ["service_category"],
            "reply_message": "عذراً، النظام يواجه ضغط تقني. الرجاء المحاولة لاحقاً."
        }

# Singleton instance - Discovery runs immediately on import
gemini_service = GeminiService()
