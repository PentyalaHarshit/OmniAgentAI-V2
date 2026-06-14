import json
import zipfile

from tools.huge_general_facts import HugeGeneralFacts, normalize_fact_query


def test_normalize_fact_query_keeps_programming_symbols():
    assert normalize_fact_query("Who invented C++?") == "who invented c++"
    assert normalize_fact_query("What is Agentic-RAG?") == "what is agentic rag"


def test_build_index_and_lookup(tmp_path):
    jsonl = tmp_path / "facts.jsonl"
    db = tmp_path / "facts.sqlite"
    jsonl.write_text(
        "\n".join([
            json.dumps({
                "query": "who was ada lovelace",
                "answer": "Ada Lovelace was an English mathematician.",
                "category": "history",
                "source": "test",
            }),
            json.dumps({
                "query": "what is agentic rag",
                "answer": "Agentic RAG combines retrieval with tool-using AI agents.",
                "category": "ai",
                "source": "test",
            }),
        ]),
        encoding="utf-8",
    )

    stats = HugeGeneralFacts.build_index(jsonl, db)
    facts = HugeGeneralFacts(db_path=str(db), jsonl_path=str(tmp_path / "missing.jsonl"))

    assert stats["indexed"] == 2
    assert facts.lookup("Who was Ada Lovelace?") == "Ada Lovelace was an English mathematician."
    assert "tool-using AI agents" in facts.lookup("what is agentic rag")
    assert facts.lookup("Who was the Ada Lovelace?") == "Ada Lovelace was an English mathematician."


def test_lookup_handles_common_query_variants(tmp_path):
    jsonl = tmp_path / "facts.jsonl"
    db = tmp_path / "facts.sqlite"
    jsonl.write_text(
        "\n".join([
            json.dumps({
                "query": "what is cpu",
                "answer": "A CPU executes instructions in a computer.",
            }),
            json.dumps({
                "query": "give a short summary of mars",
                "answer": "Mars is the fourth planet from the Sun.",
            }),
        ]),
        encoding="utf-8",
    )
    HugeGeneralFacts.build_index(jsonl, db)
    facts = HugeGeneralFacts(db_path=str(db), jsonl_path=str(tmp_path / "missing.jsonl"))

    assert facts.lookup("what is a cpu") == "A CPU executes instructions in a computer."
    assert facts.lookup("tell me about cpu") == "A CPU executes instructions in a computer."
    assert facts.lookup("define cpu") == "A CPU executes instructions in a computer."
    assert facts.lookup("give me a short summary of mars") == "Mars is the fourth planet from the Sun."


def test_small_jsonl_fallback_lookup(tmp_path):
    jsonl = tmp_path / "facts.jsonl"
    jsonl.write_text(
        json.dumps({
            "query": "who was hypatia",
            "answer": "Hypatia was a philosopher and mathematician in Alexandria.",
        }),
        encoding="utf-8",
    )
    facts = HugeGeneralFacts(db_path=str(tmp_path / "missing.sqlite"), jsonl_path=str(jsonl))

    assert facts.lookup("Who was Hypatia?") == "Hypatia was a philosopher and mathematician in Alexandria."


def test_build_index_from_zip_jsonl(tmp_path):
    zip_path = tmp_path / "facts.zip"
    db = tmp_path / "facts.sqlite"
    rows = [
        json.dumps({
            "query": "what is europa",
            "answer": "Europa is one of Jupiter's moons.",
            "category": "astronomy",
            "source": "test_zip",
        }),
        json.dumps({
            "query": "what is io",
            "answer": "Io is a volcanically active moon of Jupiter.",
            "category": "astronomy",
            "source": "test_zip",
        }),
    ]
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("million_general_facts.jsonl", "\n".join(rows))

    stats = HugeGeneralFacts.build_index(
        zip_path,
        db,
        zip_entry="million_general_facts.jsonl",
        limit=1,
    )
    facts = HugeGeneralFacts(db_path=str(db), jsonl_path=str(tmp_path / "missing.jsonl"))

    assert stats["indexed"] == 1
    assert facts.lookup("what is europa") == "Europa is one of Jupiter's moons."
    assert facts.lookup("what is io") == ""


def test_million_fact_tool_uses_sqlite_index(tmp_path):
    from tools.million_fact_tool import MillionFactTool

    jsonl = tmp_path / "facts.jsonl"
    db = tmp_path / "facts.sqlite"
    jsonl.write_text(
        json.dumps({
            "query": "what is cpu",
            "answer": "A CPU executes instructions in a computer.",
            "category": "technology",
            "source": "test",
        }),
        encoding="utf-8",
    )
    HugeGeneralFacts.build_index(jsonl, db)

    tool = MillionFactTool(path=str(tmp_path / "missing.jsonl"), db_path=str(db))

    assert tool.lookup("What is CPU?") == "A CPU executes instructions in a computer."
