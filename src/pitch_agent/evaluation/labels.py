"""Gold labels: read and validate data/eval/expected.csv (FR-027, FR-028).

File-level problems (missing or unreadable file, not UTF-8, missing columns, no
data rows) raise ``LoadError``. Invalid rows are all collected first and then
raised together as ``GoldLabelError``.
"""

from __future__ import annotations

import hashlib

from dataclasses import dataclass
from pathlib import Path

from pitch_agent.loaders import LoadError, _read_csv, read_bytes

COLUMNS = ("restaurant_id", "decision", "must_include", "acceptable", "rationale")
DECISIONS = ("recommend", "no_recommendation", "insufficient_evidence")


@dataclass(frozen=True)
class GoldLabel:
    restaurant_id: str
    decision: str
    must_include: tuple[str, ...]
    acceptable: tuple[str, ...]
    rationale: str


@dataclass(frozen=True)
class LabelError:
    row_number: int
    restaurant_id: str
    reason: str

    def __str__(self) -> str:
        return f"row {self.row_number} ({self.restaurant_id}): {self.reason}"


class GoldLabelError(Exception):
    """One or more invalid rows; ``errors`` lists all of them."""

    def __init__(self, errors: list[LabelError]):
        super().__init__("\n".join(str(e) for e in errors))
        self.errors = errors


def _products(field: str) -> tuple[str, ...]:
    """``;``-separated product IDs; spaces and empty items are ignored."""
    return tuple(item.strip() for item in field.split(";") if item.strip())


def _row_reasons(label: GoldLabel, restaurants: dict, catalog: dict) -> list[str]:
    reasons = []
    if label.restaurant_id not in restaurants:
        reasons.append("unknown restaurant_id")
    if label.decision not in DECISIONS:
        reasons.append(f"invalid decision '{label.decision}'")
    for name in ("must_include", "acceptable"):
        products = getattr(label, name)
        reasons += [f"unknown product '{p}' in {name}" for p in products if p not in catalog]
        reasons += [f"product '{p}' repeated in {name}" for p in dict.fromkeys(products) if products.count(p) > 1]
    reasons += [f"product '{p}' in both must_include and acceptable"
                for p in label.must_include if p in label.acceptable]
    if label.must_include and label.decision != "recommend":
        reasons.append("must_include must be empty unless decision is recommend")
    return reasons


def read_gold_labels(path: Path, restaurants: dict, catalog: dict) -> tuple[list[GoldLabel], str]:
    """The validated labels and the SHA-256 of the bytes they were read from (the file
    is read once, so the hash always matches what was validated)."""
    content = read_bytes(path, str(path))
    return load_gold_labels(path, restaurants, catalog, content), hashlib.sha256(content).hexdigest()


def load_gold_labels(path: Path, restaurants: dict, catalog: dict, content: bytes | None = None) -> list[GoldLabel]:
    path = Path(path)
    rows = _read_csv(path, COLUMNS, name=str(path), content=content)
    if not rows:
        raise LoadError(f"{path}: no labelled restaurants")

    labels, errors, first_row = [], [], {}
    for row_number, row in rows:
        label = GoldLabel(
            restaurant_id=row["restaurant_id"].strip(),
            decision=row["decision"].strip(),
            must_include=_products(row["must_include"]),
            acceptable=_products(row["acceptable"]),
            rationale=row["rationale"],
        )
        reasons = _row_reasons(label, restaurants, catalog)
        if label.restaurant_id in first_row:
            reasons.append(f"duplicate restaurant_id (first in row {first_row[label.restaurant_id]})")
        else:
            first_row[label.restaurant_id] = row_number
        errors += [LabelError(row_number, label.restaurant_id, reason) for reason in reasons]
        labels.append(label)
    if errors:
        raise GoldLabelError(errors)
    return labels
