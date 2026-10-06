from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from threading import Lock
from urllib.parse import urlparse

from models import Settings, WeddingBrief
from prompts import LOGISTICS_PROMPT, PLANNER_PROMPT, VENUE_PROMPT


class PlannerError(RuntimeError):
    """A safe, user-facing planner failure."""


def message_text(message) -> str:
    content = message.content
    if isinstance(content, str):
        return content.strip()
    return "\n".join(block.get("text", "") for block in content if isinstance(block, dict)).strip()


@dataclass
class RunState:
    searches: int = 0
    delegations: int = 0
    events: list[str] = field(default_factory=list)
    sources: dict[str, dict] = field(default_factory=dict)
    lock: Lock = field(default_factory=Lock, repr=False)

    def reserve(self, kind: str, limit: int, event: str) -> bool:
        with self.lock:
            count = getattr(self, kind)
            if count >= limit:
                return False
            setattr(self, kind, count + 1)
            self.events.append(event)
            return True

    def add_sources(self, results: list[dict]) -> list[dict]:
        clean = []
        with self.lock:
            for item in results:
                url = str(item.get("url", ""))
                parsed = urlparse(url)
                if parsed.scheme not in ("https", "http") or not parsed.netloc:
                    continue
                row = {
                    "title": str(item.get("title", "Source"))[:250],
                    "url": url,
                    "content": str(item.get("content", ""))[:2500],
                }
                self.sources[url] = row
                clean.append(row)
        return clean


def generate_plan(brief: WeddingBrief, settings: Settings) -> dict:
    if not settings.ready:
        raise PlannerError("Add both the Groq and Tavily keys to generate a researched plan.")

    # Lazy, per-run clients avoid import-time calls and credential sharing across sessions.
    from langchain.agents import create_agent
    from langchain.tools import tool
    from langchain_openai import ChatOpenAI
    from tavily import TavilyClient

    state = RunState()
    try:
        # Groq's documented compatible endpoint; no OpenAI account/key is used.
        model = ChatOpenAI(
            model=settings.model,
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
            use_responses_api=False,
            timeout=60,
            max_retries=1,
            max_completion_tokens=6000,
        )
        search_client = TavilyClient(api_key=settings.tavily_api_key)

        @tool
        def search_web(topic: str) -> str:
            """Search current public wedding information and return excerpts with source URLs."""
            if not state.reserve(
                "searches", 8, "Searched public venue, vendor or logistics sources"
            ):
                return "Search limit reached. Synthesize the evidence already collected."
            response = search_client.search(
                query=topic[:500],
                search_depth="basic",
                max_results=4,
                include_answer=False,
                include_raw_content=False,
                timeout=30,
            )
            return json.dumps(state.add_sources(response.get("results", [])), ensure_ascii=False)

        venue_agent = create_agent(
            model=model,
            tools=[search_web],
            system_prompt=VENUE_PROMPT,
            name="VenueVendorResearcher",
        )
        logistics_agent = create_agent(
            model=model,
            tools=[search_web],
            system_prompt=LOGISTICS_PROMPT,
            name="BudgetLogisticsResearcher",
        )

        def delegate(agent, query: str, label: str) -> str:
            if not state.reserve("delegations", 4, label):
                return "Delegation limit reached. Complete the plan using available findings."
            result = agent.invoke(
                {"messages": [{"role": "user", "content": query[:14000]}]},
                config={"recursion_limit": 12},
            )
            return message_text(result["messages"][-1])

        @tool
        def research_venues_and_vendors(query: str) -> str:
            """Delegate venue and vendor research; include location, budget, guests and style."""
            return delegate(venue_agent, query, "Delegated venue and vendor research")

        @tool
        def research_budget_and_logistics(query: str) -> str:
            """Delegate budget, timeline, travel and guest logistics research with the brief."""
            return delegate(logistics_agent, query, "Delegated budget and logistics research")

        planner = create_agent(
            model=model,
            tools=[research_venues_and_vendors, research_budget_and_logistics],
            system_prompt=PLANNER_PROMPT.format(today=date.today().isoformat()),
            name="MainWeddingPlannerAgent",
        )
        result = planner.invoke(
            {"messages": [{"role": "user", "content": brief.to_prompt()}]},
            config={"recursion_limit": 20},
        )
        text = message_text(result["messages"][-1])
        if not text:
            raise PlannerError("The model returned no plan. Try again or choose another model.")
        return {
            "markdown": text,
            "sources": list(state.sources.values()),
            "events": state.events,
            "searches": state.searches,
            "mode": "Live research",
            "model": settings.model,
        }
    except PlannerError:
        raise
    except Exception:
        # Provider exception strings can include request details; never render them in the UI.
        raise PlannerError(
            "The research run did not finish. Check both keys, model access and provider quota, "
            "then retry. No incomplete plan was saved."
        ) from None
