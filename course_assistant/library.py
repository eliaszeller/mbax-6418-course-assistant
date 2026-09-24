from __future__ import annotations

import hashlib
import json
import shutil
import threading
from pathlib import Path

from .ingest import ACCEPTED, ingest_file, load_index
from .models import SourceChunk


class MaterialLibrary:
    """Persistent, deduplicated course-material collection."""

    def __init__(self, index_path: Path, data_root: Path):
        self.index_path = index_path
        self.data_root = data_root
        self.upload_root = data_root / "uploads"
        self.index_root = data_root / "index"
        self.lock = threading.RLock()
        loaded = load_index(index_path) if index_path.exists() else []
        self.chunks = []
        seen = set()
        for chunk in loaded:
            signature = self._signature(chunk)
            if signature not in seen:
                seen.add(signature)
                self.chunks.append(chunk)
        if len(self.chunks) != len(loaded):
            self._write()

    @property
    def materials(self) -> list[str]:
        return sorted({chunk.material for chunk in self.chunks})

    def _write(self) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.index_path.with_suffix(".jsonl.tmp")
        with temporary.open("w", encoding="utf-8") as stream:
            for chunk in self.chunks:
                stream.write(chunk.model_dump_json() + "\n")
        temporary.replace(self.index_path)

    def add(self, files: list[Path], max_bytes: int = 150 * 1024 * 1024) -> tuple[list[str], list[str], int]:
        added, skipped, record_count = [], [], 0
        with self.lock:
            existing_ids = {chunk.id for chunk in self.chunks}
            # IDs include the source path, so compare content metadata too. This
            # catches the same deck uploaded from Downloads, Desktop, etc.
            existing_signatures = {self._signature(chunk) for chunk in self.chunks}
            for source in files:
                if source.suffix.lower() not in ACCEPTED:
                    skipped.append(f"{source.name} (unsupported format)")
                    continue
                if source.stat().st_size > max_bytes:
                    skipped.append(f"{source.name} (over 150 MB)")
                    continue
                digest = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
                destination_dir = self.upload_root / digest
                destination_dir.mkdir(parents=True, exist_ok=True)
                destination = destination_dir / source.name
                if not destination.exists():
                    shutil.copy2(source, destination)
                incoming = ingest_file(destination, self.index_root)
                unique = [chunk for chunk in incoming
                          if chunk.id not in existing_ids and self._signature(chunk) not in existing_signatures]
                if not unique:
                    skipped.append(f"{source.name} (already indexed)")
                    continue
                self.chunks.extend(unique)
                existing_ids.update(chunk.id for chunk in unique)
                existing_signatures.update(self._signature(chunk) for chunk in unique)
                added.append(unique[0].material)
                record_count += len(unique)
            self._write()
        return added, skipped, record_count

    @staticmethod
    def _signature(chunk: SourceChunk) -> tuple[str, str, str, str]:
        return (chunk.document.casefold(), chunk.locator.casefold(), chunk.kind,
                " ".join(chunk.text.split()).casefold())

    def remove(self, materials: list[str]) -> int:
        targets = set(materials)
        if not targets:
            return 0
        with self.lock:
            removed = [chunk for chunk in self.chunks if chunk.material in targets]
            self.chunks = [chunk for chunk in self.chunks if chunk.material not in targets]
            self._write()

            live_images = {chunk.image_path for chunk in self.chunks if chunk.image_path}
            asset_roots = set()
            for chunk in removed:
                if chunk.image_path and chunk.image_path not in live_images:
                    image = Path(chunk.image_path)
                    try:
                        asset_roots.add(image.parents[1])
                    except IndexError:
                        pass
            for root in asset_roots:
                if root.is_relative_to(self.index_root / "assets") and root.exists():
                    shutil.rmtree(root)

            for directory in self.upload_root.glob("*") if self.upload_root.exists() else []:
                if any(file.stem in targets for file in directory.iterdir() if file.is_file()):
                    shutil.rmtree(directory)
        return len(removed)
