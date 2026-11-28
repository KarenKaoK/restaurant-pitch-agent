"""Section O: the real catalog, mapping table and gold labels are valid (L3)."""

import pytest

from conftest import REAL_DATA_DIR
from pitch_agent.evaluation.labels import load_gold_labels
from pitch_agent.loaders import load_agent_data


@pytest.fixture(scope="module")
def data():
    return load_agent_data(REAL_DATA_DIR)


def test_tc_x01_catalog(data):
    assert len(data.catalog) == 6
    assert data.catalog["dish-ai-phone-assistant"].requires == "dish-professional-reservation"


def test_tc_x02_mapping(data):
    ids = data.mapping.category_ids
    assert len(ids) == 21 and len(set(ids)) == 21
    for category_id in ids:
        assert set(data.mapping.category(category_id).product_ids) <= set(data.catalog)


def test_tc_x03_gold_labels(data):
    labels = load_gold_labels(REAL_DATA_DIR / "eval" / "expected.csv", data.restaurants, data.catalog)
    assert len(labels) == 15
    assert {label.restaurant_id for label in labels} <= set(data.restaurants)
