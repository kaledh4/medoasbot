import re

def normalize_text(text):
    """
    Normalizes text for consistent comparison:
    - Lowercase
    - Strip whitespace
    - Arabic Normalization (Alif, Taa Marbuta)
    """
    if not text:
        return ""
    
    # 1. Basic Cleaning
    text = str(text).strip().lower()
    
    # 2. Arabic Normalization
    # Normalize Alif forms (إأآا) -> ا
    text = re.sub(r"[إأآا]", "ا", text)
    # Normalize Taa Marbuta (ة) -> ه
    text = re.sub(r"ة", "ه", text)
    # Normalize Ya (ي) -> ی (Optional, but 'ي' is standard in Saudi. 'ى' is Alif Maqsura)
    # Let's map Alif Maqsura 'ى' to 'ي' just in case
    text = re.sub(r"ى", "ي", text)
    
    # Remove Diacritics (Tashkeel)
    text = re.sub(r"[\u064B-\u065F]", "", text)
    
    return text

def is_cancellation(text):
    """
    Checks if the text is a cancellation command.
    """
    normalized = normalize_text(text)
    
    # Strip common markdown/formatting symbols (* _ ` ~)
    normalized = normalized.replace('*', '').replace('_', '').replace('`', '').replace('~', '')
    normalized = normalized.strip()
    
    # Keywords map (Normalized forms)
    # 'إلغاء' -> 'الغاء'
    # 'كنسل' -> 'كنسل'
    keywords = {
        'cancel', 
        'reset', 
        'stop', 
        'exit',
        'quit',
        'الغاء',  # Normalized 'إلغاء'
        'كنسل',
        'خروج',
        'توقف',
        'انهاء'
    }
    
    return normalized in keywords
