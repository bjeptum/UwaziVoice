from africastalking.AfricasTalkingGateway import (Gateway)
import os
from dotenv import load_dotenv

load_dotenv()
username = os.getenv("AFRICASTALKING_USERNAME")
api_key = os.getenv("AFRICASTALKING_API_KEY")

# Hard-coded phrases
MENUS = {
    "English": {
        "welcome": "Welcome to UwaziVoice! 1. English 2. Kiswahili 3. Gikuyu 4. Luo",
        "prompt": "Ask your question about government or policy:",
        "fallback": "I don't have verified info on that. Ask about Constitution or Vision 2030."
    },
    "Kiswahili": {
        "welcome": "Karibu UwaziVoice! 1. Kiingereza 2. Kiswahili 3. Gikuyu 4. Luo",
        "prompt": "Uliza swali lako kuhusu serikali au sera:",
        "fallback": "Samahani, sina taarifa iliyothibitishwa kuhusu hilo."
    },
    # Add Kikuyu and Kalenjin (use Google Translate for demo; replace with accurate)
    "Gikuyu": {
        "welcome": "Welcome to UwaziVoice in Gikuyu! 1. English 2. Kiswahili 3. Gikuyu 4. Luo",  # Placeholder
        "prompt": "Andika swali lako kuhusu serikali:",  # Placeholder
        "fallback": "Nĩndĩhĩte taarifa ya kwĩra kũgĩ."  # Placeholder
    },
    "Luo": {
        "welcome": "Welcome to UwaziVoice in Luo! 1. English 2. Kiswahili 3. Gikuyu 4. Luo",  # Placeholder
        "prompt": "Andika swali lako:",  # Placeholder
        "fallback": "Sit have verified info."  # Placeholder
    }
}

# Session store (in-memory for MVP)
sessions = {}

def handle_ussd(text: str, session_id: str):
    if session_id not in sessions:
        sessions[session_id] = {"step": "lang_select", "lang": None}
    
    session = sessions[session_id]
    
    if session["step"] == "lang_select":
        if text == "1":
            session["lang"] = "English"
        elif text == "2":
            session["lang"] = "Kiswahili"
        elif text == "3":
            session["lang"] = "Gikuyu"
        elif text == "4":
            session["lang"] = "Luo"
        else:
            return {"response": MENUS["English"]["welcome"], "language": "English", "score": 0}
        
        session["step"] = "query"
        return {"response": MENUS[session["lang"]]["prompt"], "language": session["lang"], "score": 0}
    
    elif session["step"] == "query":
        from rag import get_rag_response  # Import here to avoid cycle
        from translation import translate_text
        lang = session["lang"]
        
        # Translate to English for RAG
        query_en = translate_text(text, "en", lang) if lang != "English" else text
        
        rag_result = get_rag_response(query_en, lang)
        answer = rag_result["answer"]
        
        # Translate back
        if lang != "English":
            answer = translate_text(answer, lang, "en")
        
        session["step"] = "end"  # One-shot for MVP
        return {"response": answer[:160], "language": lang, "score": rag_result["score"]}  # Truncate for USSD