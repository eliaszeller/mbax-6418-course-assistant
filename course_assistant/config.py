from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Settings:
    api_key: str
    vision_base_url: str
    vision_model: str
    text_embedding_base_url: str
    text_embedding_model: str
    visual_embedding_base_url: str
    visual_embedding_model: str
    rerank_base_url: str
    rerank_model: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        return cls(
            api_key=os.getenv("CLASS_API_KEY", ""),
            vision_base_url=os.getenv("CLASS_VISION_BASE_URL", "http://dobolyi.com:9001/v1"),
            vision_model=os.getenv("CLASS_VISION_MODEL", ""),
            text_embedding_base_url=os.getenv("CLASS_TEXT_EMBEDDING_BASE_URL", ""),
            text_embedding_model=os.getenv("CLASS_TEXT_EMBEDDING_MODEL", ""),
            visual_embedding_base_url=os.getenv("CLASS_VISUAL_EMBEDDING_BASE_URL", ""),
            visual_embedding_model=os.getenv("CLASS_VISUAL_EMBEDDING_MODEL", ""),
            rerank_base_url=os.getenv("CLASS_RERANK_BASE_URL", ""),
            rerank_model=os.getenv("CLASS_RERANK_MODEL", ""),
        )

