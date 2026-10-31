from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from app.services.voice_service import voice_service, AVAILABLE_VOICES

router = APIRouter(prefix="/voice", tags=["voice"])

class SynthesizeRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize into speech")
    voice: Optional[str] = Field("en-US-ChristopherNeural", description="Voice identifier")
    rate: Optional[str] = Field("+0%", description="Speech speed adjustment (e.g. +10%, -10%)")
    pitch: Optional[str] = Field("+0Hz", description="Pitch adjustment")
    engine: Optional[str] = Field("auto", description="Synthesis engine ('auto', 'edge-tts', 'pyttsx3')")

class TranscribeResponse(BaseModel):
    text: str
    duration: float
    language: str
    latency_ms: float
    confidence: float
    segments: List[Dict[str, Any]]

@router.get("/status")
def get_voice_status():
    """Returns the operational status of the low-latency open-source STT and TTS engines."""
    return {
        "status": "online",
        "stt": {
            "engine": "faster-whisper",
            "model": "base.en",
            "compute_type": "int8",
            "device": "cpu",
            "vad_enabled": True,
            "quantization": "int8"
        },
        "tts": {
            "primary_engine": "edge-tts",
            "fallback_engine": "pyttsx3",
            "default_voice": "en-US-ChristopherNeural",
            "total_voices": len(AVAILABLE_VOICES)
        }
    }

@router.get("/voices")
def get_available_voices():
    """Returns list of curated open-source TTS voices."""
    return AVAILABLE_VOICES

@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    file: UploadFile = File(..., description="Audio recording file (webm, wav, mp3, ogg)")
):
    """
    Transcribes spoken voice into text using the low-latency open-source faster-whisper model.
    """
    if not file:
        raise HTTPException(status_code=400, detail="Audio file must be provided.")

    try:
        audio_bytes = await file.read()
        print(f"[VoiceAPI] /transcribe received file='{file.filename}', size={len(audio_bytes)} bytes")
        if len(audio_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file received.")

        result = voice_service.transcribe(audio_bytes, filename=file.filename or "audio.webm")
        print(f"[VoiceAPI] Transcription result: '{result.get('text')}'")
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Audio transcription failed: {str(e)}")

@router.post("/synthesize")
async def synthesize_speech(req: SynthesizeRequest):
    """
    Synthesizes conversational text into human-like speech with sub-second latency.
    """
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    try:
        audio_bytes, mime_type = await voice_service.synthesize(
            text=req.text,
            voice=req.voice or "en-US-ChristopherNeural",
            rate=req.rate or "+0%",
            pitch=req.pitch or "+0Hz",
            engine=req.engine or "auto"
        )

        ext = "mp3" if "mpeg" in mime_type else "wav"
        return Response(
            content=audio_bytes,
            media_type=mime_type,
            headers={
                "Content-Disposition": f'inline; filename="speech.{ext}"',
                "Cache-Control": "public, max-age=3600"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speech synthesis failed: {str(e)}")
