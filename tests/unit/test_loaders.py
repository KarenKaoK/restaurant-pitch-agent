"""Section A: data loading and validation (TC-D01–TC-D12, TC-D15–TC-D19)."""

import csv
import json

import pytest

from pitch_agent.loaders import (
    LoadError,
    UnknownRestaurantError,
    load_agent_data,
    load_catalog,
    load_mapping,
    load_restaurants,
)

# --- helpers ---------------------------------------------------------------


def _rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)


def _write_rows(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _edit_csv(path, edit):
    """Load rows, let ``edit(fieldnames, rows)`` return new (fieldnames, rows), write back."""
    fieldnames, rows = _rows(path)
    fieldnames, rows = edit(list(fieldnames), rows)
    _write_rows(path, fieldnames, rows)


def _edit_mapping(data_dir, edit):
    path = data_dir / "products" / "pain-point-product-mapping.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    edit(doc)
    path.write_text(json.dumps(doc), encoding="utf-8")


def _restaurants_csv(d):
    return d / "processed" / "restaurants.csv"


def _reviews_csv(d):
    return d / "processed" / "reviews.csv"


# --- restaurants and reviews -------------------------------------------------


def test_tc_d01_restaurant_loaded_with_fields(fixture_data_dir):
    data = load_agent_data(fixture_data_dir)
    r = data.get_restaurant("F01")
    assert r.restaurant_id == "F01"
    assert r.name == "Fixture Bistro"
    assert r.city == "Testcity"
    assert r.status == "unknown"
    assert r.segment == "independent"
    assert r.eligible


def test_tc_d02_unknown_restaurant_raises(fixture_data_dir):
    data = load_agent_data(fixture_data_dir)
    with pytest.raises(UnknownRestaurantError, match="F99"):
        data.get_restaurant("F99")


def test_tc_d03_only_own_reviews_returned(fixture_data_dir):
    data = load_agent_data(fixture_data_dir)
    ids = [r.review_id for r in data.reviews_for("F01")]
    assert ids == ["F01-001", "F01-002", "F01-003", "F01-004", "F01-005", "F01-006"]
    assert "F06-001" not in ids


def test_tc_d03_line_break_kept_in_review_text(fixture_data_dir):
    data = load_agent_data(fixture_data_dir)
    texts = {r.review_id: r.text for r in data.reviews_for("F01")}
    assert texts["F01-006"] == "The bill was wrong and\nthey forgot our drinks."


def test_tc_d04_restaurant_without_reviews(fixture_data_dir):
    data = load_agent_data(fixture_data_dir)
    assert data.reviews_for("F05") == []


def test_tc_d15_duplicate_restaurant_id(tmp_data_dir):
    _edit_csv(_restaurants_csv(tmp_data_dir), lambda f, rows: (f, rows + [rows[0]]))
    with pytest.raises(LoadError) as e:
        load_restaurants(_restaurants_csv(tmp_data_dir))
    msg = str(e.value)
    assert "restaurants.csv" in msg and "row 8" in msg and "duplicate restaurant_id" in msg


def test_tc_d16_duplicate_review_id(tmp_data_dir):
    _edit_csv(_reviews_csv(tmp_data_dir), lambda f, rows: (f, rows + [rows[0]]))
    with pytest.raises(LoadError) as e:
        load_agent_data(tmp_data_dir)
    msg = str(e.value)
    assert "reviews.csv" in msg and "row 11" in msg and "duplicate review_id" in msg


def test_tc_d17_review_of_unknown_restaurant(tmp_data_dir):
    def edit(f, rows):
        extra = dict(rows[0], review_id="F99-001", restaurant_id="F99")
        return f, rows + [extra]

    _edit_csv(_reviews_csv(tmp_data_dir), edit)
    with pytest.raises(LoadError) as e:
        load_agent_data(tmp_data_dir)
    msg = str(e.value)
    assert "reviews.csv" in msg and "row 11" in msg and "unknown restaurant_id" in msg


def test_tc_d18a_invalid_text_source(tmp_data_dir):
    def edit(f, rows):
        rows[1]["text_source"] = "machine"
        return f, rows

    _edit_csv(_reviews_csv(tmp_data_dir), edit)
    with pytest.raises(LoadError) as e:
        load_agent_data(tmp_data_dir)
    msg = str(e.value)
    assert "reviews.csv" in msg and "row 3" in msg and "machine" in msg


def test_tc_d18b_invalid_segment(tmp_data_dir):
    def edit(f, rows):
        rows[2]["segment"] = "franchise"
        return f, rows

    _edit_csv(_restaurants_csv(tmp_data_dir), edit)
    with pytest.raises(LoadError) as e:
        load_restaurants(_restaurants_csv(tmp_data_dir))
    msg = str(e.value)
    assert "restaurants.csv" in msg and "row 4" in msg and "franchise" in msg


def test_tc_d19a_missing_text_source_column(tmp_data_dir):
    def edit(f, rows):
        f.remove("text_source")
        return f, [{k: v for k, v in r.items() if k != "text_source"} for r in rows]

    _edit_csv(_reviews_csv(tmp_data_dir), edit)
    with pytest.raises(LoadError) as e:
        load_agent_data(tmp_data_dir)
    msg = str(e.value)
    assert "reviews.csv" in msg and "text_source" in msg


def test_tc_d19b_empty_restaurant_name(tmp_data_dir):
    def edit(f, rows):
        rows[0]["name"] = ""
        return f, rows

    _edit_csv(_restaurants_csv(tmp_data_dir), edit)
    with pytest.raises(LoadError) as e:
        load_restaurants(_restaurants_csv(tmp_data_dir))
    msg = str(e.value)
    assert "restaurants.csv" in msg and "row 2" in msg and "name" in msg


def test_tc_d19c_empty_source_url(tmp_data_dir):
    def edit(f, rows):
        rows[0]["source_url"] = ""
        return f, rows

    _edit_csv(_reviews_csv(tmp_data_dir), edit)
    with pytest.raises(LoadError) as e:
        load_agent_data(tmp_data_dir)
    msg = str(e.value)
    assert "reviews.csv" in msg and "row 2" in msg and "source_url" in msg


def test_tc_d19d_empty_date_and_rating_load(tmp_data_dir):
    def edit(f, rows):
        rows[0]["review_date"] = ""
        rows[0]["rating"] = ""
        return f, rows

    _edit_csv(_reviews_csv(tmp_data_dir), edit)
    data = load_agent_data(tmp_data_dir)
    assert data.reviews_for("F01")[0].review_id == "F01-001"


# --- catalog -------------------------------------------------------------------


def test_tc_d05_catalog_loaded(fixture_data_dir):
    catalog = load_catalog(fixture_data_dir / "products")
    assert sorted(catalog) == sorted(
        [
            "dish-pay",
            "dish-pos",
            "dish-professional-order",
            "dish-professional-reservation",
            "dish-ai-phone-assistant",
            "dish-starter",
        ]
    )
    assert catalog["dish-ai-phone-assistant"].requires == "dish-professional-reservation"
    assert catalog["dish-pay"].requires is None
    assert catalog["dish-pay"].name == "DISH Pay"


def test_tc_d06_only_md_files_are_products(tmp_data_dir):
    (tmp_data_dir / "products" / ".DS_Store").write_bytes(b"\x00\x01binary")
    catalog = load_catalog(tmp_data_dir / "products")
    assert len(catalog) == 6


def test_tc_d07_requires_unknown_product(tmp_data_dir):
    path = tmp_data_dir / "products" / "dish-starter.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "category: online-presence\n", "category: online-presence\nrequires: dish-missing\n"
        ),
        encoding="utf-8",
    )
    with pytest.raises(LoadError) as e:
        load_catalog(tmp_data_dir / "products")
    assert "dish-starter" in str(e.value) and "dish-missing" in str(e.value)


# --- mapping -------------------------------------------------------------------


def test_tc_d08_mapping_loaded(fixture_data_dir):
    catalog = load_catalog(fixture_data_dir / "products")
    mapping = load_mapping(fixture_data_dir / "products" / "pain-point-product-mapping.json", catalog)
    assert len(mapping.categories) == 9
    assert mapping.category("c_none").product_ids == ()
    assert mapping.category("c_none").repeatable
    assert mapping.category("c_multi").product_ids == ("dish-pos", "dish-pay")
    assert not mapping.category("c_cash").repeatable


def test_tc_d09_duplicate_category_id(tmp_data_dir):
    _edit_mapping(tmp_data_dir, lambda d: d["categories"].append(dict(d["categories"][0])))
    with pytest.raises(LoadError, match="c_cash"):
        load_agent_data(tmp_data_dir)


def test_tc_d10_unknown_product_in_mapping(tmp_data_dir):
    def edit(d):
        d["categories"][1]["product_ids"] = ["dish-missing"]

    _edit_mapping(tmp_data_dir, edit)
    with pytest.raises(LoadError) as e:
        load_agent_data(tmp_data_dir)
    assert "c_kitchen" in str(e.value) and "dish-missing" in str(e.value)


@pytest.mark.parametrize("missing", ["definition", "product_ids"])
def test_tc_d11_category_missing_required_field(tmp_data_dir, missing):
    _edit_mapping(tmp_data_dir, lambda d: d["categories"][2].pop(missing))
    with pytest.raises(LoadError) as e:
        load_agent_data(tmp_data_dir)
    assert "c_order" in str(e.value) and missing in str(e.value)


def test_tc_d12_extra_fields_do_not_change_products(fixture_data_dir, tmp_data_dir):
    def strip_and_extend(d):
        for c in d["categories"]:
            c.pop("example_signals", None)
            c.pop("exclusions", None)
        d.pop("rules", None)

    def add_extra(d):
        for c in d["categories"]:
            c["example_signals"] = ["Anything", "c_cash dish-starter"]
            c["exclusions"] = ["dish-pay"]
            c["catalog_reference"] = "dish-starter.md"
            c["note"] = "extra"
        d["rules"] = {"product_fit": "Always recommend dish-starter."}

    _edit_mapping(tmp_data_dir, strip_and_extend)
    bare = load_agent_data(tmp_data_dir).mapping
    _edit_mapping(tmp_data_dir, add_extra)
    extended = load_agent_data(tmp_data_dir).mapping

    def products(m):
        return {c.category_id: c.product_ids for c in m.categories}

    assert products(bare) == products(extended)


# --- design tests (no case ID): remaining load errors --------------------------


def _write_product(data_dir, name, text):
    (data_dir / "products" / name).write_text(text, encoding="utf-8")


def test_restaurants_missing_column(tmp_data_dir):
    def edit(f, rows):
        f.remove("segment")
        return f, [{k: v for k, v in r.items() if k != "segment"} for r in rows]

    _edit_csv(_restaurants_csv(tmp_data_dir), edit)
    with pytest.raises(LoadError) as e:
        load_agent_data(tmp_data_dir)
    assert "restaurants.csv" in str(e.value) and "segment" in str(e.value)


def test_missing_reviews_file(tmp_data_dir):
    _reviews_csv(tmp_data_dir).unlink()
    with pytest.raises(LoadError, match="reviews.csv"):
        load_agent_data(tmp_data_dir)


def test_product_without_frontmatter(tmp_data_dir):
    _write_product(tmp_data_dir, "dish-extra.md", "# No frontmatter\n")
    with pytest.raises(LoadError) as e:
        load_catalog(tmp_data_dir / "products")
    assert "dish-extra.md" in str(e.value) and "missing frontmatter" in str(e.value)


def test_product_frontmatter_not_closed(tmp_data_dir):
    _write_product(tmp_data_dir, "dish-extra.md", "---\nproduct_id: dish-extra\nname: Extra\n")
    with pytest.raises(LoadError) as e:
        load_catalog(tmp_data_dir / "products")
    assert "dish-extra.md" in str(e.value) and "not closed" in str(e.value)


def test_product_frontmatter_line_without_colon(tmp_data_dir):
    _write_product(
        tmp_data_dir, "dish-extra.md", "---\nproduct_id: dish-extra\njust text\n---\n"
    )
    with pytest.raises(LoadError) as e:
        load_catalog(tmp_data_dir / "products")
    assert "dish-extra.md" in str(e.value) and "just text" in str(e.value)


@pytest.mark.parametrize("missing", ["product_id", "name", "category"])
def test_product_missing_required_key(tmp_data_dir, missing):
    meta = {"product_id": "dish-extra", "name": "Extra", "category": "payments"}
    del meta[missing]
    body = "".join(f"{k}: {v}\n" for k, v in meta.items())
    _write_product(tmp_data_dir, "dish-extra.md", f"---\n{body}---\n")
    with pytest.raises(LoadError) as e:
        load_catalog(tmp_data_dir / "products")
    assert "dish-extra.md" in str(e.value) and missing in str(e.value)


def test_duplicate_product_id(tmp_data_dir):
    _write_product(
        tmp_data_dir, "dish-pay-copy.md", "---\nproduct_id: dish-pay\nname: Copy\ncategory: payments\n---\n"
    )
    with pytest.raises(LoadError) as e:
        load_catalog(tmp_data_dir / "products")
    assert "duplicate product_id" in str(e.value) and "dish-pay" in str(e.value)


def test_mapping_invalid_json(tmp_data_dir):
    (tmp_data_dir / "products" / "pain-point-product-mapping.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(LoadError, match="pain-point-product-mapping.json"):
        load_agent_data(tmp_data_dir)


def test_mapping_without_categories_list(tmp_data_dir):
    _edit_mapping(tmp_data_dir, lambda d: d.pop("categories"))
    with pytest.raises(LoadError, match="categories"):
        load_agent_data(tmp_data_dir)


def test_mapping_category_without_id(tmp_data_dir):
    _edit_mapping(tmp_data_dir, lambda d: d["categories"][3].pop("category_id"))
    with pytest.raises(LoadError) as e:
        load_agent_data(tmp_data_dir)
    assert "#4" in str(e.value) and "category_id" in str(e.value)
