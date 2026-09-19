import hashlib
import re
from typing import Any
from app.ingestion.models import ColumnProfile
INJECTION_PATTERNS = re.compile(r"(?i)(ignore\s+(all\s+)?previous|system\s+prompt|developer\s+message|tool\s+call|execute\s+command|jailbreak)")
EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
PHONE_RE = re.compile(r"(?<!\w)\+?\d[\d\s().-]{7,}\d(?!\w)")
def mask_text(value: str) -> str: return PHONE_RE.sub("[MASKED_PHONE]", EMAIL_RE.sub("[MASKED_EMAIL]", value))
def safe_sample(value: Any) -> Any:
    if not isinstance(value, str): return value
    if INJECTION_PATTERNS.search(value): return "[REDACTED_UNTRUSTED_INSTRUCTION]"
    return mask_text(value)[:80]
def model_safe_column(column: ColumnProfile) -> dict[str, Any]:
    payload = column.model_dump(mode="json"); payload["masked_samples"] = [safe_sample(item) for item in column.masked_samples[:3]]; return payload
def value_hash(value: Any) -> str: return hashlib.sha256(repr(value).encode()).hexdigest()
