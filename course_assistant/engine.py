from __future__ import annotations

import json
import base64
import mimetypes
import urllib.request
from typing import Any

from pydantic import ValidationError

from .config import Settings
from .models import Answer, Quiz, SourceChunk, citation_from_chunk
from .retrieval import HybridRetriever


SYSTEM = """Use only the supplied course evidence. If evidence is insufficient, say the answer was not found.
Never invent facts or citations. Return strict JSON with separate answer and sources fields. Every source must use
an exact supplied source_id and a faithful excerpt. Visual claims require a source with image_path."""


class OpenAICompatibleClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            self.settings.vision_base_url.rstrip("/") + path,
            data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {self.settings.api_key}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=90) as response:
            return json.loads(response.read())

    def complete_json(self, prompt: str, image_paths: list[str] | None = None) -> dict[str, Any]:
        if not self.settings.api_key or not self.settings.vision_model:
            raise RuntimeError("Configure CLASS_API_KEY and CLASS_VISION_MODEL in .env")
        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        for path in (image_paths or [])[:2]:
            try:
                mime = mimetypes.guess_type(path)[0] or "image/png"
                with open(path, "rb") as stream:
                    encoded = base64.b64encode(stream.read()).decode()
                content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}"}})
            except OSError:
                continue
        data = self._post("/chat/completions", {
            "model": self.settings.vision_model,
            "temperature": 0,
            "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": content}],
            "response_format": {"type": "json_object"},
        })
        raw = data["choices"][0]["message"]["content"].strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(raw)


class CourseAssistant:
    def __init__(self, chunks: list[SourceChunk], client: OpenAICompatibleClient):
        self.chunks = {chunk.id: chunk for chunk in chunks}
        self.retriever = HybridRetriever(chunks)
        self.client = client

    def _evidence(self, question: str, materials: list[str] | None, topic: str) -> list[SourceChunk]:
        return self.retriever.search(question, materials, topic)

    @staticmethod
    def _packet(chunks: list[SourceChunk]) -> str:
        return "\n\n".join(json.dumps({"source_id": c.id, "document": c.document, "locator": c.locator,
                                                   "text": c.text, "image_path": c.image_path}) for c in chunks)

    def _validate_sources(self, answer: Answer, evidence: list[SourceChunk]) -> Answer:
        allowed = {c.id: c for c in evidence}
        for citation in answer.sources:
            if citation.source_id not in allowed:
                raise ValueError(f"Unknown citation: {citation.source_id}")
            source = allowed[citation.source_id]
            normalized = " ".join(citation.excerpt.split()).lower()
            if normalized not in " ".join(source.text.split()).lower():
                raise ValueError(f"Citation excerpt is not present in source {citation.source_id}")
        return answer

    @staticmethod
    def _hydrate_sources(raw_sources: list[Any], evidence: list[SourceChunk]):
        allowed = {chunk.id: chunk for chunk in evidence}
        hydrated = []
        for raw in raw_sources or []:
            source_id = raw if isinstance(raw, str) else raw.get("source_id", "")
            source = allowed.get(source_id)
            if not source:
                continue
            candidate = "" if isinstance(raw, str) else str(raw.get("excerpt", ""))
            excerpt = candidate if candidate and candidate.lower() in source.text.lower() else source.excerpt()
            hydrated.append(citation_from_chunk(source).model_copy(update={"excerpt": excerpt}))
        return hydrated

    def answer(self, question: str, materials: list[str] | None = None, topic: str = "") -> Answer:
        evidence = self._evidence(question, materials, topic)
        prompt = ("Return exactly this JSON shape: {\"answer\": \"...\", \"sources\": "
                  "[{\"source_id\": \"...\", \"document\": \"...\", \"locator\": \"...\", "
                  "\"excerpt\": \"exact source substring\", \"image_path\": null}]}.\n"
                  f"Question: {question}\nTopic filter: {topic or 'none'}\nEvidence:\n{self._packet(evidence)}")
        try:
            images = list(dict.fromkeys(c.image_path for c in evidence if c.image_path))
            raw = self.client.complete_json(prompt, images)
            raw["sources"] = [item.model_dump() for item in self._hydrate_sources(raw.get("sources", []), evidence)]
            answer = Answer.model_validate(raw)
            return self._validate_sources(answer, evidence)
        except (ValidationError, ValueError, KeyError, json.JSONDecodeError):
            return Answer(answer="A verifiable answer was not found in the selected course materials.", sources=[])

    def quiz(self, materials: list[str], topic: str, count: int) -> Quiz:
        evidence = self._evidence(topic or "important course concepts", materials, topic)[: max(6, count * 2)]
        prompt = (f"Create exactly {count} multiple-choice questions. Return strict JSON as "
                  "{\"questions\":[{\"question\":\"...\",\"choices\":[\"...\"],\"answer_index\":0,"
                  "\"explanation\":\"...\",\"sources\":[{\"source_id\":\"...\",\"excerpt\":\"exact text\"}]}]}. "
                  f"Evidence:\n{self._packet(evidence)}")
        raw = self.client.complete_json(prompt)
        normalized = []
        for item in raw.get("questions", []):
            normalized.append({
                "question": item.get("question") or item.get("prompt") or item.get("stem") or "Course question",
                "choices": item.get("choices", []),
                "answer_index": item.get("answer_index", 0),
                "explanation": item.get("explanation", ""),
                "sources": [source.model_dump() for source in self._hydrate_sources(item.get("sources", []), evidence)],
            })
        quiz = Quiz.model_validate({"questions": normalized})
        for item in quiz.questions:
            self._validate_sources(Answer(answer=item.explanation, sources=item.sources), evidence)
        return quiz
