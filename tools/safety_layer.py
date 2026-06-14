import re


class SafetyLayer:
    """
    Central guardrail for high-impact actions.

    The app may prepare recommendations, quotes, checkout summaries, booking
    options, cancellation drafts, or healthcare triage. It must not claim that
    it completed a purchase, payment, booking, cancellation, or diagnosis.
    """

    ACTION_RULES = {
        "buy": {
            "patterns": [r"\bbuy\b", r"\bpurchase\b", r"\border\b", r"\bcheckout\b", r"\badd to cart\b"],
            "label": "purchase",
            "message": "No purchase has been made. Please explicitly confirm before any checkout or order step.",
        },
        "pay": {
            "patterns": [r"\bpay\b", r"\bpayment\b", r"\bcharge\b", r"\bcharged\b", r"\bcard\b", r"\bwallet\b"],
            "label": "payment",
            "message": "No payment has been made and no card has been charged. Please explicitly confirm before any payment step.",
        },
        "book": {
            "patterns": [r"\bbook\b", r"\bbooking\b", r"\breserve\b", r"\breservation\b", r"\bticket\b"],
            "label": "booking",
            "message": "No booking or reservation has been confirmed. Please explicitly confirm before any booking step.",
        },
        "cancel": {
            "patterns": [r"\bcancel\b", r"\bcancellation\b", r"\brefund\b", r"\breschedule\b"],
            "label": "cancellation",
            "message": "No booking, order, or service has been cancelled. Please explicitly confirm before any cancellation or refund step.",
        },
        "diagnose": {
            "patterns": [r"\bdiagnos", r"\bmedical\b", r"\bsymptom\b", r"\btreatment\b", r"\bmedicine\b"],
            "label": "medical diagnosis",
            "message": "This is not a medical diagnosis. Please consult a licensed medical professional for medical decisions.",
        },
    }

    UNSAFE_REPLACEMENTS = [
        (r"\border confirmed\b", "order prepared for review"),
        (r"\border placed\b", "order prepared for review"),
        (r"\bpurchase completed\b", "purchase prepared for review"),
        (r"\bpurchased\b", "selected for review"),
        (r"\bpayment (?:was )?charged\b", "payment was not charged"),
        (r"\bcharged your card\b", "did not charge your card"),
        (r"\bbooking confirmed\b", "booking prepared for review"),
        (r"\breservation confirmed\b", "reservation prepared for review"),
        (r"\bcancellation confirmed\b", "cancellation prepared for review"),
        (r"\bdiagnosis is\b", "non-diagnostic assessment is"),
        (r"\byou have been diagnosed\b", "this is not a diagnosis"),
    ]

    CHECKOUT_BLOCK_RE = re.compile(
        r"\n*---CHECKOUT_FORM---[\s\S]*?---END_CHECKOUT_FORM---\n*",
        re.I,
    )

    def enforce(self, result: dict, query: str = "", route: str = "") -> dict:
        answer = result.get("answer", "") or ""
        detected = self.detect_actions(query, route, answer)

        sanitized = self.CHECKOUT_BLOCK_RE.sub("", answer).strip()
        for pattern, replacement in self.UNSAFE_REPLACEMENTS:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.I)

        if detected:
            sanitized = self.append_confirmation_notice(sanitized, detected)

        result["answer"] = sanitized
        extra = result.setdefault("extra", {})
        extra["safety_layer"] = {
            "checked": True,
            "requires_confirmation": bool(detected),
            "blocked_auto_actions": detected,
            "policy": "Never auto buy, pay, book, cancel, or diagnose.",
        }
        if "checkout" in extra:
            extra["checkout"]["show_checkout_form"] = False
            extra["checkout"]["requires_user_confirmation"] = True
        return result

    def detect_actions(self, query: str, route: str, answer: str) -> list[str]:
        haystack = f"{query}\n{route}\n{answer}".lower()
        detected = []

        route_map = {
            "shopping": ["buy", "pay"],
            "payment": ["pay"],
            "hotel": ["book", "pay"],
            "flight": ["book", "pay"],
            "movie": ["book", "pay"],
            "restaurant": ["book"],
            "train": ["book", "pay"],
            "bus": ["book", "pay"],
            "cab": ["book", "pay"],
            "event": ["book", "pay"],
            "vacation_package": ["book", "pay"],
            "travel": ["book"],
            "cancellation": ["cancel"],
            "healthcare": ["diagnose", "book"],
        }
        for action in route_map.get(route, []):
            if action not in detected:
                detected.append(action)

        for action, rule in self.ACTION_RULES.items():
            if any(re.search(pattern, haystack, re.I) for pattern in rule["patterns"]):
                if action not in detected:
                    detected.append(action)

        return detected

    def append_confirmation_notice(self, answer: str, actions: list[str]) -> str:
        messages = []
        for action in actions:
            message = self.ACTION_RULES[action]["message"]
            if message not in messages:
                messages.append(message)

        notice = (
            "\n\nSafety confirmation required:\n"
            + "\n".join(f"- {message}" for message in messages)
        )
        if notice.strip() in answer:
            return answer
        return answer.rstrip() + notice
