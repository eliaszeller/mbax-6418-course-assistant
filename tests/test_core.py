import unittest
import tempfile
from pathlib import Path

from course_assistant.engine import CourseAssistant
from course_assistant.models import Answer, Citation, QuizQuestion, SourceChunk
from course_assistant.retrieval import HybridRetriever
from course_assistant.library import MaterialLibrary


def chunks():
    return [
        SourceChunk(id="a", document="week2.pptx", material="week2", locator="Slide 8", text="Context is working memory measured in tokens."),
        SourceChunk(id="b", document="week5.pptx", material="week5", locator="Slide 10", text="RAG retrieves relevant chunks using keyword and vector search."),
    ]


class CoreTests(unittest.TestCase):
    def test_hybrid_retrieval_finds_rag(self):
        self.assertEqual(HybridRetriever(chunks()).search("keyword and vector search retrieves relevant chunks")[0].id, "b")

    def test_answer_requires_sources(self):
        with self.assertRaises(ValueError):
            Answer(answer="Context is working memory.", sources=[])

    def test_quiz_answer_key_is_validated_and_fixed(self):
        q = QuizQuestion(question="What is context?", choices=["Storage", "Working memory"], answer_index=1,
                         explanation="The slide defines it this way.",
                         sources=[Citation(source_id="a", document="week2.pptx", locator="Slide 8", excerpt="Context is working memory")])
        self.assertEqual(q.answer_index, 1)

    def test_quiz_hydrates_source_metadata(self):
        class FakeClient:
            def complete_json(self, prompt, image_paths=None):
                return {"questions": [{"prompt": "What does RAG retrieve?", "choices": ["Chunks", "Weights"],
                    "answer_index": 0, "explanation": "It retrieves relevant chunks.",
                    "sources": [{"source_id": "b", "excerpt": "retrieves relevant chunks"}]}]}

        quiz = CourseAssistant(chunks(), FakeClient()).quiz(["week5"], "RAG", 1)
        self.assertEqual(quiz.questions[0].question, "What does RAG retrieve?")
        self.assertEqual(quiz.questions[0].sources[0].locator, "Slide 10")

    def test_library_deduplicates_and_removes_searchable_content(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "notes.txt"
            source.write_text("Course fact.\n\nSecond section.", encoding="utf-8")
            library = MaterialLibrary(root / "data/index/chunks.jsonl", root / "data")
            added, skipped, count = library.add([source])
            self.assertEqual(added, ["notes"])
            self.assertEqual(count, 2)
            added_again, skipped_again, _ = library.add([source])
            self.assertEqual(added_again, [])
            self.assertIn("already indexed", skipped_again[0])
            self.assertEqual(library.remove(["notes"]), 2)
            self.assertEqual(library.chunks, [])

    def test_library_deduplicates_same_content_from_different_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first, second = root / "a" / "notes.txt", root / "b" / "notes.txt"
            first.parent.mkdir(); second.parent.mkdir()
            first.write_text("Same course fact.", encoding="utf-8")
            second.write_text("Same course fact.", encoding="utf-8")
            library = MaterialLibrary(root / "data/index/chunks.jsonl", root / "data")
            library.add([first])
            added, skipped, count = library.add([second])
            self.assertEqual((added, count), ([], 0))
            self.assertIn("already indexed", skipped[0])

    def test_missing_information_returns_grounded_fallback(self):
        class BadClient:
            def complete_json(self, prompt, image_paths=None):
                return {"answer": "Invented", "sources": [{"source_id": "missing"}]}

        result = CourseAssistant(chunks(), BadClient()).answer("Who won the 2034 World Cup?")
        self.assertEqual(result.sources, [])
        self.assertIn("not found", result.answer)


if __name__ == "__main__":
    unittest.main()
