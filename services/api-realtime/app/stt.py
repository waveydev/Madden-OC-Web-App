import base64
import os
from uuid import uuid4

import httpx  # pyright: ignore[reportMissingImports]


class STTConfigurationError(RuntimeError):
    pass


def _decode_audio(audio_base64: str) -> bytes:
    try:
        return base64.b64decode(audio_base64)
    except Exception as exc:
        raise ValueError("Invalid base64 audio payload.") from exc


def _ext_from_mime(mime_type: str) -> str:
    mapping = {
        "audio/m4a": "m4a",
        "audio/mp4": "mp4",
        "audio/wav": "wav",
        "audio/mpeg": "mp3",
        "audio/webm": "webm",
    }
    return mapping.get(mime_type.lower(), "m4a")


async def transcribe_audio_base64(audio_base64: str, mime_type: str = "audio/m4a") -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise STTConfigurationError("OPENAI_API_KEY is not configured for cloud STT.")

    model = os.getenv("STT_MODEL", "gpt-4o-mini-transcribe")
    audio_bytes = _decode_audio(audio_base64)
    ext = _ext_from_mime(mime_type)
    filename = f"voice_{uuid4().hex}.{ext}"

    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {api_key}"},
            data={"model": model},
            files={"file": (filename, audio_bytes, mime_type)},
        )

    if response.status_code >= 400:
        raise RuntimeError(f"Transcription API error ({response.status_code}): {response.text}")

    data = response.json()
    transcript = (data.get("text") or "").strip()
    if not transcript:
        raise RuntimeError("Transcription response did not include text.")
    return transcript
