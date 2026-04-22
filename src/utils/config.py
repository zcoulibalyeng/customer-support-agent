"""
Centralised configuration.

All tuneable parameters live here. Agent code never hardcodes
model names, thresholds, or paths — it reads from this module.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
SEED_DIR = DATA_DIR / "seed"
VECTORSTORE_DIR = DATA_DIR / "vectorstore"
DB_PATH = DATA_DIR / "support.db"

# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o")
LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0"))

# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# ---------------------------------------------------------------------------
# Guardrails
# ---------------------------------------------------------------------------
MAX_AUTO_REFUND: float = float(os.getenv("MAX_AUTO_REFUND", "50.00"))
MAX_EVAL_ITERATIONS: int = int(os.getenv("MAX_EVAL_ITERATIONS", "5"))

# ---------------------------------------------------------------------------
# Email (optional — set to enable real email sending)
# ---------------------------------------------------------------------------
SMTP_HOST: str = os.getenv("SMTP_HOST", "")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER: str = os.getenv("SMTP_USER", "")
SMTP_PASS: str = os.getenv("SMTP_PASS", "")
EMAIL_FROM: str = os.getenv("EMAIL_FROM", "support@example.com")
