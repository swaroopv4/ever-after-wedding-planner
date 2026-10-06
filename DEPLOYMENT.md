# GitHub and online hosting

Repository: `swaroopv4/ever-after-wedding-planner`.
The repository contains this wedding planner as a standalone project at its root.

GitHub stores the code and runs automated checks. GitHub Pages serves static sites
and cannot run the Python agents. Use Streamlit Community Cloud for the running app.

## Streamlit Community Cloud

1. Sign in at https://share.streamlit.io and connect the GitHub repository.
2. Choose **Create app**, then **Yup, I have an app**.
3. Set repository to `swaroopv4/ever-after-wedding-planner`, branch to `main`,
   and the main file path to `app.py`.
4. Select **Python 3.12** under Advanced settings.
5. Deploy. With no server credentials, Preview works and visitors can supply their
   own Groq and Tavily keys for Live research.

The lockfile and exported requirements are included. The checked-in Streamlit
configuration contains the theme and telemetry preference; it does not bind the
hosted server to a local port. The Windows launcher supplies loopback settings
for local runs.

## Model and search credentials

No real credentials are included in the repository. Enter credentials in the app's
sidebar for the current session, or use the hosting service's protected Secrets setting:

```toml
GROQ_API_KEY = "your-own-groq-key"
TAVILY_API_KEY = "your-own-tavily-key"
GROQ_MODEL = "openai/gpt-oss-20b"
```

`.streamlit/secrets.toml.example` contains empty placeholders. The actual `.env`
and `.streamlit/secrets.toml` files are ignored. Do not put secret values into
repository files, GitHub issues, workflow logs or screenshots.

The default hosting instructions use visitor-supplied keys. If you configure server
keys, every authorized viewer can spend that provider quota through the app. Configure
private viewer access for an owner-funded app. This project has no application-level
authentication or shared multi-user rate limiter.

Saved plans remain in each browser session. Download Markdown/JSON to keep them.
No wedding plan, private input brief or local environment is included in the repository.

## Verification after deployment

- Confirm Preview can generate and download a plan.
- Confirm the app reports Groq and Tavily configuration correctly.
- With both keys, run a small live brief and review its sources and budget.
- Review GitHub Actions before relying on a new revision.

Official documentation:
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
- https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages
