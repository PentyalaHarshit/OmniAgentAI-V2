import json
import re
from pathlib import Path


class ConversationState:
    def __init__(self, state_file: str = "uploads/conversation_state.json"):
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.state_file.exists():
            self.state_file.write_text("{}", encoding="utf-8")

    def load_all(self):
        try:
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def save_all(self, data):
        self.state_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get(self, session_id: str = "default"):
        data = self.load_all()
        return data.get(session_id, {})

    def set(self, session_id: str, state: dict):
        data = self.load_all()
        data[session_id] = state
        self.save_all(data)

    def clear(self, session_id: str = "default"):
        data = self.load_all()
        if session_id in data:
            del data[session_id]
        self.save_all(data)

    def is_waiting(self, session_id: str = "default"):
        state = self.get(session_id)
        return bool(state.get("active_agent") and state.get("missing_fields"))

    def start_or_update(self, session_id: str, agent_name: str, fields: dict, missing_fields: list[str]):
        state = {
            "active_agent": agent_name,
            "fields": fields,
            "missing_fields": missing_fields
        }
        self.set(session_id, state)
        return state

    def update_from_user_reply(self, session_id: str, user_reply: str):
        state = self.get(session_id)
        if not state:
            return state

        missing = state.get("missing_fields", [])
        fields = state.get("fields", {})

        if missing:
            field = missing[0]
            fields[field] = self.clean_reply(user_reply)

        new_missing = [k for k, v in fields.items() if v == "not provided"]

        state["fields"] = fields
        state["missing_fields"] = new_missing
        self.set(session_id, state)
        return state

    def clean_reply(self, text: str):
        return re.sub(r"\s+", " ", text.strip())
