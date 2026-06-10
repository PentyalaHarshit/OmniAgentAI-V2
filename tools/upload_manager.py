import json
import re
import uuid
from pathlib import Path
from fastapi import UploadFile

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

try:
    import docx
except Exception:
    docx = None


class UploadManager:
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.upload_dir / "index.json"

        if not self.index_file.exists():
            self.index_file.write_text("{}", encoding="utf-8")

    def _load(self):
        try:
            return json.loads(self.index_file.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save(self, data):
        self.index_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    async def save_and_index(self, file: UploadFile):
        file_id = str(uuid.uuid4())[:8]
        original_name = file.filename or "uploaded_file"
        safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", original_name)
        stored = f"{file_id}_{safe_name}"

        path = self.upload_dir / stored
        content = await file.read()
        path.write_bytes(content)

        text = self.extract_text(path)

        data = self._load()
        data[file_id] = {
            "file_id": file_id,
            "filename": safe_name,
            "stored_name": stored,
            "path": str(path),
            "size_bytes": len(content),
            "text_chars": len(text),
            "text": text[:200000]
        }
        self._save(data)

        return {
            "file_id": file_id,
            "filename": safe_name,
            "size_bytes": len(content),
            "text_chars": len(text),
            "message": "File uploaded and indexed successfully"
        }

    def extract_text(self, path: Path):
        suffix = path.suffix.lower()

        if suffix == ".txt":
            return path.read_text(encoding="utf-8", errors="ignore")

        if suffix == ".pdf":
            if PdfReader is None:
                return "PDF support not installed. Run: pip install pypdf"
            try:
                reader = PdfReader(str(path))
                return "\n".join((page.extract_text() or "") for page in reader.pages)
            except Exception as e:
                return f"PDF extract error: {e}"

        if suffix == ".docx":
            if docx is None:
                return "DOCX support not installed. Run: pip install python-docx"
            try:
                document = docx.Document(str(path))
                return "\n".join(p.text for p in document.paragraphs)
            except Exception as e:
                return f"DOCX extract error: {e}"

        return "Unsupported file type. Supported file types: txt, pdf, docx."

    def list_files(self):
        data = self._load()
        files = []
        for v in data.values():
            file_exists = Path(v.get("path", "")).exists()
            files.append({
                "file_id": v["file_id"],
                "filename": v["filename"],
                "size_bytes": v["size_bytes"],
                "text_chars": v["text_chars"],
                "exists": file_exists
            })
        return {"files": files}

    def get_context(self, file_id: str, query: str, max_chars: int = 6000):
        data = self._load()
        item = data.get(file_id)
        if not item:
            return ""

        text = item.get("text", "")
        if not text:
            return ""

        q_words = set(re.findall(r"[a-zA-Z0-9]+", query.lower()))
        parts = [p.strip() for p in re.split(r"\n\s*\n|\n", text) if p.strip()]

        scored = []
        for p in parts:
            p_words = set(re.findall(r"[a-zA-Z0-9]+", p.lower()))
            score = len(q_words & p_words)
            if score:
                scored.append((score, p))

        scored.sort(reverse=True, key=lambda x: x[0])
        context = "\n\n".join(p for _, p in scored[:10]) if scored else text[:max_chars]

        return f"File: {item['filename']}\n\n{context[:max_chars]}"
