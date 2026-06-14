from tools.huge_general_facts import HugeGeneralFacts


class MillionFactTool:
    """
    Compatibility wrapper for million-fact lookup.

    The original tool loaded the full JSONL into memory. This wrapper uses the
    SQLite-backed HugeGeneralFacts index so million-row files stay fast and
    memory-friendly.
    """

    def __init__(
        self,
        path: str = "knowledge/million_general_facts.jsonl",
        db_path: str = "knowledge/general_facts.sqlite",
        fuzzy: bool = False,
    ):
        self.path = path
        self.db_path = db_path
        self.fuzzy = fuzzy
        self.index = HugeGeneralFacts(db_path=db_path, jsonl_path=path)

    def lookup(self, query: str) -> str:
        return self.index.lookup(query)


if __name__ == "__main__":
    tool = MillionFactTool()
    while True:
        q = input("Ask: ")
        print(tool.lookup(q) or "No fact found")
