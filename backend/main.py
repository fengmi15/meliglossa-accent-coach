import os
import tempfile
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from transcriber import transcribe
from error_detector import detect_errors
from feedback import generate_feedback

app = FastAPI(title="Meliglossa Accent Coach API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyse")
async def analyse(
    audio: UploadFile = File(...),
    prompt_text: str = Form(None),
):
    allowed_extensions = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm"}
    ext = os.path.splitext(audio.filename or "")[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name

    try:
        transcript = transcribe(tmp_path)
        errors = detect_errors(transcript)
        feedback_text, cost_usd = generate_feedback(transcript, errors, prompt_text)
    finally:
        os.unlink(tmp_path)

    return {
        "transcript": transcript,
        "errors": errors,
        "feedback_bengali": feedback_text,
        "token_cost_usd": round(cost_usd, 6),
    }
