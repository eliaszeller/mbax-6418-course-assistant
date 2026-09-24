# Proposed GitHub issues

Assign owners before implementation. Each issue includes a completion checklist.

## 1. Confirm class service contracts

- [ ] Record base URL, model name, authentication, request schema, and response schema for every service.
- [ ] Add one redacted request example per service.
- [ ] Confirm upload and payload limits.
- [ ] Confirm whether visual embeddings accept image URLs, data URLs, or multipart files.
- [ ] Owner: unassigned

## 2. Course-material ingestion

- [ ] Extract PDF, PPTX, DOCX, TXT, and Markdown text.
- [ ] Render every PDF page and PowerPoint slide.
- [ ] Preserve filename, page or slide number, and asset path.
- [ ] Add failure fixtures for scanned and malformed documents.
- [ ] Owner: unassigned

## 3. Class embedding and reranking adapters

- [ ] Replace deterministic development embeddings with documented class services.
- [ ] Keep text and visual collections separate.
- [ ] Combine keyword, text-vector, and visual-vector candidates.
- [ ] Compare hybrid retrieval against vector-only retrieval on a fixed question set.
- [ ] Owner: unassigned

## 4. Grounded answer generation

- [ ] Enforce the `answer` and `sources` schema.
- [ ] Reject unknown source IDs and unsupported excerpts.
- [ ] Display source text and original page or slide images.
- [ ] Test missing-information responses.
- [ ] Owner: unassigned

## 5. Practice quizzes

- [ ] Filter by materials and optional topic.
- [ ] Generate validated multiple-choice questions.
- [ ] Keep the answer key in server-side session state.
- [ ] Reveal explanations and citations only after submission or an explicit request.
- [ ] Owner: unassigned

## 6. Release and evaluation

- [ ] Add screenshots without credentials or private data.
- [ ] Run automated tests from a clean environment.
- [ ] Document tested behavior and remaining gaps.
- [ ] Review the README and open a pull request.
- [ ] Owner: unassigned

