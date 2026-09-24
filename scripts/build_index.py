from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from course_assistant.ingest import ACCEPTED, build_index


def collect(values: list[str]) -> list[Path]:
    files: list[Path] = []
    for value in values:
        path = Path(value)
        if path.is_dir():
            files.extend(p for p in path.rglob("*") if p.suffix.lower() in ACCEPTED)
        elif path.suffix.lower() in ACCEPTED:
            files.append(path)
    return sorted(set(files))


if __name__ == "__main__":
    inputs = collect(sys.argv[1:])
    if not inputs:
        raise SystemExit("Usage: python scripts/build_index.py <file-or-folder> [...]")
    chunks = build_index(inputs, Path("data/index"))
    print(f"Indexed {len(chunks)} text and visual records from {len(inputs)} files.")
