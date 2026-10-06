# Ever After — AI wedding planner

A working reconstruction of [this video](https://www.youtube.com/watch?v=-7ajktD8pOo),
**Build a Multi-Agent AI Wedding Planner with LangChain**, informed by its English captions
and [companion repository](https://github.com/Mohamad-Hachem/MultiAgent_Wedding_Planner_With_Langchain).
The video uses OpenAI `gpt-5-nano`, two LangChain research subagents, Tavily search and Streamlit.
This implementation uses **Groq `openai/gpt-oss-20b`** for all three agents at your request.
It retains the agent architecture and adds distinct researcher roles, source collection,
bounded search/delegation, input validation and a clearly labeled local preview.

## GitHub and online hosting

This is a standalone app. See [DEPLOYMENT.md](DEPLOYMENT.md) to host it with
Streamlit Community Cloud from GitHub. Select branch `main`, entrypoint `app.py`
and Python 3.12. GitHub Actions runs the offline tests and lint checks automatically.
The repository includes empty credential examples; real keys stay out of GitHub.

## Run on Windows

From this folder, with Python 3.12 and [uv](https://docs.astral.sh/uv/) installed:

```powershell
uv sync --frozen
uv run --frozen streamlit run app.py --server.port 8510
```

Open [the wedding planner](http://localhost:8510). Preview mode works without keys.
After installing the isolated environment, you can also launch the app by
double-clicking **Start Wedding Planner.cmd** in this folder.
Load the sample brief, edit your details, and click **Build preview plan**.
The **Your plan** tab contains the output, source links, original brief and downloads.
The sidebar keeps the latest 10 plans for the current browser session.

Alternative installation without uv:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8510
```

## API keys

| Variable | Purpose | Obtain your own key |
| --- | --- | --- |
| `GROQ_API_KEY` | Main planner and both research agents | [Groq dashboard](https://console.groq.com/keys) |
| `TAVILY_API_KEY` | Current public web search | [Tavily dashboard](https://app.tavily.com) |
| `GROQ_MODEL` | Optional model setting, default `openai/gpt-oss-20b` | Use a Groq model with tool calling available to your account |

Both keys are required for **Live research**. Configure your own credentials locally or
in your hosted app. No credential is included in source or exports.
Groq and Tavily billing/quota depend on your own accounts.
The installed LangChain OpenAI adapter and OpenAI SDK call Groq's documented
[compatible endpoint](https://console.groq.com/docs/openai). No OpenAI key is needed.

Either enter keys in the sidebar password fields, set environment variables, use
`.streamlit/secrets.toml`, or create this application's private `.env`:

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
# Edit .env locally and add GROQ_API_KEY and TAVILY_API_KEY.
```

The app reads only its own `.env`; it never copies the parent application's credentials.
Sidebar overrides are passed directly to clients for this session, without changing process
environment variables. Keys are excluded from plan/brief exports. Do not put key values in chat.
No provider request is made on page load or in preview mode. Entering keys marks them configured;
it does not verify credentials or guarantee quota.

## Agent workflow

The main planner can delegate to **VenueVendorResearcher** and **BudgetLogisticsResearcher**.
Each specialist has a Tavily search tool. Their findings are returned to the planner,
which produces a Markdown plan with concept, shortlist, budget, timeline, guest experience,
risks and next steps. Source pages returned by Tavily are collected separately for review.
Prompts request both researchers, source-backed recommendations and explicit estimate labels.
The model decides actual tool use; the research activity and source count show what occurred.

Per-run limits: eight searches, four delegations, bounded graph iterations and provider request
timeouts. These bounds limit runaway work; they are not a fixed-dollar spending limit.
API errors are shown as a safe message; incomplete plans are not added to history.
Research activity is displayed after generation completes.

Preview is a deterministic planning template with no model or web requests. Its allocations
sum to the exact entered budget, and dates are arranged between today and your wedding day.
It does not supply actual venue names or pretend to have verified prices.

## CLI

```powershell
uv run --frozen python main.py --preview --output plans/sample.md
uv run --frozen python main.py --brief wedding-brief.json --output plans/researched.md
```

Without `--brief`, the CLI uses the sample brief. It supports the same JSON exported by the UI.
Omit `--preview` to use real providers with your locally configured keys.

## Verification

```powershell
uv sync --frozen --group dev
uv run --frozen pytest -q
uv run --frozen ruff check .
```

Tests cover exact budget totals, brief validation, key isolation, source URL handling,
search/delegation boundaries, actual LangChain tool orchestration with a scripted test model,
provider-error behavior, and Streamlit form generation/history/export without real keys.
Full live Groq/Tavily research requires both credentials and remains unverified until
Tavily is configured. See VALIDATION.md for the completed Groq connection checks.

Saved plans disappear when the browser session resets; download them to keep a copy.
This is a local application bound to loopback, without a hosted authentication system.
Generated market claims and model-calculated budgets require review; source collection does
not prove every statement. Confirm availability and itemized quotes directly before booking.

## Tutorial review

Reviewed the video introduction/demo, prompt/model/tool preparation, subagent creation,
main-agent orchestration and UI walkthrough through the English caption transcript and
linked code. The original has import-time model/search clients and identical subagents.
Here clients initialize only for a live run, researchers have distinct instructions and
the UI retains the brief, run history, readiness controls and Markdown export.
This is a functional reconstruction, not a frame-perfect copy of the tutorial UI.
