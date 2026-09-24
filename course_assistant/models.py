from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class SourceChunk(BaseModel):
    id: str
    document: str
    material: str
    locator: str
    text: str
    image_path: str | None = None
    kind: Literal["text", "visual"] = "text"

    def excerpt(self, limit: int = 320) -> str:
        clean = " ".join(self.text.split())
        return clean if len(clean) <= limit else clean[: limit - 1] + "…"


class Citation(BaseModel):
    source_id: str
    document: str
    locator: str
    excerpt: str = Field(min_length=1)
    image_path: str | None = None


class Answer(BaseModel):
    answer: str
    sources: list[Citation]

    @model_validator(mode="after")
    def require_sources_for_claims(self) -> "Answer":
        if self.answer.strip() and "not found" not in self.answer.lower() and not self.sources:
            raise ValueError("A substantive answer requires at least one source.")
        return self


class QuizQuestion(BaseModel):
    question: str
    choices: list[str] = Field(min_length=2)
    answer_index: int
    explanation: str
    sources: list[Citation] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_answer(self) -> "QuizQuestion":
        if not 0 <= self.answer_index < len(self.choices):
            raise ValueError("answer_index is outside choices")
        return self


class Quiz(BaseModel):
    questions: list[QuizQuestion] = Field(min_length=1)


def citation_from_chunk(chunk: SourceChunk) -> Citation:
    return Citation(
        source_id=chunk.id,
        document=chunk.document,
        locator=chunk.locator,
        excerpt=chunk.excerpt(),
        image_path=chunk.image_path if chunk.image_path and Path(chunk.image_path).exists() else None,
    )

