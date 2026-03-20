from bs4 import BeautifulSoup
import re


FORMATION_HINTS = ("gun", "singleback", "i form", "iform", "pistol", "shotgun", "ace", "bunch", "trips", "empty")
FOOTBALL_TERMS = (
    "slant",
    "mesh",
    "cross",
    "dagger",
    "flood",
    "post",
    "corner",
    "screen",
    "zone",
    "boot",
    "draw",
    "inside",
    "outside",
    "quick",
    "read",
    "option",
)
GENERIC_BLACKLIST = {
    "subscribe",
    "gameplans",
    "offensive coordinator",
    "meta buster",
    "database",
    "playbook finder",
    "privacy",
    "terms",
    "login",
    "sign up",
    "quicksell values",
    "training",
    "platinum",
    "chems",
    "abilities",
    "alternate playbook",
}


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _contains_term(text: str, term: str) -> bool:
    return re.search(rf"\b{re.escape(term)}\b", text) is not None


def _has_letters(value: str) -> bool:
    return any(char.isalpha() for char in value)


def _too_numeric(value: str) -> bool:
    stripped = re.sub(r"[^0-9A-Za-z]", "", value)
    if not stripped:
        return True
    digits = sum(1 for char in stripped if char.isdigit())
    return digits / len(stripped) > 0.45


def _looks_like_play_label(value: str) -> bool:
    text = _clean_text(value)
    if len(text) < 6 or len(text) > 90:
        return False
    if not _has_letters(text):
        return False
    if _too_numeric(text):
        return False
    return True


def _infer_concept(value: str) -> str:
    lower = value.lower()
    if "mesh" in lower:
        return "Mesh"
    if "cross" in lower:
        return "Crossers"
    if "flood" in lower or "boot" in lower:
        return "Flood"
    if "slant" in lower:
        return "Quick Game"
    if "dagger" in lower:
        return "Dagger"
    if "zone" in lower:
        return "Zone Run"
    return "Unknown"


def _split_formation_and_play(text: str) -> tuple[str, str]:
    chunks = [part.strip() for part in re.split(r"\s[-|•]\s", text) if part.strip()]
    if len(chunks) >= 2:
        left = chunks[0].lower()
        if any(hint in left for hint in FORMATION_HINTS):
            return chunks[0], chunks[1]

    for hint in FORMATION_HINTS:
        if hint in text.lower():
            return text, text

    return "Unknown", text


def _looks_football_specific(formation: str, play_name: str, concept: str) -> bool:
    lower_name = play_name.lower()
    lower_formation = formation.lower()
    lower_concept = concept.lower()

    if any(_contains_term(lower_name, term) for term in GENERIC_BLACKLIST):
        return False

    if any(_contains_term(lower_name, term) for term in FOOTBALL_TERMS):
        return True

    if any(hint in lower_formation for hint in FORMATION_HINTS):
        return True

    if lower_concept != "unknown":
        return True

    if lower_formation == "unknown" and lower_concept == "unknown":
        return False

    return False


def parse_huddle_playbook_index(html: str, base_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict] = []

    for anchor in soup.select('a[href*="/playbooks/"]'):
        label = anchor.get_text(" ", strip=True)
        href_value = anchor.get("href")
        if isinstance(href_value, list):
            href = " ".join(str(part) for part in href_value).strip()
        else:
            href = str(href_value or "").strip()
        if not href or not label:
            continue

        team = "Unknown"
        year = "Unknown"
        parts = [part for part in label.replace("|", "-").split("-") if part.strip()]
        if parts:
            team = parts[0].strip()
        if len(parts) > 1:
            year = parts[-1].strip()

        full_url = href if href.startswith("http") else f"{base_url.rstrip('/')}/{href.lstrip('/')}"
        rows.append(
            {
                "team": team,
                "madden_version": year,
                "playbook_url": full_url,
                "raw_label": label,
            }
        )

    unique = {(entry["playbook_url"], entry["raw_label"]): entry for entry in rows}
    return list(unique.values())


def parse_huddle_playbook_detail(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    plays: list[dict] = []

    selectors = [
        "[data-play-name]",
        "[class*='play-name']",
        "[class*='play']",
        "[class*='formation']",
        "a[href*='/plays/']",
        "li",
        "tr",
    ]

    for block in soup.select(", ".join(selectors)):
        text = _clean_text(block.get_text(" ", strip=True))
        if not _looks_like_play_label(text):
            continue

        formation, play_name = _split_formation_and_play(text)
        concept = _infer_concept(play_name)

        if not _looks_like_play_label(play_name):
            continue
        if not _looks_football_specific(formation, play_name, concept):
            continue
        if formation.lower() == play_name.lower() and concept == "Unknown":
            continue

        plays.append(
            {
                "formation": formation,
                "play_name": play_name,
                "concept": concept,
                "raw_text": text,
            }
        )

    unique = {(entry["formation"], entry["play_name"], entry["concept"]): entry for entry in plays}
    return list(unique.values())
