import json

from scripts.generate_queries import generate_queries, make_queries


def test_make_queries_skips_short_or_untitled_chunks():
    assert make_queries({"title": "", "text": "x" * 200}) == []
    assert make_queries({"title": "Tiny", "text": "too short"}) == []


def test_generate_queries_writes_expected_jsonl(tmp_path):
    input_file = tmp_path / "chunks.jsonl"
    output_file = tmp_path / "knowledge_queries.jsonl"
    input_file.write_text(
        "\n".join([
            json.dumps({
                "title": "Saladin",
                "source": "Wikipedia",
                "text": "Saladin was the founder of the Ayyubid dynasty. " * 5,
            }),
            json.dumps({
                "title": "Babur",
                "source": "Wikipedia",
                "text": "Babur was the founder of the Mughal Empire. " * 5,
            }),
        ]),
        encoding="utf-8",
    )

    total = generate_queries(
        input_file=input_file,
        output_file=output_file,
        queries_per_chunk=3,
        seed=7,
    )

    rows = [json.loads(line) for line in output_file.read_text(encoding="utf-8").splitlines()]
    assert total == 6
    assert len(rows) == 6
    assert {row["expected_title"] for row in rows} == {"Saladin", "Babur"}
    assert all(row["expected_context"] for row in rows)
