"""
Safety guardrails — PII detection and prompt injection defense.

These checks run on every incoming message before it reaches the agent.
"""

import re

# Common PII patterns
_SSN_PATTERN = re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b")
_CREDIT_CARD_PATTERN = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")
_PHONE_PATTERN = re.compile(r"\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")

# Prompt injection patterns
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+a", re.IGNORECASE),
    re.compile(r"forget\s+(all\s+)?your\s+(rules|instructions)", re.IGNORECASE),
    re.compile(r"system\s*prompt", re.IGNORECASE),
    re.compile(r"act\s+as\s+(if\s+)?you\s+(are|were)", re.IGNORECASE),
]


def detect_pii(text: str) -> dict:
    """
    Scan text for common PII patterns.

    Returns:
        dict with 'has_pii' (bool), 'types' (list of detected PII types),
        and 'warning' (str).
    """
    found = []

    if _SSN_PATTERN.search(text):
        found.append("SSN")
    if _CREDIT_CARD_PATTERN.search(text):
        found.append("credit_card")
    if _PHONE_PATTERN.search(text):
        found.append("phone_number")

    if found:
        return {
            "has_pii": True,
            "types": found,
            "warning": (
                f"Detected possible PII in message: {', '.join(found)}. "
                f"Please do not share sensitive information in chat. "
                f"Our agent will never ask for your full SSN or credit card number."
            ),
        }

    return {"has_pii": False, "types": [], "warning": ""}


def detect_prompt_injection(text: str) -> dict:
    """
    Check for common prompt injection attempts.

    Returns:
        dict with 'is_injection' (bool) and 'pattern' (str).
    """
    for pattern in _INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            return {
                "is_injection": True,
                "pattern": match.group(),
            }

    return {"is_injection": False, "pattern": ""}
