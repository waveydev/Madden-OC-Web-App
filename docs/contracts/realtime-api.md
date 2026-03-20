# Realtime API Contract (V1)

## POST /v1/suggest

### Request

```json
{
  "down": 3,
  "distance": 7,
  "yard_line": 42,
  "clock_seconds": 312,
  "offense_personnel": "11",
  "defense_shell": "Cover 3",
  "defense_front": "Nickel",
  "hash": "right"
}
```

## POST /v1/voice/analyze

Request can include either `transcript` or `audio_base64`.

### Request (text)

```json
{
  "transcript": "3rd and 7, cover 3 nickel, right hash"
}
```

### Request (audio)

```json
{
  "audio_base64": "<base64-audio>",
  "mime_type": "audio/m4a"
}
```

### Response

```json
{
  "transcript": "3rd and 7 cover 3 nickel right hash",
  "parsed_event": {
    "down": 3,
    "distance": 7,
    "yard_line": 42,
    "clock_seconds": 300,
    "offense_personnel": "11",
    "defense_shell": "Cover 3",
    "defense_front": "Nickel",
    "hash": "right"
  },
  "recommendations": [
    {
      "play_name": "Trips Y Cross",
      "formation": "Gun Trips TE",
      "concept": "Crossers",
      "confidence": 0.82,
      "rationale": "Cover 3 with 3rd-and-medium favors layered crossing concepts."
    }
  ]
}
```

### Response

```json
{
  "recommendations": [
    {
      "play_name": "Trips Y Cross",
      "formation": "Gun Trips TE",
      "concept": "Crossers",
      "confidence": 0.82,
      "rationale": "Cover 3 with 3rd-and-medium favors layered crossing concepts."
    }
  ]
}
```
