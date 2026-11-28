"""Section L: gold-label validation (FR-027, FR-028)."""

from pathlib import Path

import pytest

from pitch_agent.evaluation.labels import GoldLabel, GoldLabelError, LabelError, load_gold_labels
from pitch_agent.loaders import LoadError, load_agent_data

LABELS = Path(__file__).parents[1] / "fixtures" / "labels"


@pytest.fixture
def load(fixture_data_dir):
    data = load_agent_data(fixture_data_dir)
    return lambda name: load_gold_labels(LABELS / name, data.restaurants, data.catalog)


def row_errors(load, name):
    with pytest.raises(GoldLabelError) as e:
        load(name)
    return e.value.errors


def file_error(load, name):
    with pytest.raises(LoadError) as e:
        load(name)
    return str(e.value)


def test_tc_g01_valid_file(load):
    labels = load("valid.csv")
    assert [label.restaurant_id for label in labels] == ["F01", "F02", "F05"]
    assert labels[1] == GoldLabel("F02", "no_recommendation", (), (), "Closed")


def test_tc_g02_semicolon_list(load):
    assert load("valid.csv")[0].must_include == ("dish-pay", "dish-pos")


def test_tc_g03_blank_lists_are_empty(load):
    f05 = load("valid.csv")[2]
    assert (f05.must_include, f05.acceptable) == ((), ())


def test_tc_g04_unknown_restaurant(load):
    assert row_errors(load, "tc_g04_unknown_restaurant.csv") == [LabelError(2, "F99", "unknown restaurant_id")]


def test_tc_g05_invalid_decision(load):
    assert row_errors(load, "tc_g05_invalid_decision.csv") == [LabelError(2, "F01", "invalid decision 'yes'")]


def test_tc_g06_unknown_product(load):
    assert row_errors(load, "tc_g06_unknown_product.csv") == [
        LabelError(2, "F01", "unknown product 'dish-weblisting' in must_include")]


def test_tc_g07_missing_column(load):
    message = file_error(load, "tc_g07_missing_column.csv")
    assert str(LABELS / "tc_g07_missing_column.csv") in message and "acceptable" in message


def test_tc_g08_duplicate_restaurant(load):
    assert row_errors(load, "tc_g08_duplicate_restaurant.csv") == [
        LabelError(3, "F01", "duplicate restaurant_id (first in row 2)")]


def test_tc_g09_product_in_both_lists(load):
    assert row_errors(load, "tc_g09_product_in_both.csv") == [
        LabelError(2, "F01", "product 'dish-pay' in both must_include and acceptable")]


def test_tc_g10_must_include_without_recommend(load):
    assert row_errors(load, "tc_g10_must_include_without_recommend.csv") == [
        LabelError(2, "F01", "must_include must be empty unless decision is recommend")]


def test_tc_g11_all_invalid_rows_listed(load):
    errors = row_errors(load, "tc_g11_three_invalid_rows.csv")
    assert [(e.row_number, e.restaurant_id) for e in errors] == [(2, "F99"), (4, "F01"), (5, "F05")]


def test_tc_g11_error_message_lists_every_row(load):
    with pytest.raises(GoldLabelError) as e:
        load("tc_g11_three_invalid_rows.csv")
    assert str(e.value).splitlines() == [
        "row 2 (F99): unknown restaurant_id",
        "row 4 (F01): invalid decision 'yes'",
        "row 5 (F05): must_include must be empty unless decision is recommend",
    ]


def test_tc_g12_blank_product_lists_are_valid(load):
    labels = load("tc_g12_blank_lists.csv")
    assert labels[0] == GoldLabel("F01", "recommend", (), ("dish-pay",), "Only acceptable products")
    assert len(labels) == 3


def test_tc_g13_missing_file(load):
    assert str(LABELS / "does_not_exist.csv") in file_error(load, "does_not_exist.csv")


def test_tc_g14_byte_order_mark(load):
    assert load("tc_g14_byte_order_mark.csv") == load("valid.csv")


def test_tc_g15_not_utf8(load):
    message = file_error(load, "tc_g15_latin1.csv")
    assert str(LABELS / "tc_g15_latin1.csv") in message and "not UTF-8" in message


def test_tc_g16_spaces_and_empty_items_ignored(load):
    assert load("tc_g16_list_spacing.csv")[0].must_include == ("dish-pay", "dish-pos")


def test_tc_g17_repeated_product(load):
    assert row_errors(load, "tc_g17_repeated_product.csv") == [
        LabelError(2, "F01", "product 'dish-pos' repeated in acceptable")]


def test_tc_g18_header_only(load):
    message = file_error(load, "tc_g18_header_only.csv")
    assert str(LABELS / "tc_g18_header_only.csv") in message and "no labelled restaurants" in message


def test_tc_g19_file_the_csv_reader_cannot_parse(fixture_data_dir, tmp_path):
    data = load_agent_data(fixture_data_dir)
    path = tmp_path / "labels.csv"
    path.write_text((LABELS / "valid.csv").read_text(encoding="utf-8") + 'F03,recommend,,,"' + "x" * 200_000 + '"\n',
                    encoding="utf-8")
    with pytest.raises(LoadError) as e:
        load_gold_labels(path, data.restaurants, data.catalog)
    assert str(path) in str(e.value) and "invalid CSV" in str(e.value)
