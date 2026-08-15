from types import SimpleNamespace

from backend.lib.application_ai import _response_payload


def test_response_payload_reads_output_text_json():
    response = SimpleNamespace(
        status="completed",
        output_text='{"paragraphs": []}',
        output=[],
    )
    payload, status = _response_payload(response)
    assert status == "ok"
    assert payload == {"paragraphs": []}


def test_response_payload_reads_nested_output_text():
    part = SimpleNamespace(type="output_text", text='{"paragraphs": [{"text": "ok"}]}', parsed=None, refusal=None)
    item = SimpleNamespace(content=[part])
    response = SimpleNamespace(status="completed", output_text="", output=[item])
    payload, status = _response_payload(response)
    assert status == "ok"
    assert payload == {"paragraphs": [{"text": "ok"}]}


def test_response_payload_reports_incomplete_reason():
    response = SimpleNamespace(
        status="incomplete",
        incomplete_details=SimpleNamespace(reason="max_output_tokens"),
        output_text='{"paragraphs": [',
        output=[],
    )
    payload, status = _response_payload(response)
    assert payload is None
    assert status == "openai_incomplete_max_output_tokens"


def test_response_payload_accepts_parsed_structured_content():
    part = SimpleNamespace(parsed={"paragraphs": []}, text=None, refusal=None)
    item = SimpleNamespace(content=[part])
    response = SimpleNamespace(status="completed", output_text="", output=[item])
    payload, status = _response_payload(response)
    assert status == "ok"
    assert payload == {"paragraphs": []}


def test_response_payload_reports_refusal_without_leaking_text():
    part = SimpleNamespace(parsed=None, text=None, refusal="Cannot comply")
    item = SimpleNamespace(content=[part])
    response = SimpleNamespace(status="completed", output_text="", output=[item])
    payload, status = _response_payload(response)
    assert payload is None
    assert status == "openai_refusal"
