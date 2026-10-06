# Verification — October 6, 2026

Python 3.12.14 on Windows. Application dependencies are isolated in `.venv` and pinned in
`uv.lock`; `requirements.txt` is exported from the same lock for pip installation.

- **16 tests passed.** Budget rounding/totals, invalid input, credential precedence and isolation,
  missing-key behavior, bounded research, safe source URLs and provider-error redaction.
- The actual installed LangChain graph executed both research agents and their search tools
  with a scripted test model and simulated Tavily responses. No paid provider calls were made.
- Streamlit AppTest generated a custom plan, retained history, exposed both exports and
  disabled live generation when keys were missing.
- Ruff lint and format checks passed. CLI preview wrote `plans/sample.md` successfully.
- All three agents now use Groq `openai/gpt-oss-20b` through the installed LangChain
  OpenAI adapter pointed at `https://api.groq.com/openai/v1`. The regression checks assert
  the Groq endpoint and credential selection; no OpenAI key is used.
- A small live Groq request with the supplied credential successfully returned the requested
  function call. This verifies authentication, model access and tool calling. No venue research,
  vendor contact or booking was performed by this check.
- The installed Tavily SDK supports the configured 30-second search timeout.
- The running Streamlit service returned **HTTP 200 / ok** from its health endpoint.
- In-app browser verification confirmed the brief fields, successful preview generation,
  saved plan, exact USD 45,000 total, date timeline, preview labels and download buttons.

**Not verified:** a complete live researched wedding plan, actual Tavily search,
provider capacity/billing or hosted deployment. The supplied Groq key is configured in
the ignored application `.env`; Tavily remains missing. No existing chemistry credentials
were copied.

The tutorial's English caption transcript and linked Python source were reviewed. Reference
materials are under the parent `tutorial-extraction/evidence/wedding-source` folder. Those
materials are not runtime dependencies. The application is a separate implementation with
distinct research roles and a local preview, rather than an exact visual copy.
