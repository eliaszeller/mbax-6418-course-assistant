# Course Assistant

A Python course assistant that answers questions and generates practice quizzes from course materials downloaded from Canvas.

## Project goal

Build a grounded, multimodal course assistant that:

- accepts course files such as PDF, PPTX, DOCX, and common text formats;
- preserves extracted text, source locations, and original page/slide images;
- answers questions with hybrid retrieval using keyword, text-embedding, and visual-embedding search;
- acknowledges missing information instead of inventing answers or citations;
- generates fixed-answer multiple-choice quizzes with scores and explanations;
- shows document/page/slide/section references with supporting excerpts or screenshots.

## Collaboration model

This repository is intentionally set up for parallel alternatives:

1. Start from `main`.
2. Create one branch per design, for example `team/<name>-baseline`.
3. Keep changes scoped and include automated checks.
4. Open a pull request describing tradeoffs, test results, and limitations.
5. Compare branches against the same evaluation checklist before selecting a foundation.
6. The selected implementation will be extended on `main` after review.

Do not commit course files, API keys, endpoint credentials, generated indexes, or student data.

## Planned architecture

```text
Canvas files
  -> parser / page-slide renderer
  -> text chunks + source metadata       visual page/slide records
  -> keyword index + text vector index  visual vector index
                  \                    /
                   candidate merge + multimodal reranking
                                |
                 answer or quiz generation with evidence
                                |
                 schema validation + source-support checks
                                |
                         Python interface (planned Gradio)
```

Class services at `dobolyi.com` (ports 9001 and above) may provide document parsing, vision-capable generation, text/visual embeddings, and multimodal reranking. Connection details are intentionally not stored here. Ask the project team for the current endpoint formats and credentials, then provide them through server-side environment variables or an ignored local configuration file.

## Local setup

The implementation is being developed incrementally. The expected setup is:

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pytest
```

Use dummy values in examples. Never place real keys in source, browser code, logs, screenshots, documentation, or test artifacts.

## Supported input policy

The finished app will document its tested formats explicitly. The target set is PDF, PPTX, DOCX, TXT, and Markdown, with page/slide rendering where the format supports it. Unsupported or malformed files should receive a clear error rather than partial, untraceable ingestion.

## Evidence policy

Every answer and quiz explanation must carry structured source records. A source record should identify the document, page/slide or section, a text excerpt or image reference, and enough metadata to reproduce the evidence. If retrieval does not support an answer, the assistant must say that the materials do not establish it.

## Evaluation and status

The project is currently in repository setup. Add benchmark materials only when permitted by the course. Each design comparison should record:

- retrieval configuration and model/service versions;
- latency and failure behavior;
- grounded-answer and citation-support checks;
- quiz answer-key stability;
- visual evidence coverage;
- known limitations and unchecked cases.

Screenshots and findings will be added to `docs/` as the interface becomes available.

## License

TBD by the project team.
