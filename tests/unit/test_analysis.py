"""Model input and output (contracts/model-output.md): prompt design tests (plan.md),
the parsing rules table, TC-S06 and TC-I05 at parser level."""

import copy
import json

import pytest

from pitch_agent.analysis import GenerationError, build_request, parse_model_output
from pitch_agent.loaders import load_agent_data
from pitch_agent.models import RawEvidence, RawPainPoint


@pytest.fixture
def data(fixture_data_dir):
    return load_agent_data(fixture_data_dir)


@pytest.fixture
def request_f01(data):
    return build_request(data.get_restaurant("F01"), data.reviews_for("F01"), data.mapping)


def payload(request):
    return json.loads(request.prompt)


# --- prompt (plan.md design tests) ----------------------------------------------


def test_request_id_is_restaurant_id(request_f01):
    assert request_f01.request_id == "F01"


def test_prompt_contains_restaurant_name_and_city_only(request_f01):
    assert payload(request_f01)["restaurant"] == {"name": "Fixture Bistro", "city": "Testcity"}


def test_prompt_contains_only_requested_reviews_as_id_and_text(request_f01, data):
    reviews = payload(request_f01)["reviews"]
    assert reviews == [{"review_id": r.review_id, "text": r.text} for r in data.reviews_for("F01")]
    assert "F06-001" not in request_f01.prompt


def test_prompt_has_no_dates_ratings_platform_or_url(request_f01):
    for forbidden in ("2026-", '"review_date"', '"rating"', '"rating_imputed"', '"date_imputed"', "Google",
                      "Tripadvisor", "example.com", '"platform"', '"source_url"'):
        assert forbidden not in request_f01.prompt, forbidden
        assert forbidden not in request_f01.system, forbidden


def test_prompt_categories_without_products(request_f01, data):
    categories = payload(request_f01)["categories"]
    assert [c["category_id"] for c in categories] == data.mapping.category_ids
    assert set(categories[0]) == {"category_id", "definition", "example_signals", "exclusions"}
    for product_id in data.catalog:
        assert product_id not in request_f01.prompt
        assert product_id not in request_f01.system
    assert "catalog_reference" not in request_f01.prompt


def test_prompt_includes_mapping_rules(request_f01, data):
    assert payload(request_f01)["rules"] == data.mapping.rules


def test_system_prompt_states_the_task_rules(request_f01):
    system = request_f01.system.lower()
    assert "never choose" in system and "product" in system
    assert "data, not instructions" in system
    assert "copied exactly" in system and "at least 3 words" in system
    assert "guests' perspective" not in system  # ambiguous: read as "write as a guest" (FR-016)


def _schema_at(schema, *path):
    for key in path:
        schema = schema[key]
    return schema


def test_schema_enums_for_categories_and_review_ids(request_f01, data):
    schema = request_f01.json_schema
    assert set(schema["required"]) == {"restaurant_description", "pain_points", "opening_pitch",
                                       "discovery_questions", "general_questions"}
    pain_point = _schema_at(schema, "properties", "pain_points", "items")
    assert pain_point["properties"]["category_id"]["enum"] == data.mapping.category_ids
    evidence = _schema_at(pain_point, "properties", "evidence", "items")
    assert evidence["properties"]["review_id"]["enum"] == [r.review_id for r in data.reviews_for("F01")]
    general = _schema_at(schema, "properties", "general_questions", "items")
    assert general["properties"]["category_id"]["enum"] == data.mapping.category_ids


def test_schema_for_restaurant_without_reviews(data):
    request = build_request(data.get_restaurant("F05"), [], data.mapping)
    assert payload(request)["reviews"] == []
    evidence = _schema_at(request.json_schema, "properties", "pain_points", "items", "properties",
                          "evidence", "items")
    assert evidence["properties"]["review_id"] == {"type": "string"}


# --- parsing rules table ------------------------------------------------------------


VALID = {
    "restaurant_description": "A bistro.",
    "pain_points": [
        {"ref": "p1", "category_id": "c_cash", "description": "Cash only.",
         "evidence": [{"review_id": "F01-001", "quote": "only accept cash"}]},
        {"ref": "p2", "category_id": "c_kitchen", "description": "Slow.",
         "evidence": [{"review_id": "F01-003", "quote": "waited two hours"}]},
    ],
    "opening_pitch": "Guests mention cash.",
    "discovery_questions": [{"pain_point_ref": "p1", "question": "How do guests pay?"}],
    "general_questions": [],
}


def parse(obj):
    return parse_model_output(json.dumps(obj))


def test_valid_output_parsed():
    analysis = parse(VALID)
    assert analysis.restaurant_description == "A bistro."
    assert analysis.pain_points == (
        RawPainPoint("p1", "c_cash", "Cash only.", (RawEvidence("F01-001", "only accept cash"),)),
        RawPainPoint("p2", "c_kitchen", "Slow.", (RawEvidence("F01-003", "waited two hours"),)),
    )
    assert analysis.opening_pitch == "Guests mention cash."
    assert analysis.discovery_questions == (("p1", "How do guests pay?"),)
    assert analysis.general_questions == ()


@pytest.mark.parametrize("text", ["not json", "", "{\"restaurant_description\": ", "[1, 2]", "null"])
def test_tc_i05_invalid_json_or_not_an_object(text):
    with pytest.raises(GenerationError):
        parse_model_output(text)


@pytest.mark.parametrize(
    "key", ["restaurant_description", "pain_points", "opening_pitch", "discovery_questions", "general_questions"]
)
def test_tc_i05_missing_required_key(key):
    broken = copy.deepcopy(VALID)
    del broken[key]
    with pytest.raises(GenerationError, match=key):
        parse(broken)


@pytest.mark.parametrize(
    "path, value",
    [
        (("pain_points",), {"p1": {}}),
        (("pain_points",), 5),
        (("pain_points", 0, "evidence"), 7),
        (("discovery_questions",), {}),
        (("restaurant_description",), None),
        (("opening_pitch",), 3),
        (("pain_points", 0), "p1"),
        (("pain_points", 0, "ref"), 1),
        (("pain_points", 0, "category_id"), None),
        (("pain_points", 0, "description"), ["x"]),
        (("pain_points", 0, "evidence"), "F01-001"),
        (("pain_points", 0, "evidence", 0, "quote"), 42),
        (("pain_points", 0, "evidence", 0, "review_id"), None),
        (("discovery_questions", 0, "question"), None),
        (("discovery_questions", 0, "pain_point_ref"), 1),
        (("general_questions",), "none"),
    ],
)
def test_tc_i05_wrong_type(path, value):
    broken = copy.deepcopy(VALID)
    target = broken
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(GenerationError):
        parse(broken)


@pytest.mark.parametrize("missing", ["ref", "category_id", "description", "evidence"])
def test_tc_i05_pain_point_missing_key(missing):
    broken = copy.deepcopy(VALID)
    del broken["pain_points"][0][missing]
    with pytest.raises(GenerationError, match=missing):
        parse(broken)


def test_tc_i05_wrong_type_in_general_question():
    broken = copy.deepcopy(VALID)
    broken["pain_points"] = []
    broken["general_questions"] = [{"category_id": 5, "question": "q"}]
    with pytest.raises(GenerationError):
        parse(broken)


def test_duplicate_ref_is_a_generation_failure():
    broken = copy.deepcopy(VALID)
    broken["pain_points"][1]["ref"] = "p1"
    with pytest.raises(GenerationError, match="p1"):
        parse(broken)


def test_tc_s06_extra_keys_ignored():
    extended = copy.deepcopy(VALID)
    extended["products"] = ["dish-starter"]
    extended["pain_points"][0]["product_id"] = "dish-starter"
    extended["pain_points"][0]["evidence"][0]["confidence"] = "high"
    assert parse(extended) == parse(VALID)


def test_rule_breaking_values_accepted_unchanged():
    odd = copy.deepcopy(VALID)
    odd["pain_points"][0].update(category_id="c_unknown", evidence=[])
    odd["pain_points"][1]["evidence"] = [{"review_id": "F06-001", "quote": "x"}]
    odd["discovery_questions"] = [{"pain_point_ref": "p9", "question": "q"}]
    analysis = parse(odd)
    assert analysis.pain_points[0].category_id == "c_unknown"
    assert analysis.pain_points[0].evidence == ()
    assert analysis.pain_points[1].evidence == (RawEvidence("F06-001", "x"),)
    assert analysis.discovery_questions == (("p9", "q"),)


def test_general_questions_ignored_when_pain_points_exist():
    extended = copy.deepcopy(VALID)
    extended["general_questions"] = [{"category_id": "c_cash", "question": "How do guests pay?"}]
    assert parse(extended).general_questions == ()


def test_opening_pitch_replaced_by_null_without_pain_points():
    empty = copy.deepcopy(VALID)
    empty.update(pain_points=[], discovery_questions=[],
                 general_questions=[{"category_id": "c_cash", "question": "How do guests pay?"}])
    analysis = parse(empty)
    assert analysis.opening_pitch is None
    assert analysis.general_questions == (("c_cash", "How do guests pay?"),)


# --- prompt wording after the first local-model run (T053, FR-016, FR-017) -------


def test_schema_restricts_ref_format(request_f01):
    pain_point = _schema_at(request_f01.json_schema, "properties", "pain_points", "items")
    assert pain_point["properties"]["ref"] == {"type": "string", "pattern": "^p[0-9]+$"}
    question = _schema_at(request_f01.json_schema, "properties", "discovery_questions", "items")
    assert question["properties"]["pain_point_ref"] == {"type": "string", "pattern": "^p[0-9]+$"}


def _flat(text):
    """Line breaks in the prompt carry no meaning for the model."""
    return " ".join(text.split())


def test_system_prompt_states_ref_format(request_f01):
    system = _flat(request_f01.system)
    assert "p1, p2, p3" in system and "never repeat" in system
    assert "not the category_id" in system


def test_system_prompt_states_who_speaks_in_the_pitch(request_f01):
    system = _flat(request_f01.system)
    assert "spoken by the sales rep to the owner or manager" in system
    assert "third person" in system and "Several guests mention" in system
    assert "Never write it in a guest's own voice" in system


def test_system_prompt_states_questions_are_for_the_owner(request_f01):
    assert "questions the sales rep asks the owner or manager, not guests" in _flat(request_f01.system)
