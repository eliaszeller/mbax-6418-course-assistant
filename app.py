from __future__ import annotations

import os
from pathlib import Path

import gradio as gr

from course_assistant.config import Settings
from course_assistant.engine import CourseAssistant, OpenAICompatibleClient
from course_assistant.library import MaterialLibrary

INDEX = Path("data/index/chunks.jsonl")
MAX_QUIZ = 8
if not INDEX.exists():
    raise SystemExit("Build the index first: python scripts/build_index.py <course files or folders>")

library = MaterialLibrary(INDEX, Path("data"))
materials = library.materials
assistant = CourseAssistant(library.chunks, OpenAICompatibleClient(Settings.from_env()))


def short_name(material: str) -> str:
    for week in range(1, 20):
        if f"Week {week}" in material:
            return f"Week {week}: " + material.split(f"Week {week} - ", 1)[-1].rsplit(" v", 1)[0]
    return material


material_labels = {short_name(value): value for value in materials}


def refresh_library():
    global materials, material_labels, assistant
    materials = library.materials
    material_labels = {short_name(value): value for value in materials}
    assistant = CourseAssistant(library.chunks, OpenAICompatibleClient(Settings.from_env()))


def scope_summary(selected_labels):
    selected_materials = set(selected_values(selected_labels))
    scoped = [chunk for chunk in library.chunks if chunk.material in selected_materials]
    slide_count = len({(chunk.material, chunk.locator) for chunk in scoped})
    material_count = len(selected_materials)
    material_label = "lecture deck" if material_count == 1 else "lecture decks"
    slide_label = "slide/page" if slide_count == 1 else "slides/pages"
    record_label = "searchable record" if len(scoped) == 1 else "searchable records"
    return f"""<section class='hero'><div class='eyebrow'>Leeds School of Business</div>
    <h1>MBAX 6418 Course Assistant</h1>
    <p>Ask grounded questions and practice with quizzes built from the original lecture materials.</p>
    <div class='statbar'><span><strong>{material_count}</strong> {material_label}</span>
    <span><strong>{slide_count}</strong> {slide_label}</span>
    <span><strong>{len(scoped)}</strong> {record_label}</span></div></section>"""


def add_uploads(files, current_selection):
    if not files:
        return "Choose at least one supported file.", gr.update(), gr.update(), scope_summary(current_selection)
    added, skipped, added_records = library.add([Path(str(uploaded)) for uploaded in files])
    refresh_library()
    labels = list(material_labels)
    selected = list(dict.fromkeys([*(current_selection or []), *[short_name(name) for name in added]]))
    selected = [label for label in selected if label in labels]
    if added:
        message = f"**Indexed {len(added)} file{'s' if len(added) != 1 else ''}** as {added_records} searchable text and visual records."
    else:
        message = "No new files were indexed."
    if skipped:
        message += "\n\nSkipped: " + ", ".join(skipped)
    return (message, gr.update(choices=labels, value=selected),
            gr.update(choices=labels, value=[]), scope_summary(selected))


def remove_materials(labels, current_selection):
    targets = selected_values(labels)
    removed = library.remove(targets)
    refresh_library()
    choices = list(material_labels)
    selected = [label for label in (current_selection or []) if label in choices]
    message = f"Removed {len(targets)} material{'s' if len(targets) != 1 else ''} and {removed} searchable records."
    return (message, gr.update(choices=choices, value=selected),
            gr.update(choices=choices, value=[]), scope_summary(selected))


def selected_values(labels):
    return [material_labels.get(label, label) for label in (labels or [])]


def format_sources(sources):
    if not sources:
        return "", []
    lines, images = ["### Evidence"], []
    for number, source in enumerate(sources, 1):
        lines.append(f"**{number}. {source.document} · {source.locator}**\n\n> {source.excerpt}")
        if source.image_path:
            images.append((source.image_path, f"{source.document} · {source.locator}"))
    return "\n\n".join(lines), images


def ask(question, selected, topic):
    if not question or not question.strip():
        return "Please enter a question.", "", [], "Waiting for a question"
    try:
        result = assistant.answer(question.strip(), selected_values(selected) or None, topic.strip())
        citations, images = format_sources(result.sources)
        status = f"Used {len(result.sources)} verified source{'s' if len(result.sources) != 1 else ''}"
        return result.answer, citations, images, status
    except Exception as exc:
        return "I could not reach the class model service.", "", [], f"Service error: {type(exc).__name__}"


def make_quiz(selected, topic, count):
    hidden = [gr.update(visible=False, choices=[], value=None) for _ in range(MAX_QUIZ)]
    try:
        quiz = assistant.quiz(selected_values(selected) or materials, topic.strip(), int(count))
        updates = []
        for index in range(MAX_QUIZ):
            if index < len(quiz.questions):
                item = quiz.questions[index]
                updates.append(gr.update(visible=True, choices=item.choices, value=None,
                                         label=f"{index + 1}. {item.question}"))
            else:
                updates.append(hidden[index])
        return [*updates, quiz.model_dump(mode="json"),
                f"Quiz ready: {len(quiz.questions)} questions. Solutions stay hidden until submission."]
    except Exception as exc:
        return [*hidden, {}, f"Could not generate the quiz: {type(exc).__name__}"]


def grade(*values):
    answers, key = values[:-1], values[-1]
    questions = key.get("questions", []) if isinstance(key, dict) else []
    if not questions:
        return "Generate a quiz first."
    correct, details = 0, []
    for index, item in enumerate(questions):
        chosen = answers[index] if index < len(answers) else None
        expected = item["choices"][item["answer_index"]]
        is_correct = chosen == expected
        correct += int(is_correct)
        marker = "✓" if is_correct else "✗"
        source_lines = []
        for source in item.get("sources", []):
            source_lines.append(
                f"> **{source['document']} · {source['locator']}** — {source.get('excerpt', '')}"
            )
        details.append(
            f"### {marker} Question {index + 1}\n"
            f"**Correct answer:** {expected}\n\n{item['explanation']}\n\n"
            + ("\n\n".join(source_lines) if source_lines else "*No validated source returned.*")
        )
    percent = round(100 * correct / len(questions))
    return f"## Score: {correct}/{len(questions)} ({percent}%)\n\n" + "\n\n".join(details)


CSS = """
.gradio-container {max-width:1180px !important; margin:0 auto !important;}
.hero {padding:30px 32px; border-radius:22px; background:linear-gradient(135deg,#111827,#292524); color:#f8fafc !important; margin-bottom:18px;}
.hero h1 {font-size:2.25rem; margin:0 0 8px; letter-spacing:-.03em; color:#f8fafc !important;}
.hero p {color:#e7e5e4 !important; margin:0; font-size:1.05rem;}
.hero .eyebrow {font-size:.75rem; font-weight:700; letter-spacing:.14em; color:#fbbf24 !important; text-transform:uppercase; margin-bottom:9px;}
.hero .statbar {display:flex; gap:22px; flex-wrap:wrap; margin-top:18px; color:#d6d3d1 !important; font-size:.9rem;}
.hero .statbar span {color:#d6d3d1 !important;}
.hero .statbar strong {color:#f8fafc !important;}
.panel {border:1px solid #e7e5e4 !important; border-radius:18px !important; padding:8px !important;}
.answer-card {min-height:130px;}
.status {font-size:.82rem; color:#78716c;}
footer {display:none !important;}
"""

theme = gr.themes.Soft(primary_hue="orange", secondary_hue="gray", radius_size="lg")
with gr.Blocks(title="MBAX 6418 Course Assistant") as demo:
    hero = gr.HTML(scope_summary(list(material_labels)))

    with gr.Row(equal_height=False):
        with gr.Column(scale=1, min_width=280):
            with gr.Group(elem_classes="panel"):
                gr.Markdown("### Study scope")
                selected = gr.CheckboxGroup(list(material_labels), value=list(material_labels), label="Course materials")
                topic = gr.Textbox(label="Optional topic focus", placeholder="e.g., quantization, prompting, RAG")
                gr.Markdown("Selections apply to both questions and quizzes.", elem_classes="status")
            with gr.Group(elem_classes="panel"):
                gr.Markdown("### Add your own materials")
                uploads = gr.File(
                    label="Upload decks or supporting files",
                    file_count="multiple",
                    type="filepath",
                    file_types=[".pptx", ".ppt", ".odp", ".pdf", ".docx", ".md", ".txt"],
                )
                index_button = gr.Button("Add to study library")
                upload_status = gr.Markdown(
                    "PowerPoint, OpenDocument, PDF, Word, Markdown, and text. Maximum 150 MB per file.",
                    elem_classes="status",
                )
                remove_picker = gr.Dropdown(list(material_labels), multiselect=True, label="Remove materials")
                remove_button = gr.Button("Remove from library", variant="stop")
                index_button.click(add_uploads, [uploads, selected], [upload_status, selected, remove_picker, hero])
                remove_button.click(remove_materials, [remove_picker, selected], [upload_status, selected, remove_picker, hero])
                selected.change(scope_summary, selected, hero)
        with gr.Column(scale=3):
            with gr.Tabs():
                with gr.Tab("Ask the course"):
                    question = gr.Textbox(label="Your question", lines=3,
                        placeholder="How does prompt caching reduce time-to-first-token?")
                    ask_button = gr.Button("Find an evidence-backed answer", variant="primary", size="lg")
                    gr.Examples(
                        examples=[["What is the difference between vibe coding and agentic coding?"],
                                  ["Why does chunking matter in a RAG system?"],
                                  ["How should I write and verify a useful bug report?"]],
                        inputs=question, label="Try an example")
                    ask_status = gr.Markdown("Ready", elem_classes="status")
                    answer = gr.Markdown("### Your answer will appear here", elem_classes="answer-card")
                    with gr.Accordion("Sources and exact excerpts", open=True):
                        citations = gr.Markdown()
                    evidence = gr.Gallery(label="Original slide evidence", columns=2, height="auto", object_fit="contain")
                    ask_button.click(ask, [question, selected, topic], [answer, citations, evidence, ask_status])
                    question.submit(ask, [question, selected, topic], [answer, citations, evidence, ask_status])

                with gr.Tab("Practice quiz"):
                    with gr.Row():
                        count = gr.Slider(1, MAX_QUIZ, value=5, step=1, label="Number of questions")
                        quiz_button = gr.Button("Generate quiz", variant="primary")
                    quiz_status = gr.Markdown("Choose materials and generate a quiz.", elem_classes="status")
                    quiz_key = gr.State({})
                    radios = [gr.Radio([], label=f"Question {i+1}", visible=False) for i in range(MAX_QUIZ)]
                    grade_button = gr.Button("Submit answers and reveal explanations", variant="secondary")
                    feedback = gr.Markdown()
                    quiz_button.click(make_quiz, [selected, topic, count], [*radios, quiz_key, quiz_status])
                    grade_button.click(grade, [*radios, quiz_key], feedback)

    gr.Markdown("Responses are constrained to retrieved course evidence. Always verify important claims against the displayed source.", elem_classes="status")

demo.launch(
    server_name=os.getenv("GRADIO_SERVER_NAME", "0.0.0.0"),
    server_port=int(os.getenv("PORT", os.getenv("GRADIO_SERVER_PORT", "8060"))),
    share=os.getenv("GRADIO_SHARE", "false").lower() in {"1", "true", "yes"},
    allowed_paths=[str(Path("data/index/assets").resolve())],
    theme=theme,
    css=CSS,
)
