"""
ResearchMind - Streamlit UI for the multi-agent research pipeline.

Run:  streamlit run app.py
Needs: streamlit>=1.40  (container keys are used for styling)
"""

import html
import re
import time
from datetime import datetime
import os
import streamlit as st

# set_page_config must be the first Streamlit call
st.set_page_config(
    page_title="ResearchMind - AI Research Agent",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "OPENAI_API_KEY" in st.secrets:
    openai_api_key = st.secrets["OPENAI_API_KEY"]
else:
    openai_api_key = os.getenv("OPENAI_API_KEY")

# If your file is named agent.py, change this to: from agent import ...
try:
    from agents import (
        create_search_agent,
        create_scrap_agent,
        writter_chain,
        critic_chain,
    )
except Exception as import_error:  # pragma: no cover
    st.error(
        f"Could not import your agents module: {import_error}\n\n"
        "Make sure app.py is in the same folder as agents.py (or agent.py) and your "
        "API keys are set in .env."
    )
    st.stop()

# ---------------------------------------------------------------- config
STEPS = [
    {"key": "search", "name": "Search Agent", "desc": "Gathers recent web information",
     "working": "🔍 Search Agent is working..."},
    {"key": "reader", "name": "Reader Agent", "desc": "Scrapes & extracts deep content",
     "working": "📖 Reader Agent is scraping the best source..."},
    {"key": "writer", "name": "Writer Chain", "desc": "Drafts the full research report",
     "working": "✍️ Writer Chain is drafting the report..."},
    {"key": "critic", "name": "Critic Chain", "desc": "Reviews & scores the report",
     "working": "🧐 Critic Chain is reviewing the report..."},
]
EXAMPLES = ["LLM agents 2026", "CRISPR gene editing", "Fusion energy progress"]
MAX_HISTORY = 10

# Optional pause between steps. Keep 0: 429 rate limits are already retried automatically.
# Only raise it (e.g. 8) if you keep seeing rate-limit retries on the free tier.
COOLDOWN_SECS = 0
WRITER_SEARCH_CHARS = 2500
WRITER_SCRAPE_CHARS = 3500

# ---------------------------------------------------------------- styling
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=DM+Sans:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap');

:root {
  --bg:#07080a; --card:#0e1014; --card-2:#12151a; --line:#1e222a;
  --text:#e8e9ec; --muted:#8b909a; --accent:#ff7a1a; --accent-2:#ff5a14;
  --ok:#3ecf8e; --err:#ff5d5d;
}
html, body, .stApp { background: var(--bg); color: var(--text); font-family: 'DM Sans', sans-serif; }
.stApp {
  background:
    radial-gradient(900px 380px at 15% -5%, rgba(255,122,26,.10), transparent 60%),
    var(--bg);
}
#MainMenu, footer { visibility: hidden; }
[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 1180px; padding-top: 2.2rem; padding-bottom: 4rem; }
h1, h2, h3, h4 { font-family: 'Space Grotesk', sans-serif; letter-spacing: -.01em; }
p, li, .stMarkdown { color: var(--text); }
[data-testid="stSidebar"] { background: #0a0b0e; border-right: 1px solid var(--line); }

/* hero */
.hero-title { font-family:'Space Grotesk',sans-serif; font-weight:700; font-size:2.6rem; letter-spacing:-.02em; margin:0; }
.hero-sub { color: var(--muted); font-size:1.05rem; max-width:640px; margin:.4rem 0 1.8rem; line-height:1.55; }

/* labels */
.label { font-family:'JetBrains Mono',monospace; font-size:.74rem; letter-spacing:.16em; color:var(--accent); margin-bottom:.45rem; text-transform:uppercase; }
.label.muted { color: var(--muted); margin-top:1.2rem; }

/* input */
[data-testid="stForm"] { border:0; padding:0; background:transparent; }
[data-testid="stTextInput"] input {
  background: var(--card-2); border:1px solid var(--line); border-radius:12px;
  color: var(--text); padding:.85rem 1rem; font-size:1.05rem;
}
[data-testid="stTextInput"] input:focus { border-color: var(--accent); box-shadow:0 0 0 3px rgba(255,122,26,.18); }

/* run button */
[data-testid="stFormSubmitButton"] button {
  width:100%; border:0; border-radius:12px; padding:.85rem 1rem; font-weight:600; font-size:1.05rem;
  color:#fff; background: linear-gradient(90deg, var(--accent), var(--accent-2));
  box-shadow: 0 8px 28px rgba(255,100,20,.28); transition: transform .12s ease, box-shadow .12s ease;
}
[data-testid="stFormSubmitButton"] button:hover { transform: translateY(-1px); box-shadow:0 12px 34px rgba(255,100,20,.38); color:#fff; }
[data-testid="stFormSubmitButton"] button:focus-visible { outline:2px solid #fff; outline-offset:2px; }

/* example chips */
.st-key-chips button {
  background: var(--card); border:1px solid var(--line); color: var(--text);
  border-radius:8px; padding:.35rem .8rem; font-size:.92rem; min-height:0; justify-content:flex-start;
}
.st-key-chips button:hover { border-color: var(--accent); color: var(--accent); }

/* pipeline cards */
.step { background:var(--card); border:1px solid var(--line); border-radius:16px; padding:1.1rem 1.3rem; margin-bottom:.8rem; transition:border-color .2s, background .2s; }
.step.running { border-color: rgba(255,122,26,.7); background: linear-gradient(180deg, rgba(255,122,26,.07), var(--card)); }
.step.done { border-color: rgba(62,207,142,.35); }
.step.error { border-color: rgba(255,93,93,.6); }
.step-top { display:flex; align-items:center; gap:.8rem; }
.num { font-family:'JetBrains Mono',monospace; color:var(--accent); font-size:.85rem; }
.name { font-family:'Space Grotesk',sans-serif; font-weight:600; font-size:1.15rem; flex:1; }
.badge { font-family:'JetBrains Mono',monospace; font-size:.72rem; letter-spacing:.14em; color:var(--muted); display:flex; align-items:center; gap:.45rem; }
.badge.running { color: var(--accent); }
.badge.done { color: var(--ok); }
.badge.error { color: var(--err); }
.dot { width:8px; height:8px; border-radius:50%; background:currentColor; display:inline-block; }
.running .dot { animation: pulse 1.1s ease-in-out infinite; }
.desc { color: var(--muted); margin-top:.45rem; font-size:.95rem; }
@keyframes pulse { 0%,100%{opacity:1; transform:scale(1)} 50%{opacity:.3; transform:scale(.7)} }

/* overall progress */
.prog { background:var(--card); border:1px solid var(--line); border-radius:14px; padding:1rem 1.2rem; margin-top:.6rem; }
.prog-head { display:flex; justify-content:space-between; font-size:.95rem; margin-bottom:.6rem; }
.prog-head .pct { font-family:'JetBrains Mono',monospace; color:var(--accent); }
.track { height:8px; background:#191c22; border-radius:99px; overflow:hidden; }
.fill { height:100%; border-radius:99px; background:linear-gradient(90deg,var(--accent),var(--accent-2)); transition:width .5s ease; }
.fill.live { background-size:200% 100%; animation: shimmer 1.6s linear infinite;
  background-image:linear-gradient(90deg,var(--accent),#ffb36b,var(--accent-2),var(--accent)); }
.fill.done { background: var(--ok); }
@keyframes shimmer { to { background-position:-200% 0; } }

/* result */
.result-title { font-family:'Space Grotesk',sans-serif; font-size:1.7rem; font-weight:700; margin:.2rem 0 1rem; }
.stats { display:grid; grid-template-columns:repeat(4,1fr); gap:.8rem; margin-bottom:1.2rem; }
.stat { background:var(--card); border:1px solid var(--line); border-radius:14px; padding:.9rem 1.1rem; }
.stat .v { font-family:'Space Grotesk',sans-serif; font-size:1.6rem; font-weight:600; }
.stat .k { color:var(--muted); font-size:.85rem; }
@media (max-width: 760px){ .stats{grid-template-columns:repeat(2,1fr);} .hero-title{font-size:2rem;} }

[data-testid="stTabs"] button { font-size:1rem; }
[data-testid="stDownloadButton"] button { background:var(--card-2); border:1px solid var(--line); color:var(--text); border-radius:10px; }
[data-testid="stDownloadButton"] button:hover { border-color:var(--accent); color:var(--accent); }
[data-testid="stExpander"] { background:var(--card); border:1px solid var(--line); border-radius:12px; }
a { color: var(--accent); }
.src { padding:.5rem 0; border-bottom:1px solid var(--line); word-break:break-all; }

@media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------- helpers
def as_text(value) -> str:
    """Agent/chain outputs can be str, message objects or lists of content parts."""
    if value is None:
        return ""
    content = getattr(value, "content", value)
    if isinstance(content, list):
        parts = []
        for p in content:
            parts.append(p.get("text", "") if isinstance(p, dict) else str(p))
        return "\n".join(parts)
    return str(content)


def fmt_secs(s: float) -> str:
    return f"{s:.0f}s" if s >= 10 else f"{s:.1f}s"


def extract_urls(text: str) -> list:
    seen, out = set(), []
    for u in re.findall(r"https?://[^\s\)\]>\"']+", text or ""):
        u = u.rstrip(".,;:")
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def with_retry(fn, attempts: int = 5, on_wait=None):
    """Retry on errors. For 429 rate limits, wait exactly as long as the API asks."""
    last = None
    for n in range(attempts):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            last = e
            msg = str(e)
            rate_limited = "429" in msg or "rate limit" in msg.lower()
            if n == attempts - 1 or (not rate_limited and n >= 1):
                break
            hint = re.search(r"try again in ([\d.]+)\s*(ms|s|m)", msg)
            if hint:
                val, unit = float(hint.group(1)), hint.group(2)
                wait = val / 1000 if unit == "ms" else val * 60 if unit == "m" else val
                wait += 2
            else:
                wait = min(10 * (n + 1), 40) if rate_limited else 2
            if on_wait:
                on_wait(wait, rate_limited)
            time.sleep(wait)
    raise last


def run_agent(agent, prompt: str, label: str):
    """Stream the agent so the UI shows which tool it is calling instead of looking stuck."""
    payload = {"messages": [("user", prompt)]}
    last = None
    try:
        for chunk in agent.stream(payload, stream_mode="values"):
            msgs = chunk.get("messages", [])
            if not msgs:
                continue
            last = msgs[-1]
            for call in getattr(last, "tool_calls", None) or []:
                ss.progress_msg = f"{label}: using {call.get('name', 'tool')}..."
                render()
    except AttributeError:
        last = agent.invoke(payload)["messages"][-1]
    return last


def pipeline_html(states: dict, timings: dict) -> str:
    labels = {"waiting": "WAITING", "running": "RUNNING", "error": "FAILED", "skipped": "SKIPPED"}
    cards = []
    for i, s in enumerate(STEPS, start=1):
        st_ = states.get(s["key"], "waiting")
        if st_ == "done":
            label = f"DONE · {fmt_secs(timings.get(s['key'], 0))}"
        else:
            label = labels[st_]
        cards.append(
            f'<div class="step {st_}">'
            f'<div class="step-top"><span class="num">{i:02d}</span>'
            f'<span class="name">{s["name"]}</span>'
            f'<span class="badge {st_}"><span class="dot"></span>{label}</span></div>'
            f'<div class="desc">{s["desc"]}</div></div>'
        )
    return "".join(cards)


def progress_html(states: dict, message: str) -> str:
    done = sum(1 for s in STEPS if states.get(s["key"]) in ("done", "skipped"))
    running = any(states.get(s["key"]) == "running" for s in STEPS)
    pct = int(round((done + (0.5 if running else 0)) / len(STEPS) * 100))
    cls = "live" if running else ("done" if done == len(STEPS) else "")
    return (
        f'<div class="prog"><div class="prog-head"><span>{html.escape(message)}</span>'
        f'<span class="pct">{pct}%</span></div>'
        f'<div class="track"><div class="fill {cls}" style="width:{pct}%"></div></div></div>'
    )


# ---------------------------------------------------------------- state
ss = st.session_state
ss.setdefault("topic", "")
ss.setdefault("history", [])
ss.setdefault("result", None)
ss.setdefault("states", {s["key"]: "waiting" for s in STEPS})
ss.setdefault("timings", {})
ss.setdefault("progress_msg", "Ready. Enter a topic and run the pipeline.")


def set_topic(value: str):
    ss.topic = value


def load_history(idx: int):
    item = ss.history[idx]
    ss.result = item
    ss.states = {s["key"]: "done" for s in STEPS}
    ss.timings = item["timings"]
    ss.progress_msg = f"Loaded: {item['topic']}"


def clear_history():
    ss.history = []
    ss.result = None
    ss.states = {s["key"]: "waiting" for s in STEPS}
    ss.timings = {}
    ss.progress_msg = "Ready. Enter a topic and run the pipeline."


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown("### 🔎 ResearchMind")
    st.caption("Multi-agent research: search, read, write, critique.")
    st.toggle("Fast mode: skip critic review", key="skip_critic",
              help="Saves one full model call (often 10-30s).")
    st.markdown('<div class="label muted">History</div>', unsafe_allow_html=True)
    if not ss.history:
        st.caption("Your researched topics will appear here.")
    for idx in range(len(ss.history) - 1, -1, -1):
        item = ss.history[idx]
        st.button(
            f"{item['topic'][:34]}",
            key=f"hist_{idx}",
            on_click=load_history,
            args=(idx,),
            use_container_width=True,
            help=item["ts"],
        )
    if ss.history:
        st.button("Clear history", on_click=clear_history, use_container_width=True)

# ---------------------------------------------------------------- hero
st.markdown('<h1 class="hero-title">ResearchMind</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-sub">Four AI agents search the web, read the best source, write a '
    "full report and critique it, so you get a reviewed research report on any topic.</p>",
    unsafe_allow_html=True,
)

left, right = st.columns([1.1, 1], gap="large")

with left:
    st.markdown('<div class="label">Research topic</div>', unsafe_allow_html=True)
    with st.form("topic_form", border=False):
        st.text_input(
            "Research topic",
            key="topic",
            placeholder="e.g. Quantum computing breakthroughs in 2026",
            label_visibility="collapsed",
            max_chars=200,
        )
        run_clicked = st.form_submit_button("⚡ Run Research Pipeline", use_container_width=True)

    st.markdown('<div class="label muted">Try</div>', unsafe_allow_html=True)
    with st.container(key="chips"):
        for ex in EXAMPLES:
            st.button(ex, key=f"ex_{ex}", on_click=set_topic, args=(ex,))

with right:
    st.markdown("### Pipeline")
    pipeline_ph = st.empty()

progress_ph = st.empty()


def render():
    pipeline_ph.markdown(pipeline_html(ss.states, ss.timings), unsafe_allow_html=True)
    progress_ph.markdown(progress_html(ss.states, ss.progress_msg), unsafe_allow_html=True)


render()

# ---------------------------------------------------------------- run
if run_clicked:
    topic = (ss.topic or "").strip()
    cached = next((h for h in ss.history if h["topic"].lower() == topic.lower()), None)
    if len(topic) < 3:
        st.warning("Enter a topic with at least 3 characters.")
    elif cached:
        load_history(ss.history.index(cached))
        render()
        st.toast("Loaded from history (no new API calls)", icon="⚡")
    else:
        ss.states = {s["key"]: "waiting" for s in STEPS}
        ss.timings = {}
        ss.result = None
        data = {"topic": topic, "ts": datetime.now().strftime("%d %b %Y, %H:%M")}

        def run_step(idx: int, fn):
            step = STEPS[idx]
            ss.states[step["key"]] = "running"
            ss.progress_msg = step["working"]
            render()
            t0 = time.time()
            def on_wait(secs, rate_limited):
                why = "Rate limit reached" if rate_limited else "Temporary error"
                ss.progress_msg = f"{why}. Retrying {step['name']} in {secs:.0f}s..."
                render()

            try:
                out = with_retry(fn, on_wait=on_wait)
            except Exception as e:  # noqa: BLE001
                ss.states[step["key"]] = "error"
                ss.progress_msg = f"{step['name']} failed."
                render()
                raise RuntimeError(f"{step['name']}: {e}") from e
            ss.timings[step["key"]] = time.time() - t0
            ss.states[step["key"]] = "done"
            render()
            if COOLDOWN_SECS and idx < len(STEPS) - 1:
                ss.progress_msg = f"Pausing {COOLDOWN_SECS}s to stay under the API rate limit..."
                render()
                time.sleep(COOLDOWN_SECS)
            return out

        try:
            # 1. search
            data["search_results"] = as_text(run_step(0, lambda: run_agent(
                create_search_agent(),
                f"Find recent, Reliable and detailed infromation about: {topic}",
                "Search Agent")))

            # 2. scrape
            data["scraped_content"] = as_text(run_step(1, lambda: run_agent(
                create_scrap_agent(),
                f"Based on the following search results about '{topic}',"
                f"pick the most relevant URL and scrape it for deeper content. \n\n"
                f"Search result: \n{data['search_results'][:800]}",
                "Reader Agent")))

            # 3. write
            research = (
                f"SEARCH RESULTS: \n {data['search_results'][:WRITER_SEARCH_CHARS]} \n\n"
                f"DETAILD SCRAPED CONTENT: \n {data['scraped_content'][:WRITER_SCRAPE_CHARS]}"
            )
            data["report"] = as_text(run_step(2, lambda: writter_chain.invoke(
                {"topic": topic, "research": research})))

            # 4. critique
            if ss.get("skip_critic"):
                ss.states["critic"] = "skipped"
                ss.timings["critic"] = 0
                data["feedback"] = "Critic review was skipped (fast mode)."
                render()
            else:
                data["feedback"] = as_text(run_step(3, lambda: critic_chain.invoke(
                    {"report": data["report"]})))

            data["timings"] = dict(ss.timings)
            ss.result = data
            ss.history.append(data)
            ss.history = ss.history[-MAX_HISTORY:]
            total = sum(ss.timings.values())
            ss.progress_msg = f"Research complete in {fmt_secs(total)}."
            render()
            st.toast("Research complete", icon="✅")
        except Exception as e:  # noqa: BLE001
            if "429" in str(e) or "rate limit" in str(e).lower():
                st.error(
                    "The API rate limit was hit and retries did not clear it. Wait a minute and "
                    "run again, use a model with a higher limit, or upgrade your plan.\n\n"
                    f"Details: {e}"
                )
            else:
                st.error(
                    f"The pipeline stopped. {e}\n\n"
                    "Check your API keys in .env and your internet connection, then run it again."
                )

# ---------------------------------------------------------------- results
res = ss.result
if res:
    st.markdown("---")
    st.markdown(f'<div class="result-title">{html.escape(res["topic"])}</div>', unsafe_allow_html=True)

    report, feedback = res["report"], res["feedback"]
    urls = extract_urls(res["search_results"] + "\n" + res["scraped_content"])
    score = re.search(r"(\d+(?:\.\d+)?)\s*/\s*10", feedback)
    total_time = sum(res["timings"].values())
    stats = [
        (fmt_secs(total_time), "Total time"),
        (f"{len(report.split()):,}", "Words in report"),
        (str(len(urls)), "Sources found"),
        (f"{score.group(1)}/10" if score else "-", "Critic score"),
    ]
    st.markdown(
        '<div class="stats">'
        + "".join(f'<div class="stat"><div class="v">{v}</div><div class="k">{k}</div></div>' for v, k in stats)
        + "</div>",
        unsafe_allow_html=True,
    )

    tab_report, tab_feedback, tab_sources = st.tabs(["Report", "Critic feedback", "Sources"])

    slug = re.sub(r"[^a-z0-9]+", "-", res["topic"].lower()).strip("-") or "report"

    with tab_report:
        st.markdown(report)
        c1, c2, _ = st.columns([1, 1, 2])
        c1.download_button("Download report (.md)", report, f"{slug}.md", "text/markdown",
                           use_container_width=True)
        c2.download_button(
            "Report + feedback (.md)",
            f"{report}\n\n---\n\n## Critic feedback\n\n{feedback}",
            f"{slug}-full.md", "text/markdown", use_container_width=True,
        )

    with tab_feedback:
        st.markdown(feedback)

    with tab_sources:
        if urls:
            for u in urls:
                st.markdown(f'<div class="src"><a href="{html.escape(u)}" target="_blank" rel="noopener">{html.escape(u)}</a></div>',
                            unsafe_allow_html=True)
        else:
            st.caption("No URLs were found in the agent output.")
        with st.expander("Raw search results"):
            st.markdown(res["search_results"])
        with st.expander("Raw scraped content"):
            st.markdown(res["scraped_content"])