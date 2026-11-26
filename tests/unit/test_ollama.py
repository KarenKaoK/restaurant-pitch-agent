"""Design tests (plan.md, no case ID): Ollama provider against a local stub HTTP server."""

import json
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from pitch_agent.llm import LLMError, LLMRequest
from pitch_agent.llm.ollama import OllamaLLM

REQUEST = LLMRequest(system="You classify reviews.", prompt='{"reviews": []}',
                     json_schema={"type": "object"}, request_id="F01")
MODEL = "granite4.2:8b"


class StubOllama:
    """Records POST bodies; answers with a configurable status, body and delay."""

    def __init__(self):
        self.requests = []
        self.status = 200
        self.body = {"message": {"role": "assistant", "content": '{"ok": true}'}}
        self.delay = 0.0
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers["Content-Length"])
                stub.requests.append({"path": self.path, "body": json.loads(self.rfile.read(length))})
                time.sleep(stub.delay)
                payload = stub.body if isinstance(stub.body, bytes) else json.dumps(stub.body).encode()
                self.send_response(stub.status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *args):
                pass

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.host = f"http://127.0.0.1:{self.server.server_port}"
        threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True).start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def stub():
    server = StubOllama()
    yield server
    server.close()


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def assert_names_host_and_model(error, host):
    message = str(error)
    assert host in message and MODEL in message
    return message


def test_request_body(stub):
    OllamaLLM(MODEL, host=stub.host).generate(REQUEST)
    assert len(stub.requests) == 1
    sent = stub.requests[0]
    assert sent["path"] == "/api/chat"
    assert sent["body"] == {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You classify reviews."},
            {"role": "user", "content": '{"reviews": []}'},
        ],
        "format": {"type": "object"},
        "stream": False,
        "think": False,
        "options": {"temperature": 0, "seed": 42, "num_ctx": 8192},
    }


def test_returns_message_content(stub):
    assert OllamaLLM(MODEL, host=stub.host).generate(REQUEST) == '{"ok": true}'


def test_provider_and_model(stub):
    llm = OllamaLLM(MODEL, host=stub.host)
    assert (llm.provider, llm.model) == ("ollama", MODEL)


def test_connection_refused():
    host = f"http://127.0.0.1:{free_port()}"
    with pytest.raises(LLMError) as e:
        OllamaLLM(MODEL, host=host).generate(REQUEST)
    message = assert_names_host_and_model(e.value, host)
    assert "cannot connect" in message and "ollama serve" in message
    assert "ollama pull" not in message


@pytest.mark.parametrize("status", [400, 404, 500])
def test_http_error(stub, status):
    stub.status = status
    stub.body = {"error": f"model '{MODEL}' not found"}
    with pytest.raises(LLMError) as e:
        OllamaLLM(MODEL, host=stub.host).generate(REQUEST)
    message = assert_names_host_and_model(e.value, stub.host)
    assert f"HTTP {status}" in message and "not found" in message
    assert f"ollama pull {MODEL}" in message
    assert "ollama serve" not in message


def test_timeout(stub):
    stub.delay = 1.0
    with pytest.raises(LLMError) as e:
        OllamaLLM(MODEL, host=stub.host, timeout=0.2).generate(REQUEST)
    message = assert_names_host_and_model(e.value, stub.host)
    assert "timed out after 0.2 s" in message and "PITCH_AGENT_LLM_TIMEOUT" in message
    assert "ollama serve" not in message and "ollama pull" not in message


@pytest.mark.parametrize("body", [{"message": {"role": "assistant"}}, {"done": True}, b"not json",
                                  {"message": {"content": 5}}])
def test_missing_message_content(stub, body):
    stub.body = body
    with pytest.raises(LLMError) as e:
        OllamaLLM(MODEL, host=stub.host).generate(REQUEST)
    message = assert_names_host_and_model(e.value, stub.host)
    assert "message.content" in message


def test_host_and_timeout_from_environment(stub):
    llm = OllamaLLM(MODEL, env={"OLLAMA_HOST": stub.host, "PITCH_AGENT_LLM_TIMEOUT": "12.5"})
    assert (llm.host, llm.timeout) == (stub.host, 12.5)
    assert llm.generate(REQUEST) == '{"ok": true}'


def test_defaults():
    llm = OllamaLLM(MODEL, env={})
    assert (llm.host, llm.timeout) == ("http://localhost:11434", 900.0)

