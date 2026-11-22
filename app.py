import html
from urllib.parse import urlparse

import streamlit as st

from models import Brief
from workflow import orchestrator

st.set_page_config(page_title="Market Research Agents", layout="centered")

# ---------- Colors: set THEME to "ember", "ocean", "violet" or "forest" ----------
THEME = "ember"
PALETTES = {
    "ember": ("#7c3a14", "#6b1a35"),
    "ocean": ("#0f766e", "#2563eb"),
    "violet": ("#4f46e5", "#9d2a8f"),
    "forest": ("#166534", "#0f766e"),
}
C1, C2 = PALETTES[THEME]

st.markdown(
    f"""
<style>
.block-container {{max-width: 880px; padding-top: 5.5rem; padding-bottom: 4rem;}}
[data-testid="stSidebarHeader"] {{height: 2.6rem; min-height: 0; padding-bottom: 0; margin-bottom: 0;}}
[data-testid="stSidebarUserContent"] {{padding-top: .4rem; padding-bottom: 2rem;}}

/* accent colors for Streamlit widgets */
[data-testid="stFormSubmitButton"] button, button[kind="primaryFormSubmit"] {{
  background: linear-gradient(135deg, {C1}, {C2}); border: 0; color: #fff; font-weight: 600;
  padding: .65rem 1rem; transition: filter .15s, transform .15s;}}
[data-testid="stFormSubmitButton"] button:hover {{filter: brightness(1.12); transform: translateY(-1px); color: #fff;}}
.stTextInput [data-baseweb="input"]:focus-within {{border-color: {C2} !important; box-shadow: 0 0 0 1px {C2};}}
.stTabs [data-baseweb="tab-highlight"], .stTabs [class*="SelectionIndicator"] {{background-color: {C2} !important;}}
.stTabs [aria-selected="true"], .stTabs [aria-selected="true"] p {{color: {C2} !important; font-weight: 600;}}
.stDownloadButton button:hover {{border-color: {C2}; color: {C2};}}

/* hero */
.hero {{background: linear-gradient(135deg, {C1} 0%, {C2} 100%); padding: 32px 34px 28px; border-radius: 20px;
  color: #fff; margin-bottom: 18px; box-shadow: 0 12px 30px rgba(0,0,0,.14);}}
.hero h1 {{margin: 0; font-size: 2.1rem; color: #fff; padding: 0; letter-spacing: -.01em;}}
.hero p {{margin: 8px 0 14px; opacity: .93; font-size: 1.02rem;}}
.hero .tags span {{display: inline-block; font-size: .74rem; font-weight: 600; letter-spacing: .04em;
  padding: 4px 12px; margin: 0 6px 4px 0; border-radius: 999px; background: rgba(255,255,255,.16);
  border: 1px solid rgba(255,255,255,.28);}}

/* agent progress cards */
.agents {{display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 16px 0 8px;}}
.agent {{border: 1px solid rgba(128,128,128,.3); border-radius: 14px; padding: 12px 14px; min-height: 84px;
  background: rgba(128,128,128,.05);}}
.agent .no {{width: 24px; height: 24px; border-radius: 50%; font-size: .72rem; font-weight: 700;
  display: flex; align-items: center; justify-content: center; background: rgba(128,128,128,.25); margin-bottom: 7px;}}
.agent .nm {{font-weight: 700; font-size: .92rem;}}
.agent .st {{font-size: .76rem; opacity: .72; margin-top: 2px; line-height: 1.35;}}
.agent.work {{border-color: {C2}; background: rgba(128,128,128,.08); animation: pulse 1.3s infinite;}}
.agent.work .no {{background: {C2}; color: #fff;}}
.agent.done {{border-color: rgba(34,197,94,.55); background: rgba(34,197,94,.09);}}
.agent.done .no {{background: #16a34a; color: #fff;}}
@keyframes pulse {{0% {{box-shadow: 0 0 0 0 rgba(128,128,128,.45);}} 100% {{box-shadow: 0 0 0 12px rgba(128,128,128,0);}}}}

/* stat tiles */
.tiles {{display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 6px 0 16px;}}
.tile {{border: 1px solid rgba(128,128,128,.25); border-radius: 14px; padding: 14px 16px;
  background: rgba(128,128,128,.05);}}
.tile .v {{font-size: 1.55rem; font-weight: 700; line-height: 1.1; color: {C2};}}
.tile .l {{font-size: .74rem; letter-spacing: .06em; text-transform: uppercase; opacity: .7; margin-top: 4px;}}

/* empty state */
.sec-title {{font-size: .78rem; letter-spacing: .1em; text-transform: uppercase; font-weight: 700;
  color: {C1}; margin: 26px 0 10px;}}
.feat-grid {{display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;}}
.feat {{border: 1px solid rgba(128,128,128,.25); border-radius: 16px; padding: 16px 18px;
  background: rgba(128,128,128,.05);}}
.feat::before {{content: ""; display: block; width: 30px; height: 4px; border-radius: 4px; margin-bottom: 12px;
  background: linear-gradient(135deg, {C1}, {C2});}}
.feat .ft {{font-weight: 700; font-size: 1rem; margin-bottom: 4px;}}
.feat .fd {{font-size: .86rem; line-height: 1.55; opacity: .8;}}

/* result cards */
.card {{border: 1px solid rgba(128,128,128,.25); border-radius: 16px; padding: 18px 22px; margin-bottom: 14px;
  background: rgba(128,128,128,.05);}}
.card h4 {{margin: 0 0 10px; font-size: .78rem; letter-spacing: .1em; text-transform: uppercase; color: {C1};}}
.card.warn {{border-color: rgba(245,158,11,.5); background: rgba(245,158,11,.08);}}
.card.warn h4 {{color: #d97706;}}
.chip {{display: inline-block; background: rgba(128,128,128,.16); padding: 6px 16px; border-radius: 999px;
  margin: 3px 8px 3px 0; font-weight: 600; font-size: .92rem;}}
.obs {{display: flex; gap: 12px; margin: 10px 0; align-items: flex-start;}}
.num {{flex: 0 0 28px; height: 28px; border-radius: 50%; background: linear-gradient(135deg, {C1}, {C2});
  color: #fff; display: flex; align-items: center; justify-content: center; font-size: .8rem; font-weight: 700;}}
.src {{display: block; padding: 10px 12px; border-radius: 10px; margin: 6px 0; text-decoration: none;
  border: 1px solid rgba(128,128,128,.25); background: rgba(128,128,128,.05);}}
.src:hover {{border-color: {C2};}}
.src .t {{font-weight: 600; font-size: .9rem; color: inherit;}}
.src .d {{font-size: .75rem; opacity: .65; color: inherit;}}
.badge {{display: inline-block; padding: 3px 12px; border-radius: 999px; font-size: .75rem; font-weight: 700;}}
.badge.web {{background: rgba(34,197,94,.18); color: #16a34a;}}
.badge.sample {{background: rgba(245,158,11,.2); color: #d97706;}}

/* sidebar timeline */
.side-title {{font-size: 1.2rem; font-weight: 700; margin: 4px 0 4px;}}
.side-sub {{font-size: .85rem; opacity: .72; margin-bottom: 22px; line-height: 1.5;}}
.tl-item {{position: relative; padding-left: 50px; margin-bottom: 26px;}}
.tl-item:not(:last-child)::before {{content: ""; position: absolute; left: 15px; top: 38px; bottom: -22px;
  width: 2px; background: rgba(128,128,128,.28);}}
.tl-num {{position: absolute; left: 0; top: 0; width: 32px; height: 32px; border-radius: 50%;
  background: linear-gradient(135deg, {C1}, {C2}); color: #fff; font-weight: 700; font-size: .85rem;
  display: flex; align-items: center; justify-content: center;}}
.tl-name {{font-weight: 700; font-size: 1.02rem; line-height: 1.2; padding-top: 1px;}}
.tl-tag {{font-size: .68rem; letter-spacing: .1em; text-transform: uppercase; font-weight: 700; color: {C1}; margin: 3px 0 7px;}}
.tl-desc {{font-size: .85rem; line-height: 1.6; opacity: .88;}}
.tl-io {{margin-top: 10px; display: flex; gap: 6px; flex-wrap: wrap;}}
.pill {{font-size: .7rem; padding: 3px 10px; border-radius: 999px; border: 1px solid rgba(128,128,128,.35);
  background: rgba(128,128,128,.07);}}
.pill b {{opacity: .55; font-weight: 700; margin-right: 6px; letter-spacing: .06em;}}
.tip {{margin-top: 6px; padding: 12px 14px; font-size: .82rem; line-height: 1.55; border-radius: 10px;
  border-left: 3px solid {C2}; background: rgba(128,128,128,.08);}}

@media (max-width: 700px) {{.agents, .tiles {{grid-template-columns: repeat(2, 1fr);}} .feat-grid {{grid-template-columns: 1fr;}}}}
</style>
""",
    unsafe_allow_html=True,
)

AGENT_NAMES = ["Orchestrator", "Researcher", "Analyst", "Critic"]
STATUS_TEXT = {"wait": "Waiting", "work": "Working...", "done": "Done"}

ROLES = [
    ("Orchestrator", "The project manager",
     "Receives your topic, starts the workflow and hands the work from one role to the next. "
     "It also allows the Analyst one revision if the Critic asks for it.",
     "your topic", "final brief"),
    ("Researcher", "Finds the evidence",
     "Searches the web and keeps only facts that appear in the results it found. "
     "It also notes what it could not find.",
     "your topic", "facts, sources, gaps"),
    ("Analyst", "Writes the brief",
     "Turns the findings into a short brief: summary, up to two competitors, key observations, "
     "sources and missing information.",
     "findings", "draft brief"),
    ("Critic", "Checks the work",
     "Compares the draft with the findings, flags unsupported claims, and either approves the brief "
     "or sends it back once with specific feedback.",
     "findings + draft", "approve or revise"),
]

FEATURES = [
    ("Summary", "A short, plain overview of the company or market."),
    ("Competitors", "Up to two competitors, only when the evidence supports them."),
    ("Key observations", "The main takeaways, each grounded in the search results."),
    ("Sources and gaps", "Linked sources, plus a clear list of what could not be found."),
]


def esc(t: str) -> str:
    return html.escape(str(t))


def agents_html(states: list[str], details: list[str] | None = None) -> str:
    cells = []
    for i, (name, s) in enumerate(zip(AGENT_NAMES, states), 1):
        text = details[i - 1] if details and s == "done" and details[i - 1] else STATUS_TEXT[s]
        cells.append(
            f'<div class="agent {s}"><div class="no">{i}</div><div class="nm">{name}</div>'
            f'<div class="st">{esc(text)}</div></div>'
        )
    return '<div class="agents">' + "".join(cells) + "</div>"


def final_agents_html(state) -> str:
    details = [
        "Workflow complete",
        f"{len(state.findings.facts)} facts, {len(state.findings.sources)} sources",
        "Revised once" if state.revised else "Draft written",
        "Approved" if state.critique.approved else "Requested 1 revision",
    ]
    return agents_html(["done"] * 4, details)


def card(title: str, body: str, warn: bool = False) -> None:
    cls = "card warn" if warn else "card"
    st.markdown(f'<div class="{cls}"><h4>{title}</h4>{body}</div>', unsafe_allow_html=True)


def bullets_html(items: list[str], fallback: str) -> str:
    if not items:
        return f"<em>{fallback}</em>"
    return "<ul>" + "".join(f"<li>{esc(i)}</li>" for i in items) + "</ul>"


def sources_html(items: list[str]) -> str:
    if not items:
        return "<em>None</em>"
    out = []
    for s in items:
        title, url = s, ""
        if " - http" in s:
            title, url = s.rsplit(" - http", 1)
            url = "http" + url
        if url:
            out.append(
                f'<a class="src" href="{esc(url)}" target="_blank">'
                f'<div class="t">{esc(title)}</div><div class="d">{esc(urlparse(url).netloc)}</div></a>'
            )
        else:
            out.append(f'<div class="src"><div class="t">{esc(title)}</div></div>')
    return "".join(out)


def brief_to_markdown(query: str, b: Brief, origin: str) -> str:
    def bl(items):
        return "\n".join(f"- {i}" for i in items) or "- None"

    return (
        f"# Research brief: {query}\n\n_Data origin: {origin}_\n\n## Summary\n{b.summary}\n\n"
        f"## Competitors\n{bl(b.competitors)}\n\n## Key observations\n{bl(b.key_observations)}\n\n"
        f"## Sources\n{bl(b.sources)}\n\n## Missing information\n{bl(b.missing_information)}\n"
    )


# ---------- Sidebar ----------
with st.sidebar:
    st.markdown(
        '<div class="side-title">How it works</div>'
        '<div class="side-sub">Four AI roles work one after another. Each one passes structured data '
        "to the next.</div>",
        unsafe_allow_html=True,
    )
    items = "".join(
        f'<div class="tl-item"><div class="tl-num">{n}</div><div class="tl-name">{name}</div>'
        f'<div class="tl-tag">{tag}</div><div class="tl-desc">{desc}</div>'
        f'<div class="tl-io"><span class="pill"><b>IN</b>{i_in}</span>'
        f'<span class="pill"><b>OUT</b>{i_out}</span></div></div>'
        for n, (name, tag, desc, i_in, i_out) in enumerate(ROLES, 1)
    )
    st.markdown(f'<div class="tl">{items}</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="tip"><b>Tip:</b> a specific topic gives better results. '
        '"Ride-hailing in Nepal" works better than "transport". '
        "Open the <b>Agent handoffs</b> tab to see what each role passed on.</div>",
        unsafe_allow_html=True,
    )

# ---------- Header and input ----------
st.markdown(
    '<div class="hero"><h1>Market Research Agents</h1>'
    "<p>Type any company or industry. Four AI roles research it, write a short brief and review it.</p>"
    '<div class="tags"><span>LIVE WEB RESEARCH</span><span>STRUCTURED HANDOFFS</span>'
    "<span>CRITIC REVIEW</span></div></div>",
    unsafe_allow_html=True,
)

with st.form("research_form"):
    query = st.text_input("Company or industry", placeholder="Type any company or industry, then press Enter")
    start = st.form_submit_button("Start research", type="primary", use_container_width=True)

pipe_slot = st.empty()
msg_slot = st.empty()

# ---------- Run ----------
if start:
    if not query.strip():
        st.warning("Please type a company or industry first.")
    else:
        def notify(msg: str) -> None:
            idx = 1 if "Researcher" in msg else 3 if "Critic" in msg else 2
            states = ["done"] * idx + ["work"] + ["wait"] * (3 - idx)
            pipe_slot.markdown(agents_html(states), unsafe_allow_html=True)
            msg_slot.caption(msg)

        pipe_slot.markdown(agents_html(["work", "wait", "wait", "wait"]), unsafe_allow_html=True)
        try:
            st.session_state["state"] = orchestrator(query, notify=notify)
            msg_slot.empty()
        except Exception as e:  # noqa: BLE001
            pipe_slot.empty()
            msg_slot.empty()
            st.session_state.pop("state", None)
            st.error(str(e))

# ---------- Results ----------
state = st.session_state.get("state")
if state and state.final:
    pipe_slot.markdown(final_agents_html(state), unsafe_allow_html=True)
    b, origin = state.final, state.findings.data_origin
    tab_brief, tab_flow = st.tabs(["Research brief", "Agent handoffs"])

    with tab_brief:
        badge = (
            '<span class="badge web">Live web sources</span>'
            if origin == "web"
            else '<span class="badge sample">Sample data, not live research</span>'
        )
        rev = " &nbsp;·&nbsp; revised once after Critic feedback" if state.revised else ""
        st.markdown(f"<h2 style='margin-bottom:6px'>{esc(state.query)}</h2>{badge}{rev}", unsafe_allow_html=True)
        st.write("")
        tiles = [
            (len(state.findings.sources), "Sources"),
            (len(state.findings.facts), "Facts found"),
            (len(b.competitors), "Competitors"),
            ("Approved" if state.critique.approved else "Revised", "Critic verdict"),
        ]
        st.markdown(
            '<div class="tiles">'
            + "".join(f'<div class="tile"><div class="v">{v}</div><div class="l">{l}</div></div>' for v, l in tiles)
            + "</div>",
            unsafe_allow_html=True,
        )
        card("Summary", f"<p style='margin:0'>{esc(b.summary)}</p>")
        chips = "".join(f'<span class="chip">{esc(c)}</span>' for c in b.competitors) or "<em>None identified</em>"
        card("Competitors", chips)
        obs = "".join(
            f'<div class="obs"><div class="num">{i}</div><div>{esc(o)}</div></div>'
            for i, o in enumerate(b.key_observations, 1)
        )
        card("Key observations", obs or "<em>None</em>")
        card("Sources", sources_html(b.sources))
        card("Missing information", bullets_html(b.missing_information, "None noted"), warn=True)
        st.download_button(
            "Download brief (.md)", brief_to_markdown(state.query, b, origin), "brief.md", use_container_width=True
        )

    with tab_flow:
        st.markdown("**Activity log**")
        for line in state.log:
            st.markdown(f"- {line}")
        st.markdown("**Critic verdict:** " + ("Approved" if state.critique.approved else "Revision requested (done once)"))
        if state.critique.feedback:
            st.info(f"Critic feedback: {state.critique.feedback}")
        with st.expander("Researcher findings"):
            st.json(state.findings.model_dump())
        with st.expander("Analyst draft"):
            st.json(state.draft.model_dump())
        with st.expander("Critic verdict (raw)"):
            st.json(state.critique.model_dump())
        with st.expander("Full shared state"):
            st.json(state.model_dump())
elif not start:
    st.markdown('<div class="sec-title">What your brief will contain</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="feat-grid">'
        + "".join(f'<div class="feat"><div class="ft">{t}</div><div class="fd">{d}</div></div>' for t, d in FEATURES)
        + "</div>",
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sec-title">The workflow</div>', unsafe_allow_html=True)
    st.markdown(agents_html(["wait"] * 4, None).replace("Waiting", "Ready"), unsafe_allow_html=True)