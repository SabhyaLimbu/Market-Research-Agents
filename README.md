# Multi-Agent Market Research App

A Streamlit app that takes a company or industry and produces a short research brief using four
sequential roles: **Orchestrator → Researcher → Analyst → Critic** (at most one revision).
All roles use the same LLM (Anthropic Claude). Data is passed between roles as Pydantic models.

## How it works
| Role | File | Job |
|---|---|---|
| Orchestrator | `workflow.py` | Receives the query, runs the roles in order, allows one revision |
| Researcher | `workflow.py`, `search.py` | DuckDuckGo search, extracts facts only from results; falls back to labelled sample data |
| Analyst | `workflow.py` | Writes the brief (summary, up to 2 competitors, observations, sources, gaps) |
| Critic | `workflow.py` | Checks the draft against the findings; requests one revision if needed |

Shared data models: `models.py` (`Findings`, `Brief`, `Critique`, `WorkflowState`).

## Setup
Requires Python 3.10+.

```bash
git clone <your-repo-url> && cd market-research-agents
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # Windows: copy .env.example .env
# edit .env and set ANTHROPIC_API_KEY
streamlit run app.py
```
Open http://localhost:8501, enter e.g. `Analyze the food delivery market in Nepal`, click **Start research**.

## Notes and limitations
- Web search uses the `ddgs` package (no key). If it returns nothing, the app uses clearly labelled sample data and says so in the brief.
- The brief only reflects retrieved snippets, not full pages, so gaps are listed under "Missing information".
- To use a different LLM, change `ask_json` in `llm.py`.

## Sample output
See `sample_output.md`.
