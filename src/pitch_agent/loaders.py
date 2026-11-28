"""Load and validate the agent's input data (FR-002, FR-002a, FR-003, FR-013a, FR-014).

The agent reads only ``data_dir/processed/`` and ``data_dir/products/`` (research R13).
"""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from pathlib import Path

from pitch_agent.models import Mapping, PainPointCategory, Product, Restaurant, Review

MAPPING_FILE = "pain-point-product-mapping.json"

RESTAURANT_REQUIRED = ("restaurant_id", "name", "city", "status", "segment")
SEGMENTS = ("independent", "chain")

REVIEW_REQUIRED = ("review_id", "restaurant_id", "text", "text_source", "platform", "source_url")
REVIEW_OPTIONAL = ("review_date", "date_imputed", "rating", "rating_imputed")
TEXT_SOURCES = ("original", "translated", "expanded")


class LoadError(Exception):
    """Input data is missing or invalid."""


class UnknownRestaurantError(LookupError):
    """The requested restaurant ID is not in the data (FR-004)."""

    def __init__(self, restaurant_id: str):
        super().__init__(f"Unknown restaurant: {restaurant_id}")
        self.restaurant_id = restaurant_id


# ---------------------------------------------------------------------------
# CSV files
# ---------------------------------------------------------------------------


def read_bytes(path: Path, name: str | None = None) -> bytes:
    try:
        return Path(path).read_bytes()
    except OSError as e:
        raise LoadError(f"{name or Path(path).name}: cannot read file: {e}") from e


def _read_csv(path: Path, required: tuple[str, ...], name: str | None = None,
              content: bytes | None = None) -> list[tuple[int, dict[str, str]]]:
    """Return ``(row_number, row)`` pairs; the header is row 1.

    UTF-8 only; a byte order mark (as written by Excel) is accepted. Errors name the
    file as ``name`` (default: the file name). ``content`` is the file's bytes if the
    caller has already read them."""
    name = name or path.name
    content = read_bytes(path, name) if content is None else content
    try:
        reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig"), newline=""))
        missing = [c for c in required if c not in (reader.fieldnames or [])]
        if missing:
            raise LoadError(f"{name}: missing column(s): {', '.join(missing)}")
        rows = list(reader)
    except UnicodeDecodeError as e:
        raise LoadError(f"{name}: not UTF-8 ({e.reason} at byte {e.start})") from e
    except csv.Error as e:
        raise LoadError(f"{name}: invalid CSV ({e})") from e
    return [(i + 2, {k: (v or "") for k, v in row.items() if k is not None}) for i, row in enumerate(rows)]


def _require_values(path: Path, row_number: int, row: dict[str, str], fields: tuple[str, ...]) -> None:
    for name in fields:
        if not row[name].strip():
            raise LoadError(f"{path.name} row {row_number}: empty required value '{name}'")


def load_restaurants(path: Path) -> dict[str, Restaurant]:
    path = Path(path)
    restaurants: dict[str, Restaurant] = {}
    for row_number, row in _read_csv(path, RESTAURANT_REQUIRED):
        _require_values(path, row_number, row, RESTAURANT_REQUIRED)
        rid = row["restaurant_id"]
        if rid in restaurants:
            raise LoadError(f"{path.name} row {row_number}: duplicate restaurant_id '{rid}'")
        if "/" in rid or "\\" in rid or rid in (".", ".."):
            raise LoadError(
                f"{path.name} row {row_number}: invalid restaurant_id {rid!r} "
                "(it names card files: no '/' or '\\', not '.' or '..')"
            )
        if row["segment"] not in SEGMENTS:
            raise LoadError(
                f"{path.name} row {row_number}: invalid segment '{row['segment']}' "
                f"(allowed: {', '.join(SEGMENTS)})"
            )
        restaurants[rid] = Restaurant(
            restaurant_id=rid,
            name=row["name"],
            city=row["city"],
            address=row.get("address", ""),
            status=row["status"],
            segment=row["segment"],
        )
    return restaurants


def load_reviews(path: Path, restaurants: dict[str, Restaurant]) -> list[Review]:
    path = Path(path)
    reviews: list[Review] = []
    seen: set[str] = set()
    for row_number, row in _read_csv(path, REVIEW_REQUIRED):
        _require_values(path, row_number, row, REVIEW_REQUIRED)
        review_id = row["review_id"]
        if review_id in seen:
            raise LoadError(f"{path.name} row {row_number}: duplicate review_id '{review_id}'")
        seen.add(review_id)
        if row["text_source"] not in TEXT_SOURCES:
            raise LoadError(
                f"{path.name} row {row_number}: invalid text_source '{row['text_source']}' "
                f"(allowed: {', '.join(TEXT_SOURCES)})"
            )
        if row["restaurant_id"] not in restaurants:
            raise LoadError(f"{path.name} row {row_number}: unknown restaurant_id '{row['restaurant_id']}'")
        # Only the documented review fields are kept (FR-005).
        fields = {name: row[name] for name in REVIEW_REQUIRED}
        fields.update({name: row.get(name, "") for name in REVIEW_OPTIONAL})
        reviews.append(Review(**fields))
    return reviews


# ---------------------------------------------------------------------------
# Catalog (research R10)
# ---------------------------------------------------------------------------


def _parse_frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise LoadError(f"{path.name}: missing frontmatter")
    values: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return values
        if not line.strip():
            continue
        key, sep, value = line.partition(":")
        if not sep:
            raise LoadError(f"{path.name}: invalid frontmatter line: {line!r}")
        values[key.strip()] = value.strip()
    raise LoadError(f"{path.name}: frontmatter is not closed with '---'")


def load_catalog(products_dir: Path) -> dict[str, Product]:
    products_dir = Path(products_dir)
    catalog: dict[str, Product] = {}
    for path in sorted(products_dir.glob("*.md")):
        meta = _parse_frontmatter(path)
        for key in ("product_id", "name", "category"):
            if not meta.get(key):
                raise LoadError(f"{path.name}: missing required frontmatter key '{key}'")
        product_id = meta["product_id"]
        if product_id in catalog:
            raise LoadError(f"{path.name}: duplicate product_id '{product_id}'")
        catalog[product_id] = Product(
            product_id=product_id,
            name=meta["name"],
            category=meta["category"],
            requires=meta.get("requires") or None,
        )
    for product in catalog.values():
        if product.requires is not None and product.requires not in catalog:
            raise LoadError(
                f"product '{product.product_id}' requires unknown product '{product.requires}'"
            )
    return catalog


# ---------------------------------------------------------------------------
# Mapping table
# ---------------------------------------------------------------------------


def load_mapping(path: Path, catalog: dict[str, Product]) -> Mapping:
    path = Path(path)
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise LoadError(f"{path.name}: cannot read mapping: {e}") from e
    if not isinstance(doc, dict) or not isinstance(doc.get("categories"), list):
        raise LoadError(f"{path.name}: 'categories' list is missing")

    categories: list[PainPointCategory] = []
    seen: set[str] = set()
    for index, raw in enumerate(doc["categories"]):
        if not isinstance(raw, dict) or not raw.get("category_id"):
            raise LoadError(f"{path.name}: category #{index + 1} has no category_id")
        cid = raw["category_id"]
        if cid in seen:
            raise LoadError(f"{path.name}: duplicate category_id '{cid}'")
        seen.add(cid)
        if not raw.get("definition"):
            raise LoadError(f"{path.name}: category '{cid}' is missing 'definition'")
        if not isinstance(raw.get("product_ids"), list):
            raise LoadError(f"{path.name}: category '{cid}' is missing 'product_ids'")
        for product_id in raw["product_ids"]:
            if product_id not in catalog:
                raise LoadError(f"{path.name}: category '{cid}' maps to unknown product '{product_id}'")
        categories.append(
            PainPointCategory(
                category_id=cid,
                definition=raw["definition"],
                product_ids=tuple(raw["product_ids"]),
                example_signals=tuple(raw.get("example_signals") or ()),
                exclusions=tuple(raw.get("exclusions") or ()),
                catalog_reference=raw.get("catalog_reference"),
            )
        )
    rules = doc.get("rules") or {}
    return Mapping(categories=tuple(categories), rules=dict(rules))


# ---------------------------------------------------------------------------
# All agent data
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AgentData:
    restaurants: dict[str, Restaurant]
    reviews: list[Review]
    catalog: dict[str, Product]
    mapping: Mapping

    def get_restaurant(self, restaurant_id: str) -> Restaurant:
        try:
            return self.restaurants[restaurant_id]
        except KeyError:
            raise UnknownRestaurantError(restaurant_id) from None

    def reviews_for(self, restaurant_id: str) -> list[Review]:
        """Only the given restaurant's reviews, in file order (FR-003)."""
        return [r for r in self.reviews if r.restaurant_id == restaurant_id]


def load_agent_data(data_dir: Path) -> AgentData:
    data_dir = Path(data_dir)
    restaurants = load_restaurants(data_dir / "processed" / "restaurants.csv")
    reviews = load_reviews(data_dir / "processed" / "reviews.csv", restaurants)
    catalog = load_catalog(data_dir / "products")
    mapping = load_mapping(data_dir / "products" / MAPPING_FILE, catalog)
    return AgentData(restaurants=restaurants, reviews=reviews, catalog=catalog, mapping=mapping)
