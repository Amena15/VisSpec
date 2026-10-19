"""
Shared traceability-enforcement predicates (Stage 5 / BR-11 / RQ3).

Single source of truth for "is this diagram element grounded in a source
requirement?". Used by BOTH:
  - backend/services/diagram/diagram_generator._check_compliance (production)
  - scripts/04_rq3_traceability_experiment.py (controlled experiment)

Keeping one implementation ensures the experiment evaluates the mechanism the
application actually ships, and lets tests assert the two stay equivalent.

Dependency-light by design (stdlib only) so the standalone experiment script
can import it without pulling in the full backend stack.
"""
import re
from typing import Dict

STOP = set(
    "the a an of to and or in on for with by is are be shall must should will "
    "can may that this it as at from".split()
)


def toks(s: str) -> set:
    """Content-word tokens (lowercase, len > 2, stopwords removed)."""
    return {w for w in re.findall(r"[a-z]+", s.lower()) if w not in STOP and len(w) > 2}


def stem(w: str) -> str:
    return re.sub(r"(ing|ed|es|s)$", "", w)


def grounded_actor(actor: str, sources: Dict[str, str]) -> bool:
    """An actor is grounded if ALL its content tokens appear in some source text."""
    a = {stem(w) for w in toks(actor)}
    return any(a and a <= {stem(w) for w in toks(t)} for t in sources.values())


def grounded_message(msg_text: str, req_id, sources: Dict[str, str],
                     min_overlap: float = 0.5) -> bool:
    """A message is grounded if it cites an existing requirement AND at least
    `min_overlap` of its content tokens appear in that requirement's text."""
    src = sources.get(req_id)
    if not src:
        return False                       # no traceable source id -> reject
    m = {stem(w) for w in toks(msg_text)}
    s = {stem(w) for w in toks(src)}
    return bool(m) and len(m & s) / len(m) >= min_overlap


def enforce_case(case: Dict) -> Dict:
    """Condition B for the RQ3 experiment: drop untraceable elements.

    Returns filtered copy + rejection counts (actors, messages).
    `case` = {"req_text": {rid: text}, "actors": [names],
              "messages": [{"from","to","text","req_id"}]}
    """
    src = case["req_text"]
    actors = [x for x in case["actors"] if grounded_actor(x, src)]
    msgs = [m for m in case["messages"]
            if grounded_message(m["text"], m.get("req_id"), src)
            and m["from"] in actors and m["to"] in actors]
    return dict(case, actors=actors, messages=msgs,
                rejected=(len(case["actors"]) - len(actors),
                          len(case["messages"]) - len(msgs)))
