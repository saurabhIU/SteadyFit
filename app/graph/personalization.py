"""Personal-doc personalization for plan-generating turns.

Qualitative only — never auto-extracts weight/height/age from documents.
Structured profile fields always win over conflicting doc text.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from app.graph.state import UserProfile, WeekPlan, WorkoutDay
from app.memory.store import user_has_personal_docs
from app.rag.retriever import retrieve_personal

logger = logging.getLogger("steadyfit.personalization")

PERSONALIZATION_ANNOUNCEMENT = (
    "I see you've uploaded a personal document — I've factored it into this plan."
)

_PLAN_CONTEXT_QUERY = (
    "health conditions injuries constraints exercises to avoid "
    "training limitations preferences food diet allergies notes"
)

# Loose "avoid X" / "no X" patterns from unstructured notes (not a medical NER).
_AVOID_PATTERNS: list[tuple[re.Pattern[str], list[str], str]] = [
    (
        re.compile(r"(?i)avoid\s+overhead\s+press(?:ing)?|no\s+overhead\s+press(?:ing)?|"
                   r"shoulder\s+issue[^.]*overhead|overhead[^.]*shoulder"),
        ["overhead press", "shoulder press", "military press", "ohp", "strict press"],
        "overhead pressing",
    ),
    (
        re.compile(r"(?i)avoid\s+(?:deep\s+)?(?:loaded\s+)?squats?|no\s+(?:deep\s+)?(?:loaded\s+)?squats?|"
                   r"knee[^.]*(?:no|avoid)\s+squat"),
        ["back squat", "barbell squat", "goblet squat", "deep squat"],
        "deep/loaded squats",
    ),
    (
        re.compile(r"(?i)back\s+pain|lower[\s-]back|spinal|lumbar"),
        [
            "barbell back squat",
            "back squat",
            "barbell squat",
            "conventional deadlift",
            "barbell deadlift",
            "deadlift",
            "good morning",
        ],
        "heavy spinal loading (back squat/conventional deadlift)",
    ),
    (
        re.compile(r"(?i)avoid\s+lunges?|no\s+lunges?|knee[^.]*lunge"),
        ["lunge", "walking lunge", "reverse lunge", "split squat"],
        "lunges",
    ),
    (
        re.compile(r"(?i)avoid\s+deadlifts?|no\s+(?:conventional\s+)?deadlifts?|"
                   r"back[^.]*(?:no|avoid)\s+deadlift"),
        ["deadlift", "conventional deadlift", "barbell deadlift"],
        "deadlifts",
    ),
]

_FOOD_AVOID_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"(?i)(?:do\s*not|don'?t|donot|no|avoid|never).{0,48}\bbe[ae]f\b"
        ),
        "beef",
    ),
    (
        re.compile(
            r"(?i)(?:do\s*not|don'?t|donot|no|avoid|never).{0,48}\bpork\b"
        ),
        "pork",
    ),
]

_NONVEG_CUES = re.compile(
    r"(?i)\b(chicken|beef|pork|fish|salmon|turkey|lamb|meat|non[- ]?veg)\b"
)
_VEG_CUES = re.compile(r"(?i)\b(vegetarian|vegan|plant[- ]based)\b")

# Diagnosed-condition cues from uploaded docs — used for gentle, non-medical
# food heads-ups (e.g. sugary food + diabetes), never for diagnosis/exercise gating.
_HEALTH_CONDITION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"(?i)\btype\s*[12]\s*diabet(?:es|ic)?\b|\bdiabet(?:es|ic)\b|"
            r"blood\s+sugar|blood\s+glucose"
        ),
        "diabetes",
    ),
    (
        re.compile(r"(?i)\bhypertension\b|high\s+blood\s+pressure\b"),
        "hypertension",
    ),
]


@dataclass
class PersonalPlanContext:
    chunks: list[str] = field(default_factory=list)
    citations: list[dict] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    avoid_labels: list[str] = field(default_factory=list)
    avoid_terms: list[str] = field(default_factory=list)
    food_avoids: list[str] = field(default_factory=list)
    health_conditions: list[str] = field(default_factory=list)
    has_docs: bool = False

    @property
    def prompt_block(self) -> str:
        if not self.chunks:
            return ""
        conflict_lines = ""
        if self.conflicts:
            conflict_lines = (
                "\nPROFILE WINS (do not override structured profile with doc text):\n"
                + "\n".join(f"- {c}" for c in self.conflicts)
                + "\n"
            )
        avoid_line = ""
        if self.avoid_labels:
            avoid_line = (
                "Document-noted constraints to respect in the week plan: "
                + ", ".join(self.avoid_labels)
                + ". Substitute safer alternatives; cite [doc:…] when you do.\n"
            )
        food_line = ""
        if self.food_avoids:
            food_line = (
                "Document food avoids (never put these in meals): "
                + ", ".join(self.food_avoids)
                + ".\n"
            )
        body = "\n\n".join(self.chunks[:6])
        return (
            "PERSONAL DOCUMENTS (user uploads — qualitative guidance only; "
            "do NOT invent weight/height/age from these):\n"
            f"{body}\n"
            f"{avoid_line}"
            f"{food_line}"
            f"{conflict_lines}"
            "You MUST emit a structured WeekPlan JSON for this turn (plan_changed) — "
            "do not answer as advisory-only when rebuilding or applying doc constraints.\n"
        )


def _citations_from_chunks(chunks: list[str]) -> list[dict]:
    cites: list[dict] = []
    seen: set[str] = set()
    for chunk in chunks:
        m = re.search(r"\[doc:([^\]]+)\]", chunk)
        if not m:
            continue
        source = m.group(1).strip()
        if not source or source in seen:
            continue
        seen.add(source)
        cites.append({
            "source_file": source,
            "section": "",
            "kb_id": None,
            "snippet": chunk[:200].replace("\n", " ").strip(),
            "tag": f"[doc: {source}]",
        })
    return cites


def _detect_conflicts(profile: UserProfile, chunks: list[str]) -> list[str]:
    blob = "\n".join(chunks)
    conflicts: list[str] = []
    pref = (profile.food_preference or "").lower()
    if pref in {"vegetarian", "vegan", "eggetarian"} and _NONVEG_CUES.search(blob):
        msg = (
            f"Doc mentions animal foods but profile food_preference={pref!r} — "
            "keeping structured profile."
        )
        conflicts.append(msg)
        logger.info("doc_profile_conflict user_food_pref=%s", pref)
    if pref in {"non-vegetarian", "no-preference"} and _VEG_CUES.search(blob):
        # Soft note only when profile explicitly non-veg vs doc vegetarian claim
        if pref == "non-vegetarian":
            msg = (
                f"Doc mentions vegetarian/vegan cues but profile food_preference="
                f"{pref!r} — keeping structured profile."
            )
            conflicts.append(msg)
            logger.info("doc_profile_conflict user_food_pref=%s", pref)
    return conflicts


def _extract_avoid_rules(chunks: list[str]) -> tuple[list[str], list[str]]:
    blob = "\n".join(chunks)
    labels: list[str] = []
    terms: list[str] = []
    for pattern, term_list, label in _AVOID_PATTERNS:
        if pattern.search(blob):
            if label not in labels:
                labels.append(label)
            for t in term_list:
                if t.lower() not in {x.lower() for x in terms}:
                    terms.append(t)
    return labels, terms


def _extract_food_avoids(chunks: list[str]) -> list[str]:
    blob = "\n".join(chunks)
    avoids: list[str] = []
    for pattern, label in _FOOD_AVOID_PATTERNS:
        if pattern.search(blob) and label not in avoids:
            avoids.append(label)
    return avoids


def _extract_health_conditions(chunks: list[str]) -> list[str]:
    blob = "\n".join(chunks)
    labels: list[str] = []
    for pattern, label in _HEALTH_CONDITION_PATTERNS:
        if pattern.search(blob) and label not in labels:
            labels.append(label)
    return labels


def _personal_doc_text_blob(user_id: str) -> str:
    """All personal upload text for constraint extraction (not just top-k RAG)."""
    from app.memory.store import _conn

    personal_types = ("personal", "program", "recipes", "reference", "knowledge")
    try:
        with _conn() as c:
            rows = c.execute(
                """
                SELECT text FROM documents
                WHERE user_id = %s AND doc_type = ANY(%s)
                ORDER BY created_at DESC
                LIMIT 40
                """,
                (user_id, list(personal_types)),
            ).fetchall()
    except Exception:
        logger.exception("personal doc blob load failed user=%s", user_id)
        return ""
    return "\n".join((r["text"] or "") for r in rows if r.get("text"))


def load_personal_plan_context(
    user_id: str,
    profile: UserProfile,
    *,
    query: str = _PLAN_CONTEXT_QUERY,
) -> PersonalPlanContext:
    """Retrieve personal docs for plan generation; empty if none."""
    uid = (user_id or "").strip()
    if not uid:
        try:
            from app.memory.user_context import get_current_user_id

            uid = (get_current_user_id() or "").strip()
        except Exception:
            uid = ""
    if not uid or not user_has_personal_docs(uid):
        return PersonalPlanContext(has_docs=False)
    # Constraint extraction uses the full upload blob so injury/food lines are
    # not missed when vector retrieval returns other sections.
    blob = _personal_doc_text_blob(uid)
    try:
        chunks = retrieve_personal(query, k=6, user_id=uid)
    except Exception:
        logger.exception("retrieve_personal failed user=%s", uid)
        chunks = []
    usable = [
        c for c in chunks
        if c and "[doc:error]" not in c and "no matching" not in c.lower()
    ]
    rule_source = [blob] if blob.strip() else usable
    conflicts = _detect_conflicts(profile, rule_source or usable)
    labels, terms = _extract_avoid_rules(rule_source or usable)
    food_avoids = _extract_food_avoids(rule_source or usable)
    health_conditions = _extract_health_conditions(rule_source or usable)
    return PersonalPlanContext(
        chunks=usable or ([f"[doc:upload] {blob[:1200]}"] if blob.strip() else []),
        citations=_citations_from_chunks(usable) if usable else (
            [{"source_file": "upload", "section": "", "kb_id": None,
              "snippet": blob[:200].replace("\n", " "), "tag": "[doc: upload]"}]
            if blob.strip() else []
        ),
        conflicts=conflicts,
        avoid_labels=labels,
        avoid_terms=terms,
        food_avoids=food_avoids,
        health_conditions=health_conditions,
        has_docs=True,
    )


def scrub_week_plan_for_avoids(
    plan: WeekPlan,
    avoid_terms: list[str],
    *,
    source_tag: str | None = None,
) -> WeekPlan:
    """Deterministic post-pass: replace all focus phrases matching avoid terms."""
    if not avoid_terms or not plan.days:
        return plan
    cite = f" {source_tag}" if source_tag else ""
    # Longest first so "barbell back squat" wins over "back squat" / "squat".
    terms = sorted({t for t in avoid_terms if t}, key=len, reverse=True)
    new_days: list[WorkoutDay] = []
    for day in plan.days:
        focus = day.focus or ""
        cleaned = focus
        hit_any = False
        for term in terms:
            if term.lower() in cleaned.lower():
                hit_any = True
                cleaned = re.sub(
                    re.escape(term), "joint-safer alternative", cleaned, flags=re.I
                )
        if not hit_any:
            new_days.append(day)
            continue
        if "joint-safer" not in cleaned.lower():
            cleaned = f"{focus} → swapped to joint-safer alternative"
        if cite and cite.strip() not in cleaned:
            cleaned = f"{cleaned}{cite}"
        new_days.append(day.model_copy(update={"focus": cleaned}))
    notes = (plan.notes or "").strip()
    if avoid_terms:
        note_bit = (
            "Personal-doc constraints applied"
            + (f" {source_tag}" if source_tag else "")
            + "."
        )
        if note_bit.lower() not in notes.lower():
            notes = f"{notes} {note_bit}".strip()
    return plan.model_copy(update={"days": new_days, "notes": notes})


def scrub_diet_for_food_avoids(
    meals: list[dict],
    food_avoids: list[str],
    *,
    source_tag: str | None = None,
) -> list[dict]:
    """Drop/replace meal rows that contain document food avoids (e.g. beef, pork)."""
    if not meals or not food_avoids:
        return meals
    avoids = [a.lower() for a in food_avoids if a]
    if not avoids:
        return meals
    # Common safe swaps when a banned meat appears.
    replacements = {
        "beef": "Grilled chicken breast + rice + salad",
        "pork": "Baked salmon + potatoes + greens",
        "beaf": "Grilled chicken breast + rice + salad",
    }
    out: list[dict] = []
    for meal in meals:
        row = dict(meal)
        text = (row.get("food_description") or "").lower()
        hit = next((a for a in avoids if a in text), None)
        if hit:
            swap = replacements.get(hit, "Lentil bowl + brown rice + veggies")
            row["food_description"] = swap
            if source_tag and source_tag not in str(row.get("citation") or ""):
                prior = (row.get("citation") or "").strip()
                row["citation"] = f"{prior} {source_tag}".strip()
        out.append(row)
    return out


def apply_personalization_flags(
    proposals: dict,
    ctx: PersonalPlanContext,
) -> dict:
    """Set additive reply note + conflict log when personal docs informed the plan."""
    out = dict(proposals)
    if not ctx.has_docs:
        return out
    out["personalization_note"] = PERSONALIZATION_ANNOUNCEMENT
    if ctx.conflicts:
        out["doc_profile_conflicts"] = list(ctx.conflicts)
    if ctx.food_avoids:
        out["doc_food_avoids"] = list(ctx.food_avoids)
    return out
