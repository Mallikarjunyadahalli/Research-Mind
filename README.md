# 🔎 ResearchMind

A multi-agent AI research system. Give it a topic and four AI agents search the web, read the best source, write a structured report, and critique it. It runs in the terminal or through a Streamlit web interface.

![ResearchMind UI](assets/screenshot.png)

## How it works

```
Topic ─▶ Search Agent ─▶ Reader Agent ─▶ Writer Chain ─▶ Critic Chain ─▶ Report + Review
```

| Step | Component        | What it does                                                                                     |
| ---- | ---------------- | ------------------------------------------------------------------------------------------------ |
| 1    | **Search Agent** | Searches the web for recent, reliable information                                                |
| 2    | **Reader Agent** | Picks the most relevant URL and scrapes it for deeper content                                    |
| 3    | **Writer Chain** | Turns the research into a structured Markdown report                                             |
| 4    | **Critic Chain** | Reviews the report, scores it out of 10, and gives a verdict (PASS / NEEDS IMPROVEMENT / REJECT) |

## Features

- Dark Streamlit UI with live status cards and a progress bar for each pipeline step
- Shows which tool the agent is using while it works
- Automatic retries for rate limits (429) and flaky model errors
- Fast mode: skip the critic review to save time
- Report, critic feedback, and sources in separate tabs, with stats (time, word count, sources, score)
- Download the report as Markdown
- History of past researches in the sidebar, reloaded instantly with no new API calls
- Still works from the terminal with `pipeline.py`

## Tech stack

- Python
- LangChain (agents, prompts, chains)
- Groq (LLM inference)
- Streamlit (web UI)

## Project structure

```
.
├── app.py                  # Streamlit UI
├── pipeline.py             # Terminal version of the pipeline
├── agents.py               # Search/Reader agents, Writer and Critic chains
├── tools.py                # web_search and scarape_url tools
├── requirements.txt
├── .env                    # API keys (not committed)
└── .streamlit/
    └── config.toml         # Dark theme
```

## Getting started

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd <your-repo-folder>
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

`requirements.txt` should include `streamlit>=1.40`.

### 3. Add your API keys

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key

# Add any key your tools.py needs, for example your search provider:
# TAVILY_API_KEY=your_search_api_key

# Optional: use a different Groq model for the Writer and Critic chains
# WRITER_MODEL=llama-3.3-70b-versatile
```

### 4. Run it

Web UI:

```bash
streamlit run app.py
```

Then open http://localhost:8501.

Terminal:

```bash
python pipeline.py
```

## Configuration

Settings at the top of `app.py`:

| Setting               | Default | Purpose                                                                     |
| --------------------- | ------- | --------------------------------------------------------------------------- |
| `COOLDOWN_SECS`       | `0`     | Pause between steps. Raise to about 8 if you hit rate limits on a free tier |
| `WRITER_SEARCH_CHARS` | `2500`  | Max search text sent to the writer                                          |
| `WRITER_SCRAPE_CHARS` | `3500`  | Max scraped text sent to the writer                                         |
| `MAX_HISTORY`         | `10`    | Number of past researches kept in the sidebar                               |

## Troubleshooting

**`429 rate_limit_exceeded`**: You hit the tokens-per-minute limit of your Groq plan. The app waits and retries automatically. If it keeps failing, use a model with a higher limit, lower the `WRITER_*_CHARS` values, or upgrade your plan.

**`400 tool_use_failed` / "Tool choice is none, but model called a tool"**: `gpt-oss` models sometimes try to call a built-in tool. The Writer and Critic chains use a Llama model to avoid this, and the app retries the error automatically.

**The pipeline is slow**: Turn on Fast mode in the sidebar, keep tool output short in `tools.py`, and limit how many times each agent can call its tool.

**`ModuleNotFoundError`**: Make sure the virtual environment is active and run `pip install -r requirements.txt` again.

## Roadmap

- Export the report as PDF
- Choose the model and search depth from the UI
- Support more than one source in the Reader step
- Stream the report text as it is written

## Author

**Mallikarjun** · [GitHub](https://github.com/Mallikarjunyadahalli)
**Mallikarjun** · [LinkedIn](https://www.linkedin.com/in/mallikarjun-yadahalli-5240732b7/)

If you find this project useful, give it a ⭐
