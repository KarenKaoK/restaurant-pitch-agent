"""Design tests (no case ID): mock provider of contracts/llm-interface.md."""

import json

import pytest

from pitch_agent.llm import LLMError, LLMRequest
from pitch_agent.llm.mock import EMPTY_ANALYSIS, MockLLM

OUTPUT = {"restaurant_description": "d", "pain_points": [], "opening_pitch": "p",
          "discovery_questions": [], "general_questions": [{"category_id": "c_cash", "question": "q"}]}


def request(request_id="F01"):
    return LLMRequest(system="s", prompt="p", json_schema={}, request_id=request_id)


def test_mapping_response_returned_as_json_text():
    assert json.loads(MockLLM({"F01": OUTPUT}).generate(request())) == OUTPUT


def test_raw_response_returned_as_is():
    assert MockLLM({"F01": {"raw": "not json {"}}).generate(request()) == "not json {"


def test_error_response_raises_llm_error():
    with pytest.raises(LLMError, match="boom"):
        MockLLM({"F01": {"error": "boom"}}).generate(request())


def test_unconfigured_restaurant_gets_empty_analysis():
    assert EMPTY_ANALYSIS == {"restaurant_description": "", "pain_points": [], "opening_pitch": "",
                              "discovery_questions": [], "general_questions": []}
    assert json.loads(MockLLM({}).generate(request("F05"))) == EMPTY_ANALYSIS
    assert json.loads(MockLLM().generate(request("F05"))) == EMPTY_ANALYSIS


def test_callable_response():
    llm = MockLLM(lambda req: {"raw": f"answer for {req.request_id}"})
    assert llm.generate(request("F06")) == "answer for F06"


def test_json_file_response(tmp_path):
    path = tmp_path / "responses.json"
    path.write_text(json.dumps({"F01": OUTPUT}), encoding="utf-8")
    assert json.loads(MockLLM(path).generate(request())) == OUTPUT
    assert json.loads(MockLLM(str(path)).generate(request())) == OUTPUT


def test_calls_recorded():
    llm = MockLLM({})
    assert llm.calls == []
    first, second = request("F01"), request("F06")
    llm.generate(first)
    llm.generate(second)
    assert llm.calls == [first, second]


def test_provider_and_model():
    assert (MockLLM().provider, MockLLM().model) == ("mock", "mock")
    assert MockLLM(model="other").model == "other"
