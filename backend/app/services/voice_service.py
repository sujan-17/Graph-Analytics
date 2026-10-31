import os
import io
import time
import tempfile
import asyncio
from typing import Optional, Dict, Any, List, Tuple
from faster_whisper import WhisperModel
import edge_tts
import pyttsx3

AVAILABLE_VOICES = [
    {
        "id": "en-US-ChristopherNeural",
        "name": "Christopher (US Male - Professional Analyst)",
        "gender": "Male",
        "locale": "en-US",
        "engine": "edge-tts",
        "recommended": True
    },
    {
        "id": "en-US-JennyNeural",
        "name": "Jenny (US Female - Clear & Conversational)",
        "gender": "Female",
        "locale": "en-US",
        "engine": "edge-tts"
    },
    {
        "id": "en-US-GuyNeural",
        "name": "Guy (US Male - Natural)",
        "gender": "Male",
        "locale": "en-US",
        "engine": "edge-tts"
    },
    {
        "id": "en-US-AriaNeural",
        "name": "Aria (US Female - Executive)",
        "gender": "Female",
        "locale": "en-US",
        "engine": "edge-tts"
    },
    {
        "id": "en-GB-RyanNeural",
        "name": "Ryan (UK Male - Polished)",
        "gender": "Male",
        "locale": "en-GB",
        "engine": "edge-tts"
    },
    {
        "id": "en-GB-SoniaNeural",
        "name": "Sonia (UK Female - Clear)",
        "gender": "Female",
        "locale": "en-GB",
        "engine": "edge-tts"
    },
    {
        "id": "en-IN-PrabhatNeural",
        "name": "Prabhat (India Male - Natural)",
        "gender": "Male",
        "locale": "en-IN",
        "engine": "edge-tts"
    },
    {
        "id": "en-IN-NeerjaNeural",
        "name": "Neerja (India Female - Natural)",
        "gender": "Female",
        "locale": "en-IN",
        "engine": "edge-tts"
    },
    {
        "id": "offline-pyttsx3",
        "name": "System SAPI5 (Offline OS Voice)",
        "gender": "Neutral",
        "locale": "en-US",
        "engine": "pyttsx3"
    }
]

class VoiceService:
    _instance: Optional["VoiceService"] = None
    _whisper_model: Optional[WhisperModel] = None
    _model_name: str = "base.en"

    @classmethod
    def get_instance(cls) -> "VoiceService":
        if cls._instance is None:
            cls._instance = VoiceService()
        return cls._instance

    def __init__(self):
        # Model lazy-loaded upon first request to prevent slow server startup
        self._whisper_model = None

    def get_whisper_model(self) -> WhisperModel:
        if self._whisper_model is None:
            # Load with int8 quantization on CPU for low latency inference
            # Multithreaded execution across CPU cores
            threads = min(os.cpu_count() or 4, 4)
            self._whisper_model = WhisperModel(
                model_size_or_path=self._model_name,
                device="cpu",
                compute_type="int8",
                cpu_threads=threads
            )
        return self._whisper_model

    def warm_up_stt(self) -> None:
        """Explicitly warm up the Whisper model in background."""
        try:
            self.get_whisper_model()
        except Exception as e:
            print(f"[VoiceService] Error warming up Whisper: {e}")

    def transcribe(self, audio_bytes: bytes, filename: str = "audio.wav") -> Dict[str, Any]:
        """
        Transcribes speech audio into text using faster-whisper.
        Supports WebM, WAV, MP3, OGG containers natively via PyAV.
        """
        if not audio_bytes or len(audio_bytes) < 100:
            return {
                "text": "",
                "duration": 0.0,
                "language": "en",
                "latency_ms": 0.0,
                "confidence": 0.0,
                "segments": []
            }

        t_start = time.perf_counter()
        model = self.get_whisper_model()

        # Save to temporary file to guarantee stream seekability across all container formats
        ext = os.path.splitext(filename)[1] or ".webm"
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write(audio_bytes)

        try:
            # Low latency parameters:
            # beam_size=1 (greedy search for lowest latency)
            # vad_filter=False to prevent quiet or short microphone speech from being discarded
            segments, info = model.transcribe(
                tmp_path,
                beam_size=1,
                best_of=1,
                temperature=0.0,
                language="en",
                vad_filter=False
            )

            segment_list = []
            full_text_parts = []
            for s in segments:
                text_clean = s.text.strip()
                if text_clean:
                    full_text_parts.append(text_clean)
                    segment_list.append({
                        "start": round(s.start, 2),
                        "end": round(s.end, 2),
                        "text": text_clean
                    })

            elapsed_ms = (time.perf_counter() - t_start) * 1000.0
            full_text = " ".join(full_text_parts).strip()
            print(f"[VoiceService] Transcribed {len(audio_bytes)} bytes -> '{full_text}' ({elapsed_ms:.1f}ms)")

            return {
                "text": full_text,
                "duration": round(getattr(info, "duration", 0.0), 2),
                "language": getattr(info, "language", "en"),
                "latency_ms": round(elapsed_ms, 1),
                "confidence": 0.95 if full_text else 0.0,
                "segments": segment_list
            }
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

    async def synthesize(
        self,
        text: str,
        voice: str = "en-US-ChristopherNeural",
        rate: str = "+0%",
        pitch: str = "+0Hz",
        engine: str = "auto"
    ) -> Tuple[bytes, str]:
        """
        Synthesizes text into speech.
        Returns: (audio_bytes, mime_type)
        """
        clean_text = text.strip()
        if not clean_text:
            return b"", "audio/mpeg"

        # Determine engine: if offline voice chosen or requested
        if engine == "pyttsx3" or voice == "offline-pyttsx3":
            return self._synthesize_pyttsx3(clean_text)

        # Default to open source edge-tts neural model
        try:
            return await self._synthesize_edge_tts(clean_text, voice, rate, pitch)
        except Exception as e:
            print(f"[VoiceService] edge-tts error: {e}, falling back to pyttsx3 offline engine.")
            return self._synthesize_pyttsx3(clean_text)

    async def _synthesize_edge_tts(
        self,
        text: str,
        voice: str,
        rate: str,
        pitch: str
    ) -> Tuple[bytes, str]:
        # Truncate overly long text for conversational TTS latency (max ~2000 chars)
        synthesize_text = text[:2500] if len(text) > 2500 else text
        communicate = edge_tts.Communicate(
            text=synthesize_text,
            voice=voice,
            rate=rate,
            pitch=pitch
        )

        audio_chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])

        return b"".join(audio_chunks), "audio/mpeg"

    def _synthesize_pyttsx3(self, text: str) -> Tuple[bytes, str]:
        synthesize_text = text[:1500] if len(text) > 1500 else text
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", 175)
            engine.save_to_file(synthesize_text, tmp_path)
            engine.runAndWait()

            with open(tmp_path, "rb") as f:
                data = f.read()
            return data, "audio/wav"
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

voice_service = VoiceService.get_instance()
