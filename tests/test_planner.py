from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from agents import PlannerError, RunState, generate_plan, message_text
from demo import budget_rows, preview_plan
from models import Settings, WeddingBrief, sample_brief


@pytest.mark.parametrize("budget", ["45000", "100.01", "1337.37", "999999.99"])
def test_budget_total_and_preview_labels(budget):
    brief = sample_brief().model_copy(update={"budget": Decimal(budget)})
    rows = budget_rows(brief)
    assert sum(row["amount"] for row in rows) == brief.budget
    assert all(row["amount"] >= 0 for row in rows)
    result = preview_plan(brief)
    assert result["searches"] == 0 and not result["sources"]
    assert "No AI models or web search were used" in result["markdown"]
    assert brief.wedding_date.strftime("%B %d, %Y") in result["markdown"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("couple", "  "),
        ("location", " "),
        ("guests", 0),
        ("budget", "-10"),
        ("wedding_date", date.today() - timedelta(days=1)),
    ],
)
def test_invalid_brief(field, value):
    data = sample_brief().model_dump()
    data[field] = value
    with pytest.raises(ValidationError):
        WeddingBrief.model_validate(data)


def test_settings_do_not_share_or_export_credentials(monkeypatch, tmp_path):
    import models

    monkeypatch.setattr(models, "ROOT", tmp_path)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    (tmp_path / ".env").write_text("GROQ_API_KEY=file-key\nTAVILY_API_KEY=file-search\n")
    first = Settings.load({"GROQ_API_KEY": "session-one"})
    second = Settings.load({"GROQ_API_KEY": "session-two"})
    assert first.groq_api_key == "session-one"
    assert second.groq_api_key == "session-two"
    assert Settings.load().groq_api_key == "file-key"
    assert "session-one" not in first.model_dump_json()
    assert "session-one" not in repr(first)
    monkeypatch.setenv("GROQ_API_KEY", "environment-key")
    assert Settings.load().groq_api_key == "environment-key"
    monkeypatch.setenv("OPENAI_API_KEY", "unrelated-openai-key")
    assert Settings.load().groq_api_key == "environment-key"


def test_missing_keys_before_provider_initialization():
    with pytest.raises(PlannerError, match="both"):
        generate_plan(sample_brief(), Settings())


def test_search_bounds_and_safe_source_urls():
    state = RunState()
    assert all(state.reserve("searches", 8, "searched") for _ in range(8))
    assert not state.reserve("searches", 8, "searched")
    assert state.searches == 8
    assert all(state.reserve("delegations", 4, "delegated") for _ in range(4))
    assert not state.reserve("delegations", 4, "delegated")
    results = state.add_sources(
        [
            {"url": "javascript:alert(1)", "content": "bad"},
            {"url": "https://venue.example/info", "title": "Venue", "content": "a" * 5000},
            {"url": "https://venue.example/info", "title": "Venue updated"},
        ]
    )
    assert len(results) == 2
    assert len(results[0]["content"]) == 2500
    assert len(state.sources) == 1


def test_content_blocks():
    from langchain_core.messages import AIMessage

    assert message_text(AIMessage(content=[{"type": "text", "text": "A plan"}])) == "A plan"


def test_real_langchain_delegation_and_tavily_boundary(monkeypatch):
    import langchain_openai
    import tavily
    from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
    from langchain_core.messages import AIMessage

    class ScriptedModel(FakeMessagesListChatModel):
        def bind_tools(self, tools, **kwargs):
            return self

    def call(name, args, call_id):
        return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": call_id}])

    model = ScriptedModel(
        responses=[
            call("research_venues_and_vendors", {"query": "100 guests in Santa Barbara"}, "d1"),
            call("search_web", {"topic": "Santa Barbara wedding garden venue capacity"}, "s1"),
            AIMessage(content="Venue evidence https://venue.example/weddings"),
            call(
                "research_budget_and_logistics", {"query": "USD 45000 budget and logistics"}, "d2"
            ),
            call("search_web", {"topic": "Santa Barbara wedding transport costs"}, "s2"),
            AIMessage(content="Logistics evidence https://travel.example/weddings"),
            AIMessage(content="# Executive summary\nA researched wedding plan."),
        ]
    )
    kwargs_seen = {}
    searches = []

    def model_factory(**kwargs):
        kwargs_seen.update(kwargs)
        return model

    class SearchClient:
        def __init__(self, api_key):
            assert api_key == "test-tavily"

        def search(self, **kwargs):
            searches.append(kwargs)
            return {
                "results": [
                    {
                        "title": "Public source",
                        "url": "https://venue.example/weddings",
                        "content": "Research excerpt",
                    }
                ]
            }

    monkeypatch.setattr(langchain_openai, "ChatOpenAI", model_factory)
    monkeypatch.setattr(tavily, "TavilyClient", SearchClient)
    result = generate_plan(
        sample_brief(), Settings(groq_api_key="test-groq", tavily_api_key="test-tavily")
    )
    assert result["searches"] == 2 and len(searches) == 2
    assert len(result["sources"]) == 1
    assert result["markdown"].startswith("# Executive summary")
    assert kwargs_seen["api_key"] == "test-groq"
    assert kwargs_seen["base_url"] == "https://api.groq.com/openai/v1"
    assert kwargs_seen["use_responses_api"] is False
    assert kwargs_seen["model"] == "openai/gpt-oss-20b"
    assert all(s["timeout"] == 30 and s["max_results"] == 4 for s in searches)


def test_provider_errors_do_not_expose_credentials(monkeypatch):
    import langchain_openai

    def fail(**kwargs):
        raise RuntimeError("secret-key-in-provider-error")

    monkeypatch.setattr(langchain_openai, "ChatOpenAI", fail)
    with pytest.raises(PlannerError) as error:
        generate_plan(sample_brief(), Settings(groq_api_key="secret", tavily_api_key="secret"))
    assert "secret-key-in-provider-error" not in str(error.value)


def test_streamlit_preview_history_export_and_live_readiness(monkeypatch, tmp_path):
    from streamlit.testing.v1 import AppTest

    import models

    monkeypatch.setattr(models, "ROOT", tmp_path)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"))
    app.run(timeout=20)
    assert not app.exception
    assert app.button(key="FormSubmitter:wedding_brief-Build preview plan")
    app.text_input(key="brief_couple").set_value("Sam & Taylor")
    app.number_input(key="brief_budget").set_value(12345.67)
    app.button(key="FormSubmitter:wedding_brief-Build preview plan").click().run(timeout=20)
    assert not app.exception
    run = app.session_state["runs"][0]
    assert run["brief"]["couple"] == "Sam & Taylor"
    assert run["brief"]["budget"] == "12345.67"
    assert "**USD 12,345.67**" in run["markdown"]
    assert len(app.get("download_button")) == 2
    app.radio[0].set_value("Live research").run(timeout=20)
    assert not app.exception
    live_button = app.button(key="FormSubmitter:wedding_brief-Generate researched wedding plan")
    assert live_button.disabled
    # Rerun the session to ensure history is retained when mode changes.
    assert len(app.session_state["runs"]) == 1
