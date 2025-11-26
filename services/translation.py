import requests
import os
from dotenv import load_dotenv

load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/facebook/nllb-200-distilled-600M"

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

def translate_text(text: str, target_lang: str, src_lang: str = "eng_Latn"):
    # Lang codes: eng_Latn (English), swa_Latn (Swahili), kik_Latn (Kikuyu approx), luo_Latn (Luo approx)
    lang_map = {"English": "eng_Latn", "Kiswahili": "swa_Latn", "Gikuyu": "kik_Latn", "Luo": "luo_Latn"}
    target_code = lang_map.get(target_lang, "eng_Latn")
    
    payload = {
        "inputs": text,
        "parameters": {"src_lang": src_lang, "tgt_lang": target_code}
    }
    
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()[0]["translation_text"]
    else:
        return text  # Fallback