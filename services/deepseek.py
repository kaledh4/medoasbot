import os
import json
from openai import OpenAI

# THE "BRAIN" SYSTEM PROMPT (Enhanced for Saudi Context & Memory)
SYSTEM_PROMPT = """
You are "Eventak Core" (نظام إيفنتك), a smart Saudi AI assistant for an event marketplace.

### 🎭 YOUR PERSONA
- **Tone:** Professional yet Friendly Saudi Dialect (لهجة سعودية بيضاء محترمة).
- **Keywords:** Use "أبشر", "سم", "ولا يهمك", "حياك الله".
- **Goal:** Help the user complete their request by asking for missing details naturally.

### 📋 1. SERVICE CATEGORIES (Expanded)
Classify the request into one of these strict codes:
| Slot | Description | Keywords (Examples) |
| :--- | :--- | :--- |
| `CATERING` | Food & Drink | بوفيه, عشاء, ذبيحة, غداء, فطور |
| `PHOTOGRAPHY` | Media | تصوير, مصورة, فيديو, زواج |
| `VENUES` | Locations | قاعة, استراحة, شاليه, فندق |
| `BEAUTY` | Makeup/Hair | ميكب, تسريحة, مشغل, كوافيرة |
| `ENTERTAINMENT` | Fun | دي جي, فرقة, مهرج |
| `ORGANIZATION` | Planning | تنظيم, كوشة, تنسيق |
| `COFFEE` | Coffee Service | قهوجي, قهوجية, صببابين, ضيافة |
| `GIFTS` | Giveaways | توزيعات, هدايا, تذكارات |
| `EQUIPMENT` | Rentals | كراسي, طاولات, خيام, سماعات |
| `OTHER` | Other | أي شيء آخر |

### 🧠 2. CONTEXT & MEMORY RULES (Critical)
You will receive "History + New Input".
- **CONFLICT RESOLUTION:** If the user provided conflicting info (e.g. Changed Location), **ALWAYS PRIORITIZE THE LATEST MESSAGE**. The user's last message overrides previous context.
- **IF** the user says "Cancel" or "Forget it", return `intent: "CANCEL"`.

### 3. OUTPUT JSON STRUCTURE
{
  "intent": "NEW_REQUEST", 
  "service_category": "CATERING", 
  "location": "الرياض - حي الملقا",
  "date": "الجمعة القادم",
  "details": "عشاء لـ 20 شخص...",
  "missing_info": ["date"], 
  "reply_message": "أبشر طال عمرك! بس متى المناسبة بالضبط؟ (عطني التاريخ والوقت)"
}

### 4. BEHAVIOR RULES
- **Language:** ALWAYS reply in **Arabic (Saudi)**.
- **Date/Location:** Extract specifically. If missing, put in `missing_info`.
- **Reply:** Must be a question asking for the `missing_info` items.
- If `missing_info` is EMPTY -> Reply: "تم استلام الطلب! (كامل المعلومات)"
"""

class DeepSeekService:
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.model_name = "deepseek-chat"
        self.client = None

        if not self.api_key:
            print("⚠️ DEEPSEEK_API_KEY not found. AI will fail.")
        else:
            print("✅ DeepSeek AI Configured.")
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com"
            )

    async def classify_intent(self, text: str) -> dict:
        return {"intent": "NEW_REQUEST", "confidence": 1.0} 

    async def extract_entities(self, text: str) -> dict:
        if not self.client:
            return self._mock_fallback(text, "MISSING_API_KEY")

        print(f"🤖 Processing with DeepSeek: {self.model_name}")

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                response_format={
                    'type': 'json_object'
                },
                temperature=0.01
            )

            raw_json = response.choices[0].message.content
            try:
                data = json.loads(raw_json)
                print(f"🧠 DeepSeek Output: {data}")
                return data
            except json.JSONDecodeError:
                print(f"⚠️ Failed to parse DeepSeek JSON: {raw_json}")
                return self._mock_fallback(text, "JSON_ERROR")
                
        except Exception as e:
            print(f"❌ DeepSeek Fatal Error: {e}")
            # Try to get more info if it's an OpenAI error
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

    ### قاعدة ذهبية (CONTEXT RULE):
    يجب أن تحكم على مدخلات العميل بناءً على "القسم المختار" في المعلومات السابقة.
    - إذا كان القسم "تصوير"، الكلمات المقبولة: (كاميرا، فيديو، ساعة، تغطية..).
    - إذا كان القسم "مأكولات"، الكلمات المقبولة: (رز، لحم، بوفيه..).
    لا تخلط بين الأقسام!

    ### صيغة المخرجات (Output Format):
    يجب أن ترد دائماً بصيغة JSON فقط، بدون أي مقدمات:
    {
    "valid": true | false,
    "reason": "رسالة الرد المقترحة للعميل (تترك فارغة إذا كان الطلب صحيحاً)",
    "corrected_value": " (اختياري) إذا قام العميل بكتابة التاريخ بشكل عام، قم بتنسيقه هنا (مثال: إذا قال العميل 'بكرة' صححها لـ 'غداً')"
    }

    ### أمثلة تدريبية (يجب القياس عليها):

    مثال 1 (رفض):
    المستخدم: "الموقع عند البقالة"
    الرد: {"valid": false, "reason": "معليش يا غالي، أي بقالة تقصد؟ عطني اسم الحي والمدينة 🌹"}

    مثال 2 (قبول):
    المستخدم: "الرياض حي النرجس"
    الرد: {"valid": true, "reason": ""}

    مثال 3 (تصحيح):
    المستخدم: "بجيكم بعد صلاة العشاء"
    الرد: {"valid": true, "corrected_value": "بعد صلاة العشاء (اليوم)"}
    """

    async def validate_input_guard(self, text: str, field_type: str, full_draft: dict = None) -> dict:
        """
        Validates user input using DeepSeek with the Eventak Constitution.
        """
        if not self.client:
            print("⚠️ GUARD SKIPPED: Missing DeepSeek API Key. Allowing input.")
            return {"valid": True, "reason": None}

        # 1. Prepare Context String
        context_str = ""
        if full_draft:
            context_str = f"""
            --- معلومات الطلب المحفوظة سابقاً (CONTEXT) ---
            - القسم المختار: {full_draft.get('category_name', 'غير محدد')}
            - المدينة/الموقع: {full_draft.get('location', 'غير محدد')}
            - التاريخ/الوقت: {full_draft.get('date', 'غير محدد')}
            ------------------------------------
            """

        full_prompt = f"""
        {context_str}
        
        --- طلب فحص جديد ---
        نوع الحقل: {field_type}
        مدخل العميل: "{text}"
        
        المطلوب:
        هل هذا المدخل منطقي ومتوافق مع "القسم المختار" ومع معلومات الطلب السابقة؟
        
        النتيجة (JSON):
        """

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": self.EVENTAK_BRAIN},
                    {"role": "user", "content": full_prompt},
                ],
                response_format={
                    'type': 'json_object'
                },
                temperature=0.01
            )

            raw_json = response.choices[0].message.content
            data = json.loads(raw_json)
            print(f"🛡️ Guard Check ({field_type}): {data}")
            return data

        except Exception as e:
            print(f"⚠️ Guard Check Failed: {e}")
            return {"valid": True, "reason": None}

    async def extract_intent(self, text: str, conversation_history: list = None) -> dict:
        """
        Extract structured intent from user message for Hudhud v2.0.
        Returns: {
            'intent': 'NEW_REQUEST' | 'CANCEL',
            'city': str,
            'category': str,
            'event_date': str,
            'details': str,
            'is_complete': bool
        }
        """
        if not self.client:
            return self._intent_fallback(text)
        
        # Build conversation context
        history_text = ""
        if conversation_history:
            history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history[-5:]])
        
        extraction_prompt = f"""
        تحليل طلب العميل واستخراج المعلومات:
        
        السياق السابق:
        {history_text}
        
        الرسالة الجديدة: "{text}"
        
        المطلوب: استخراج البيانات التالية بصيغة JSON:
        - intent: هل هو طلب جديد (NEW_REQUEST) أو إلغاء (CANCEL)؟
        - city: المدينة (مثال: الرياض، جدة، الدمام)
        - category: التصنيف بالإنجليزية من القائمة: CATERING, PHOTOGRAPHY, VENUES, BEAUTY, ENTERTAINMENT, ORGANIZATION, COFFEE, GIFTS, EQUIPMENT
        - event_date: التاريخ أو الوقت المذكور
        - details: تفاصيل الطلب الكاملة
        - is_complete: هل المعلومات كافية لإرسال الطلب للمزودين؟ (true/false)
        
        قواعد:
        - إذا قال "إلغاء" أو "cancel" → intent = "CANCEL"
        - آخر رسالة تلغي المعلومات القديمة
        - إذا ناقص معلومات → is_complete = false
        """
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "أنت مساعد ذكي لاستخراج معلومات الطلبات. أجب بـ JSON فقط."},
                    {"role": "user", "content": extraction_prompt},
                ],
                response_format={'type': 'json_object'},
                temperature=0.01
            )
            
            raw_json = response.choices[0].message.content
            data = json.loads(raw_json)
            print(f"🔍 Intent Extraction: {data}")
            return data
            
        except Exception as e:
            print(f"❌ Intent Extraction Error: {e}")
            return self._intent_fallback(text)
    
    def _intent_fallback(self, text: str):
        """Fallback for intent extraction failures"""
        return {
            "intent": "NEW_REQUEST",
            "city": None,
            "category": None,
            "event_date": None,
            "details": text,
            "is_complete": False
        }

    def _mock_fallback(self, text: str, debug_error=""):
        return {
            "intent": "NEW_REQUEST",
            "service_category": "Unknown",
            "location": "Unknown",
            "date": "Unknown",
            "missing_info": ["service_category"],
            "reply_message": "عذراً، النظام يواجه ضغط تقني. الرجاء المحاولة لاحقاً."
        }

# Singleton instance
deepseek_service = DeepSeekService()
