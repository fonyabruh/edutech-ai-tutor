"""Tests for LLMClient and prompts.py."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.config import Settings
from app.llm.client import LLMClient
from app.llm.prompts import load_prompt


def test_settings_folder_id_interpolates_model_uri():
    """Config.model_post_init replaces {folder_id} when yandex_folder_id is set (line 16)."""
    cfg = Settings(
        yandex_folder_id="my-folder",
        yandex_model_uri="gpt://{folder_id}/yandexgpt/latest",
    )
    assert "my-folder" in cfg.yandex_model_uri
    assert "{folder_id}" not in cfg.yandex_model_uri


def test_settings_no_interpolation_when_folder_id_empty():
    """When yandex_folder_id is empty, URI template is left as-is."""
    cfg = Settings(
        yandex_folder_id="",
        yandex_model_uri="gpt://{folder_id}/yandexgpt/latest",
    )
    assert "{folder_id}" in cfg.yandex_model_uri

# ── prompts.py ────────────────────────────────────────────────────────────────

def test_load_prompt_diagnose_resolves_path():
    """B1: diagnose.yaml found relative to source file, not cwd."""
    msgs = load_prompt(
        "diagnose",
        grade=9, exam="ОГЭ", subject_name="Математика", goal="хороший балл",
        answers_summary="нет данных", mastery_summary="нет данных",
    )
    assert len(msgs) >= 1
    assert any(m["role"] == "user" for m in msgs)


def test_load_prompt_plan_resolves_path():
    """B1: plan.yaml."""
    msgs = load_prompt(
        "plan",
        grade=11, exam="ЕГЭ", subject_name="Математика", goal="excellent",
        topics_priority="1. topic_id=1 (mastery=0.5)",
    )
    assert any(m["role"] == "system" for m in msgs) or any(m["role"] == "user" for m in msgs)


def test_load_prompt_explain_error_resolves_path():
    """B1: explain_error.yaml."""
    msgs = load_prompt(
        "explain_error",
        topic_name="Алгебра", statement="2+2=?", solution="4",
        correct_answer="4", user_answer="5",
    )
    assert len(msgs) >= 1


def test_load_prompt_tutor_chat_resolves_path():
    """B1: tutor_chat.yaml."""
    msgs = load_prompt("tutor_chat", subject_name="Математика", weak_topics="тригонометрия")
    assert len(msgs) >= 1


def test_tutor_chat_no_empty_user_message():
    """B5: tutor_chat system prompt only; no empty user block should appear."""
    msgs = load_prompt("tutor_chat", subject_name="Математика", weak_topics="нет данных")
    user_msgs = [m for m in msgs if m["role"] == "user"]
    for m in user_msgs:
        assert m["text"].strip() != "", "empty user message would pollute LLM context"


def test_load_prompt_renders_variables():
    msgs = load_prompt(
        "diagnose",
        grade=11, exam="ЕГЭ", subject_name="Физика", goal="excellent",
        answers_summary="topic_id=1: верно", mastery_summary="topic_id=1: 0.80",
    )
    full_text = " ".join(m["text"] for m in msgs)
    assert "11" in full_text
    assert "ЕГЭ" in full_text


# ── LLMClient._parse_json ────────────────────────────────────────────────────

def test_parse_json_plain():
    client = LLMClient.__new__(LLMClient)
    result = client._parse_json('{"key": 42}')
    assert result == {"key": 42}


def test_parse_json_strips_backtick_json_wrapper():
    client = LLMClient.__new__(LLMClient)
    text = '```json\n{"key": "value"}\n```'
    assert client._parse_json(text) == {"key": "value"}


def test_parse_json_strips_plain_backtick_wrapper():
    client = LLMClient.__new__(LLMClient)
    text = '```\n{"x": 1}\n```'
    assert client._parse_json(text) == {"x": 1}


def test_parse_json_raises_on_bad_json():
    client = LLMClient.__new__(LLMClient)
    with pytest.raises(json.JSONDecodeError):
        client._parse_json("not json at all")


# ── LLMClient._post / chat ───────────────────────────────────────────────────

def _make_yandex_response(text):
    return {"result": {"alternatives": [{"message": {"text": text}}]}}


async def test_chat_returns_text():
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = _make_yandex_response("hello")

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=resp)

    with patch("app.llm.client.httpx.AsyncClient", return_value=mock_client):
        client = LLMClient.__new__(LLMClient)
        client.cfg = MagicMock(yandex_model_uri="uri")
        client._headers = {}
        result = await client.chat([{"role": "user", "text": "test"}])
    assert result == "hello"


async def test_chat_json_format_appends_instruction():
    """chat with response_format='json' injects JSON instruction into system."""
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = _make_yandex_response('{"ok": true}')

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=resp)

    with patch("app.llm.client.httpx.AsyncClient", return_value=mock_client):
        client = LLMClient.__new__(LLMClient)
        client.cfg = MagicMock(yandex_model_uri="uri")
        client._headers = {}
        result = await client.chat(
            [{"role": "system", "text": "be helpful"}], response_format="json"
        )
    assert result == {"ok": True}
    # verify JSON instruction was appended
    call_body = mock_client.post.call_args.kwargs["json"]
    assert "JSON" in call_body["messages"][0]["text"]


async def test_post_retries_on_connect_error():
    """_post retries on ConnectError up to 3 times then raises."""
    call_count = 0

    async def failing_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        raise httpx.ConnectError("no connection")

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(side_effect=failing_post)

    with patch("app.llm.client.httpx.AsyncClient", return_value=mock_client):
        with patch("app.llm.client.asyncio.sleep", new_callable=AsyncMock):
            client = LLMClient.__new__(LLMClient)
            client.cfg = MagicMock(yandex_model_uri="uri")
            client._headers = {}
            with pytest.raises(httpx.ConnectError):
                await client._post({})
    assert call_count == 4  # 1 initial + 3 retries


async def test_stream_yields_chunks():
    """stream() yields delta text from SSE."""
    line1 = 'data: {"result": {"alternatives": [{"message": {"text": "hello "}}]}}'
    line2 = 'data: {"result": {"alternatives": [{"message": {"text": "world"}}]}}'

    async def fake_aiter_lines():
        for line in [line1, line2]:
            yield line

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.aiter_lines = fake_aiter_lines

    class FakeStream:
        async def __aenter__(self): return mock_resp
        async def __aexit__(self, *a): pass

    mock_http = MagicMock()
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=False)
    mock_http.stream = MagicMock(return_value=FakeStream())

    with patch("app.llm.client.httpx.AsyncClient", return_value=mock_http):
        client = LLMClient.__new__(LLMClient)
        client.cfg = MagicMock(yandex_model_uri="uri")
        client._headers = {}
        chunks = [c async for c in client.stream([{"role": "user", "text": "x"}])]

    assert chunks == ["hello ", "world"]


async def test_stream_skips_non_data_lines_and_empty_delta():
    """stream() ignores lines not starting with 'data:' and empty delta texts (52->51, 60->51)."""
    line_blank = ""
    line_event = "event: update"
    line_empty_delta = 'data: {"result": {"alternatives": [{"message": {"text": ""}}]}}'
    line_real = 'data: {"result": {"alternatives": [{"message": {"text": "ok"}}]}}'

    async def fake_aiter_lines():
        for line in [line_blank, line_event, line_empty_delta, line_real]:
            yield line

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.aiter_lines = fake_aiter_lines

    class FakeStream:
        async def __aenter__(self): return mock_resp
        async def __aexit__(self, *a): pass

    mock_http = MagicMock()
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=False)
    mock_http.stream = MagicMock(return_value=FakeStream())

    with patch("app.llm.client.httpx.AsyncClient", return_value=mock_http):
        client = LLMClient.__new__(LLMClient)
        client.cfg = MagicMock(yandex_model_uri="uri")
        client._headers = {}
        chunks = [c async for c in client.stream([{"role": "user", "text": "x"}])]

    assert chunks == ["ok"]
