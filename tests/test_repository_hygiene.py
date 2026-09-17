from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_required_project_docs_exist():
    for relative_path in ("README.md", "CONTRIBUTING.md", ".env.example"):
        assert (ROOT / relative_path).is_file()


def test_example_configuration_contains_no_real_secret_shape():
    contents = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "replace-with-local-dummy-value" in contents
    assert "BEGIN " + "PRIVATE KEY" not in contents


def test_course_materials_are_ignored():
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "materials/" in gitignore
    assert "*.pdf" in gitignore


def test_class_service_configuration_is_documented_without_key():
    env_example = (ROOT / ".env.example").read_text(encoding="utf-8")
    service_doc = (ROOT / "docs" / "class-services.md").read_text(encoding="utf-8")
    for endpoint in (":9002/v2/embed", ":9003/v1/embeddings", ":9004/rerank", ":9005/v1/chat/completions"):
        assert endpoint in env_example
        assert endpoint in service_doc
    assert "64" + "18" not in env_example
    assert "64" + "18" not in service_doc
