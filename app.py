from __future__ import annotations

import json
import time
from datetime import date, datetime
from decimal import Decimal

import streamlit as st
from pydantic import ValidationError

from agents import PlannerError, generate_plan
from demo import preview_plan
from models import Settings, WeddingBrief, sample_brief

STYLES = [
    "Garden",
    "Romantic",
    "Modern",
    "Classic",
    "Minimal",
    "Luxury",
    "Cultural fusion",
    "Destination",
    "Eco-conscious",
    "Black tie",
]
PRIORITIES = [
    "Guest experience",
    "Budget",
    "Venue shortlist",
    "Vendor research",
    "Timeline",
    "Design",
    "Travel logistics",
    "Risk management",
]

st.set_page_config(page_title="Ever After · Wedding Planner", page_icon="♡", layout="wide")
st.markdown(
    """
<style>
.stApp {background: #faf8f4;}
.block-container {max-width: 1180px; padding-top: 2.4rem; padding-bottom: 3rem;}
[data-testid="stSidebar"] {background:#f0ece5; border-right:1px solid #dedbd2;}
[data-testid="stHeader"] {background:transparent;}
h1,h2,h3 {color:#283b32;}
h1 {font-family:Georgia,serif !important; font-weight:400 !important;}
[data-testid="stForm"] {background:#fffdfa; border:1px solid #e3ddd2;
    border-radius:16px; padding:22px;}
button[kind="primary"] {border-radius:9px;}
.eyebrow {font-size:11px; letter-spacing:2.3px; color:#718174; font-weight:700;}
.hero {padding:26px 0 28px; border-bottom:1px solid #dedbd2; margin-bottom:24px;}
.hero h1 {font-size:clamp(38px,5vw,62px); line-height:1.12; margin:12px 0;}
.hero p {color:#6a736b; font-size:17px; max-width:700px; line-height:1.6;}
.stamp {display:inline-block; background:#e8eee6; color:#48614d; font-size:12px;
    border-radius:30px; padding:7px 12px; margin-top:8px;}
.brand {font-family:Georgia,serif; font-size:29px; color:#283b32; margin-bottom:4px;}
.step {font-size:11px; letter-spacing:1.7px; color:#8d7869; margin:8px 0;}
.agent {background:#f0f2ec; border-radius:12px; padding:16px 19px; margin:8px 0 18px;}
.agent strong {font-size:15px; color:#354a3b;}
.agent p {font-size:13px; color:#6a736b; margin:6px 0 0; line-height:1.55;}
@media(max-width:700px) {.block-container {padding:1rem;} .hero {padding-top:10px;}}
</style>
""",
    unsafe_allow_html=True,
)


def fill_sample() -> None:
    for key, value in sample_brief().model_dump().items():
        st.session_state["brief_" + key] = float(value) if isinstance(value, Decimal) else value


if "brief_couple" not in st.session_state:
    fill_sample()
if "runs" not in st.session_state:
    st.session_state.runs = []
if st.session_state.pop("plan_ready", False):
    st.toast("Your plan is ready. Open the Your plan tab to review and download it.")

with st.sidebar:
    st.markdown(
        '<div class="brand">ever after<span style="color:#b09b88">.</span></div>',
        unsafe_allow_html=True,
    )
    st.caption("A little clarity for your big day.")
    st.divider()
    mode = st.radio(
        "Planning mode",
        ["Preview", "Live research"],
        help="Preview uses a local template. Live research uses Groq and Tavily.",
    )
    with st.expander("API connections", expanded=mode == "Live research"):
        secrets = {}
        try:
            for key in ("GROQ_API_KEY", "TAVILY_API_KEY", "GROQ_MODEL"):
                if st.secrets.get(key):
                    secrets[key] = st.secrets[key]
        except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
            pass
        groq_key = st.text_input(
            "Groq API key",
            type="password",
            key="groq_input",
            placeholder="Optional override for this session",
        )
        tavily_key = st.text_input(
            "Tavily API key",
            type="password",
            key="tavily_input",
            placeholder="Optional override for this session",
        )
        if groq_key.strip():
            secrets["GROQ_API_KEY"] = groq_key.strip()
        if tavily_key.strip():
            secrets["TAVILY_API_KEY"] = tavily_key.strip()
        settings = Settings.load(secrets)
        model = st.text_input(
            "Groq model",
            value=settings.model,
            help="Default: openai/gpt-oss-20b on Groq. Choose a tool-capable model.",
        )
        settings.model = model.strip() or "openai/gpt-oss-20b"
        st.caption(
            f"Groq: {'Configured' if settings.groq_api_key else 'Missing'} · "
            f"Tavily: {'Configured' if settings.tavily_api_key else 'Missing'}"
        )
        st.markdown(
            "[Get a Groq key](https://console.groq.com/keys) · "
            "[Get a Tavily key](https://app.tavily.com)"
        )
        st.caption(
            "Keys stay on this server or in this browser session. They are excluded from exports."
        )
    st.button("Load sample brief", on_click=fill_sample, use_container_width=True)
    st.divider()
    st.markdown("**Your planning team**")
    st.caption(
        "01 · Main wedding planner\n\n02 · Venue & vendor researcher\n\n"
        "03 · Budget & logistics researcher"
    )
    st.divider()
    if st.session_state.runs:
        st.markdown("**Saved plans**")
        run_labels = [run["label"] for run in st.session_state.runs]
        selected = st.selectbox(
            "Choose a saved plan",
            range(len(st.session_state.runs)),
            format_func=lambda i: run_labels[i],
            key="selected_run",
        )
        if st.button("Clear saved plans", use_container_width=True):
            st.session_state.runs = []
            st.session_state.pop("selected_run", None)
            st.rerun()
    else:
        selected = None
        st.caption("Your plans will appear here. Saved for this session, up to 10 plans.")

st.markdown(
    """
<div class="hero">
  <div class="eyebrow">YOUR WEDDING, THOUGHTFULLY PLANNED</div>
  <h1>Big dreams.<br>A beautiful plan.</h1>
  <p>Bring your ideas, your priorities and your budget. Your planning team brings
  them together into a celebration that feels like you.</p>
  <div class="stamp">One planner. Two researchers. Your vision.</div>
</div>
""",
    unsafe_allow_html=True,
)

brief_tab, plan_tab, team_tab = st.tabs(
    ["01  Your wedding brief", "02  Your plan", "03  How it works"],
    default="02  Your plan" if st.session_state.runs else "01  Your wedding brief",
)

with brief_tab:
    left, right = st.columns([3, 1], gap="large")
    with right:
        st.markdown('<div class="step">A GOOD PLACE TO BEGIN</div>', unsafe_allow_html=True)
        st.markdown("### Make it yours")
        st.write(
            "Start with the essentials. Then add the details that will make your wedding personal."
        )
        st.markdown(
            '<div class="agent"><strong>What your plan includes</strong><p>'
            "Venue and vendor ideas<br>Budget by category<br>A practical timeline<br>"
            "Guest experience<br>Tradeoffs and next steps</p></div>",
            unsafe_allow_html=True,
        )
        if mode == "Preview":
            st.info(
                "Preview builds an illustrative plan with no API calls. Switch to Live research "
                "for current venue and vendor sources."
            )
        else:
            st.caption(
                "The brief is sent to Groq. Research topics are sent to Tavily. "
                "Live runs use your provider credits and may take a few minutes."
            )
    with left, st.form("wedding_brief"):
        st.markdown('<div class="step">THE ESSENTIALS</div>', unsafe_allow_html=True)
        st.subheader("Tell us about your day")
        couple = st.text_input("Couple's names", key="brief_couple")
        a, b = st.columns(2)
        with a:
            location = st.text_input("Wedding location", key="brief_location")
            guests = st.number_input(
                "Guest count", min_value=2, max_value=5000, step=1, key="brief_guests"
            )
            currency = st.selectbox(
                "Currency", ["USD", "EUR", "GBP", "CAD", "AUD", "INR", "AED"], key="brief_currency"
            )
        with b:
            wedding_date = st.date_input(
                "Wedding date", min_value=date.today(), key="brief_wedding_date"
            )
            budget = st.number_input(
                "Total wedding budget",
                min_value=100.0,
                max_value=100_000_000.0,
                step=1000.0,
                key="brief_budget",
            )
            event_scope = st.selectbox(
                "Event scope",
                [
                    "Ceremony + reception",
                    "Reception only",
                    "Wedding weekend",
                    "Destination wedding",
                ],
                key="brief_event_scope",
            )
        st.divider()
        st.markdown('<div class="step">THE FEELING</div>', unsafe_allow_html=True)
        styles = st.multiselect("Style direction", STYLES, key="brief_styles")
        priorities = st.multiselect("Your planning priorities", PRIORITIES, key="brief_priorities")
        must_haves = st.text_area(
            "The must-haves", key="brief_must_haves", height=90, max_chars=3000
        )
        constraints = st.text_area(
            "Constraints and accessibility needs",
            key="brief_constraints",
            height=90,
            max_chars=3000,
        )
        cultural = st.text_area(
            "Cultural and family details", key="brief_cultural_details", height=90, max_chars=3000
        )
        tone = st.selectbox(
            "Planner tone",
            ["Warm and practical", "Detailed and professional", "Creative and inspiring"],
            key="brief_tone",
        )
        submitted = st.form_submit_button(
            "Build preview plan" if mode == "Preview" else "Generate researched wedding plan",
            type="primary",
            use_container_width=True,
            disabled=mode == "Live research" and not settings.ready,
        )
        if mode == "Live research" and not settings.ready:
            st.caption("Add both API keys in the sidebar to enable live generation.")

    if submitted:
        try:
            brief = WeddingBrief(
                couple=couple,
                location=location,
                wedding_date=wedding_date,
                guests=int(guests),
                budget=Decimal(str(budget)),
                currency=currency,
                event_scope=event_scope,
                styles=styles,
                priorities=priorities,
                must_haves=must_haves,
                constraints=constraints,
                cultural_details=cultural,
                tone=tone,
            )
        except ValidationError as error:
            for issue in error.errors():
                st.error(f"{' '.join(str(p) for p in issue['loc'])}: {issue['msg']}")
        else:
            started = time.monotonic()
            try:
                with st.status("Creating your wedding plan…", expanded=True) as status:
                    if mode == "Preview":
                        st.write("Allocating your budget and arranging a planning timeline.")
                        result = preview_plan(brief)
                    else:
                        st.write(
                            "The planner is coordinating venue/vendor "
                            "and budget/logistics research."
                        )
                        st.write("Research is limited to eight web searches per run.")
                        result = generate_plan(brief, settings)
                    for event in result["events"]:
                        st.write(event)
                    status.update(label="Your plan is ready", state="complete", expanded=False)
            except PlannerError as error:
                st.error(str(error))
            else:
                result.update(
                    {
                        "brief": brief.model_dump(mode="json"),
                        "elapsed": round(time.monotonic() - started, 1),
                        "label": f"{brief.couple} · {datetime.now():%H:%M:%S} · {result['mode']}",
                    }
                )
                st.session_state.runs.insert(0, result)
                st.session_state.runs = st.session_state.runs[:10]
                st.session_state.selected_run = 0
                st.session_state.plan_ready = True
                st.rerun()

with plan_tab:
    if st.session_state.runs:
        index = st.session_state.get("selected_run", 0)
        run = st.session_state.runs[min(index, len(st.session_state.runs) - 1)]
        st.subheader(run["brief"]["couple"])
        cols = st.columns(4)
        cols[0].metric("Planning mode", run["mode"])
        cols[1].metric("Guests", run["brief"]["guests"])
        cols[2].metric(
            "Budget", f"{run['brief']['currency']} {Decimal(run['brief']['budget']):,.0f}"
        )
        cols[3].metric("Research sources", len(run["sources"]))
        c1, c2, _ = st.columns([1, 1, 2])
        c1.download_button(
            "Download plan · Markdown",
            run["markdown"],
            file_name="wedding-plan.md",
            mime="text/markdown",
            use_container_width=True,
        )
        c2.download_button(
            "Download brief · JSON",
            json.dumps(run["brief"], indent=2),
            file_name="wedding-brief.json",
            mime="application/json",
            use_container_width=True,
        )
        st.caption(
            f"Created in {run['elapsed']:g}s · {run['model']} · "
            "Saved in this browser session; download to keep a copy."
        )
        if run["mode"] == "Preview":
            st.info("Illustrative preview. No live research, quotes or availability checks.")
        st.markdown(run["markdown"])
        if run["sources"]:
            with st.expander(f"Research sources ({len(run['sources'])})"):
                st.caption(
                    "Pages returned during research. Confirm quotes and availability directly."
                )
                for source in run["sources"]:
                    st.link_button(source["title"], source["url"])
        with st.expander("Exact input brief"):
            st.json(run["brief"])
        with st.expander("Research activity"):
            for event in run["events"]:
                st.write(event)
    else:
        st.subheader("Your celebration starts with a brief.")
        st.write("Fill in Your wedding brief, then build a preview or generate a researched plan.")

with team_tab:
    st.subheader("A small team with a shared vision")
    st.write(
        "In live mode, a main LangChain planner calls two specialist agents as tools. "
        "Each researcher searches public sources through Tavily, then returns findings "
        "for the main planner to combine into your plan."
    )
    st.graphviz_chart("""digraph {
        graph [rankdir=TB, bgcolor="transparent"];
        node [shape=box, style="rounded,filled", fillcolor="#e8eee6", color="#bcc8b9",
              fontname="Arial", fontcolor="#283b32", margin="0.2,0.13"];
        edge [color="#899b88"];
        brief [label="Your wedding brief"];
        main [label="Main wedding planner"];
        venues [label="Venue & vendor researcher"];
        logistics [label="Budget & logistics researcher"];
        search [label="Tavily · current public web sources"];
        output [label="Your plan · sources · Markdown export"];
        brief -> main; main -> venues; main -> logistics;
        venues -> search; logistics -> search; venues -> main; logistics -> main;
        main -> output;
    }""")
    st.caption(
        "Model: Groq openai/gpt-oss-20b by default · Research: Tavily · Interface: Streamlit. "
        "Preview mode uses a local template and does not run the agents."
    )
    st.markdown(
        "Based on the [video tutorial](https://www.youtube.com/watch?v=-7ajktD8pOo) "
        "and its [companion project](https://github.com/Mohamad-Hachem/"
        "MultiAgent_Wedding_Planner_With_Langchain)."
    )
