"""Shared pytest fixtures: data directories and model-output builder."""

import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_DATA_DIR = REPO_ROOT / "tests" / "fixtures" / "data"
REAL_DATA_DIR = REPO_ROOT / "data"


def build_model_output(
    pain_points=None,
    restaurant_description="A fixture restaurant.",
    opening_pitch="Your guests mention a few things worth talking about.",
    discovery_questions=None,
    general_questions=None,
):
    """Build a model-output dict in the shape of contracts/model-output.md.

    ``pain_points`` items may be full dicts, or tuples
    ``(ref, category_id, [(review_id, quote), ...])`` with an optional
    fourth element ``description``.
    """
    built = []
    for item in pain_points or []:
        if isinstance(item, dict):
            built.append(item)
            continue
        ref, category_id, evidence, *rest = item
        built.append(
            {
                "ref": ref,
                "category_id": category_id,
                "description": rest[0] if rest else f"Pain point {ref}",
                "evidence": [{"review_id": rid, "quote": quote} for rid, quote in evidence],
            }
        )
    if discovery_questions is None:
        discovery_questions = [
            {"pain_point_ref": pp["ref"], "question": f"How do you handle {pp['category_id']}?"}
            for pp in built
        ]
    return {
        "restaurant_description": restaurant_description,
        "pain_points": built,
        "opening_pitch": opening_pitch,
        "discovery_questions": discovery_questions,
        "general_questions": general_questions or [],
    }


@pytest.fixture
def fixture_data_dir() -> Path:
    return FIXTURE_DATA_DIR


@pytest.fixture
def real_data_dir() -> Path:
    return REAL_DATA_DIR


@pytest.fixture
def tmp_data_dir(tmp_path) -> Path:
    """A modifiable copy of the fixture data."""
    target = tmp_path / "data"
    shutil.copytree(FIXTURE_DATA_DIR, target)
    return target


@pytest.fixture
def model_output():
    return build_model_output


@pytest.fixture
def fixture_catalog():
    from pitch_agent.loaders import load_catalog

    return load_catalog(FIXTURE_DATA_DIR / "products")


@pytest.fixture
def fixture_mapping(fixture_catalog):
    from pitch_agent.loaders import load_mapping

    return load_mapping(FIXTURE_DATA_DIR / "products" / "pain-point-product-mapping.json", fixture_catalog)


@pytest.fixture
def mock_llm():
    """Factory: ``mock_llm({restaurant_id: response})`` returns a recording MockLLM."""
    from pitch_agent.llm.mock import MockLLM

    return lambda responses=None: MockLLM(responses or {})


class _FailingLLM:
    provider = model = "fail-if-called"

    def generate(self, request):
        pytest.fail(f"the model must not be called (request {request.request_id})")


@pytest.fixture
def failing_llm():
    """Stub LLM that fails the test if it is called."""
    return _FailingLLM()
