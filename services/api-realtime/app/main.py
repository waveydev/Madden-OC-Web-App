from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from shared_schemas.realtime import PlayRecommendation, SituationEvent, SuggestResponse
from .rules_engine import suggest_plays
from .stt import STTConfigurationError, transcribe_audio_base64
from .voice_parser import parse_situation_from_transcript

app = FastAPI(title="Madden OC Realtime API", version="0.1.0")


class VoiceAnalyzeRequest(BaseModel):
    transcript: str | None = None
    audio_base64: str | None = None
    mime_type: str = Field(default="audio/m4a")


class VoiceAnalyzeResponse(BaseModel):
    transcript: str
    parsed_event: SituationEvent
    recommendations: list[PlayRecommendation]


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/suggest", response_model=SuggestResponse)
def suggest(event: SituationEvent) -> SuggestResponse:
    return SuggestResponse(recommendations=suggest_plays(event))


@app.post("/v1/voice/analyze", response_model=VoiceAnalyzeResponse)
async def voice_analyze(payload: VoiceAnalyzeRequest) -> VoiceAnalyzeResponse:
    transcript = (payload.transcript or "").strip()

    if not transcript:
        if not payload.audio_base64:
            raise HTTPException(status_code=400, detail="Provide either transcript or audio_base64.")
        try:
            transcript = await transcribe_audio_base64(payload.audio_base64, payload.mime_type)
        except STTConfigurationError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"STT request failed: {exc}") from exc

    event = parse_situation_from_transcript(transcript)
    recommendations = suggest_plays(event)
    return VoiceAnalyzeResponse(
        transcript=transcript,
        parsed_event=event,
        recommendations=recommendations,
    )
