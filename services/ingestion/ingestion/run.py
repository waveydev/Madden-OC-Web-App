import asyncio
import json
from pathlib import Path
from urllib.parse import urljoin

import httpx

from .normalize import normalize_index_entries, normalize_play_entries
from .parsers import parse_huddle_playbook_detail, parse_huddle_playbook_index
from .sources import SOURCES


OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
DETAIL_SAMPLE_LIMIT = 25


async def fetch_source_index(client: httpx.AsyncClient, base_url: str, playbooks_path: str) -> dict:
    playbooks_url = urljoin(base_url, playbooks_path)
    response = await client.get(playbooks_url, timeout=20)
    response.raise_for_status()
    index_rows = parse_huddle_playbook_index(response.text, base_url)
    return {
        "url": playbooks_url,
        "index_entries": index_rows,
        "raw_html": response.text,
        "length": len(response.text),
    }


async def fetch_playbook_details(client: httpx.AsyncClient, playbook_url: str) -> list[dict]:
    response = await client.get(playbook_url, timeout=20)
    response.raise_for_status()
    return parse_huddle_playbook_detail(response.text)


def write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


async def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    enabled_sources = [source for source in SOURCES if source.enabled]
    async with httpx.AsyncClient(headers={"User-Agent": "MaddenOCBot/0.1"}, follow_redirects=True) as client:
        results = await asyncio.gather(
            *[
                fetch_source_index(client, source.base_url, source.playbooks_path)
                for source in enabled_sources
            ],
            return_exceptions=True,
        )

    for source, result in zip(enabled_sources, results):
        if isinstance(result, Exception):
            print(f"[ERROR] {source.name}: {result}")
            continue

        index_rows = result.get("index_entries", [])
        normalized_index = normalize_index_entries(source.name, index_rows)
        write_json(OUTPUT_DIR / f"{source.name}_index.json", normalized_index)

        print(f"[OK] {source.name}: found {len(index_rows)} playbook index rows")

        sample_playbooks = index_rows[:DETAIL_SAMPLE_LIMIT]
        async with httpx.AsyncClient(headers={"User-Agent": "MaddenOCBot/0.1"}, follow_redirects=True) as client:
            detail_results = await asyncio.gather(
                *[fetch_playbook_details(client, row["playbook_url"]) for row in sample_playbooks],
                return_exceptions=True,
            )

        normalized_plays: list[dict] = []
        for row, detail in zip(sample_playbooks, detail_results):
            if isinstance(detail, Exception):
                print(f"[WARN] {source.name} detail fetch failed {row['playbook_url']}: {detail}")
                continue
            normalized_plays.extend(normalize_play_entries(source.name, row["playbook_url"], detail))

        write_json(OUTPUT_DIR / f"{source.name}_plays_sample.json", normalized_plays)
        print(f"[OK] {source.name}: normalized {len(normalized_plays)} sample play rows")


if __name__ == "__main__":
    asyncio.run(main())
