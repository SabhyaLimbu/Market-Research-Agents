"""Four sequential roles: Orchestrator -> Researcher -> Analyst -> Critic (max one revision)."""
from typing import Callable, Optional

from llm import ask_json
from models import Brief, Critique, Findings, WorkflowState
from search import web_search

Notify = Optional[Callable[[str], None]]

RESEARCHER_SYSTEM = (
    "You are a market Researcher. Extract concise facts relevant to the query using ONLY the "
    "search results given. Do not add outside knowledge. Copy the used sources into `sources`. "
    "Also extract: (a) any company or brand names the results mention as players in this market, "
    "with what the result says about each; (b) any figures with their unit and year. "
    "Only list something in `gaps` if the results truly do not contain it."
)


def researcher(state: WorkflowState) -> WorkflowState:
    sources, origin, err = web_search(state.query)
    if origin == "none":
        raise RuntimeError(
            f"Web search found nothing for '{state.query}', so no research can be done. "
            f"Check your internet connection/VPN and try again. Details: {err}"
        )
    listing = "\n".join(f"[{i}] {s.title} | {s.url}\n{s.snippet}" for i, s in enumerate(sources))
    findings = ask_json(
        RESEARCHER_SYSTEM + f" Set data_origin to '{origin}'.",
        f"Query: {state.query}\n\nSearch results:\n{listing}",
        Findings,
    )
    findings.data_origin = origin
    state.findings = findings
    state.log.append(f"Researcher: {len(findings.facts)} facts, origin={origin}")
    return state


ANALYST_SYSTEM = (
    "You are a market Analyst. Write a SHORT brief grounded only in the provided findings: a summary, "
    "up to two competitors (include them when the findings name companies; otherwise leave empty), "
    "key observations, the sources used, and missing information. "
    "Key observations must describe the market itself, add something beyond the summary, and must not "
    "describe who publishes the sources. Include a figure only if it appears in the findings and its "
    "meaning is clear; otherwise leave it out. If data_origin is 'sample', say so in the summary. "
    "Never invent figures."
)


def analyst(state: WorkflowState, feedback: str = "") -> Brief:
    prompt = f"Query: {state.query}\n\nFindings:\n{state.findings.model_dump_json(indent=2)}"
    if feedback:
        prompt += (
            f"\n\nPrevious draft:\n{state.draft.model_dump_json(indent=2)}"
            f"\n\nCritic feedback to address:\n{feedback}"
        )
    brief = ask_json(ANALYST_SYSTEM, prompt, Brief)
    brief.competitors = brief.competitors[:2]
    
    used = [
        src
        for src in state.findings.sources
        if any(
            src.title.lower()[:40] in b.lower() or b.lower() in src.title.lower()
            for b in brief.sources
        )
    ] or state.findings.sources
    brief.sources = [f"{src.title} - {src.url}" if src.url else src.title for src in used]
    return brief


CRITIC_SYSTEM = (
    "You are a strict Critic. Check the DRAFT against the findings. "
    "HARD RULE: the brief may list AT MOST two competitors. Two competitors is the correct "
    "maximum. NEVER ask for more than two, and NEVER request a revision because the findings "
    "name more companies than the draft lists. "
    "Request a revision (approved=false) ONLY if: "
    "(1) a claim or figure in the draft is not supported by the findings; "
    "(2) the draft has zero competitors although the findings name at least one company; "
    "(3) a key observation merely repeats the summary or describes who publishes the sources "
    "instead of describing the market; "
    "(4) a figure's meaning is unclear; "
    "(5) the draft has more than two competitors or has no sources. "
    "If none of these apply, set approved=true. "
    "When requesting a revision, give specific, actionable feedback that never contradicts the hard rule."
)


def critic(state: WorkflowState) -> Critique:
    return ask_json(
        CRITIC_SYSTEM,
        f"Findings:\n{state.findings.model_dump_json(indent=2)}\n\nDraft:\n{state.draft.model_dump_json(indent=2)}",
        Critique,
    )


def orchestrator(query: str, notify: Notify = None) -> WorkflowState:
    say = notify or (lambda _m: None)
    state = WorkflowState(query=query.strip())
    state.log.append("Orchestrator: workflow started")

    say("Researcher is gathering information...")
    state = researcher(state)

    say("Analyst is writing the draft...")
    state.draft = analyst(state)

    say("Critic is reviewing the draft...")
    state.critique = critic(state)

    if state.critique.approved:
        state.final = state.draft
        state.log.append("Critic: approved")
    else:
        say("Analyst is revising once based on critic feedback...")
        state.final = analyst(state, feedback=state.critique.feedback)
        state.revised = True
        state.log.append("Critic: requested revision; Analyst revised once")
    return state