from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import os
from services.rag import get_rag_response
from services.ussd import handle_ussd
from services.translation import translate_text
import structlog
from langchain.schema import Document

load_dotenv()

app = FastAPI(title="UwaziVoice", version="1.0.0")

# Logging setup
logger = structlog.get_logger()

# Templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# In-memory query log for live dashboard (for MVP, no DB)
queries_log = []

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "queries": queries_log[-20:]})

@app.post("/ussd")
async def ussd_endpoint(request: Request):
    form = await request.form()
    session_id = form.get("sessionId")
    service_code = form.get("serviceCode")
    phone_number = form.get("phoneNumber")
    text = form.get("text", "")

    # Hash phone for privacy (never store raw)
    phone_hash = hash(phone_number)  # Simple hash for demo

    logger.info("USSD request", session_id=session_id, phone_hash=phone_hash, text=text)

    response = handle_ussd(text, session_id)
    
    # Log for dashboard (anonymized)
    queries_log.append({
        "timestamp": "Now",  # Use real time in prod
        "phone_hash": phone_hash,
        "language": response.get("language", "Unknown"),
        "query": text[:50] + "..." if len(text) > 50 else text,
        "response": response.get("response", "")[:100] + "...",
        "score": response.get("score", 0)
    })
    
    return HTMLResponse(content=response["response"])

@app.get("/ask")
async def ask_question(question: str, lang: str = "English"):
    # Translate query if not English
    if lang != "English":
        question_en = translate_text(question, "en", lang)
    else:
        question_en = question
    
    response = get_rag_response(question_en)
    if lang != "English":
        response["answer"] = translate_text(response["answer"], lang, "en")  # Back to target lang
    
    return {"answer": response["answer"], "citations": response.get("citations", [])}

@app.get("/health")
async def health():
    return {"status": "healthy", "queries_today": len(queries_log)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)