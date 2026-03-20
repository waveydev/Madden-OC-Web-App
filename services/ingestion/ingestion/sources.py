from dataclasses import dataclass


@dataclass(frozen=True)
class SourceConfig:
    name: str
    base_url: str
    playbooks_path: str = "/playbooks"
    enabled: bool = True


SOURCES = [
    SourceConfig(name="huddle_gg", base_url="https://huddle.gg", playbooks_path="/playbooks", enabled=True),
]
