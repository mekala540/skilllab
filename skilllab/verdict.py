"""Turn run records into per-skill verdicts and a list of gaps."""

from __future__ import annotations

import re
from math import comb, sqrt
from statistics import median
from typing import Dict, List, Optional

HELPS, HURTS, NO_LIFT, FLAGGED, MIXED = "helps", "hurts", "no lift", "flagged", "mixed"

# A verdict needs both: a difference unlikely to be luck (Fisher's exact test, p <= ALPHA)
# and big enough to matter (at least DEFAULT_THRESHOLD of pass rate).
DEFAULT_THRESHOLD = 0.3
DEFAULT_ALPHA = 0.1
MIN_VALID = 2
SMALL_SAMPLE = 5  # below this, only large effects can reach significance
COSTLY_UPFRONT = 100  # tokens every session
COSTLY_ONUSE = 2000

# Skills built around a conversation with a person can't be measured by an unattended run.
NEEDS_PERSON = re.compile(
    r"\b(grill\w*|interview\w*|questionnaire|teach\w*|retro(spective)?|hand ?off|"
    r"conversation|re-pitch|walks? a human|ask (me|the user)|user wants to (talk|discuss)|"
    r"discussing|chat with)\b", re.I)


def needs_person(skill: dict) -> bool:
    return bool(NEEDS_PERSON.search(skill["name"].replace("-", " ") + " " + skill["description"]))


def fisher_p(a: int, n1: int, c: int, n2: int) -> float:
    """Two-sided Fisher's exact test: a passes of n1 vs c passes of n2."""
    k, n = a + c, n1 + n2

    def prob(x):
        return comb(n1, x) * comb(n2, k - x) / comb(n, k)

    observed = prob(a)
    lo, hi = max(0, k - n2), min(n1, k)
    return min(1.0, sum(prob(x) for x in range(lo, hi + 1) if prob(x) <= observed * (1 + 1e-9)))


def wilson(k: int, n: int, z: float = 1.645) -> Optional[tuple]:
    """90% Wilson score interval for k successes out of n."""
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(max(0.0, centre - half), 3), round(min(1.0, centre + half), 3))


def _cost_per_pass(recs: List[dict]) -> Optional[float]:
    passes = sum(r["passed"] for r in recs)
    costs = [r.get("cost_usd") for r in recs]
    if not passes or any(c is None for c in costs):
        return None
    return sum(costs) / passes


def _rate(recs: List[dict]) -> Optional[float]:
    return sum(r["passed"] for r in recs) / len(recs) if recs else None


def _med(values) -> Optional[float]:
    vals = [v for v in values if v is not None]
    return median(vals) if vals else None


def summarize(records: List[dict], skills: List[dict], tasks: List[dict],
              untested: List[str], threshold: float = DEFAULT_THRESHOLD,
              alpha: float = DEFAULT_ALPHA, matches: Optional[Dict[str, dict]] = None) -> dict:
    """matches: the relevance decisions ({"skill|task": {relevant, reason, by}}), shown per pair."""
    matches = matches or {}
    valid = [r for r in records if not r.get("infra_error")]
    errors = len(records) - len(valid)

    baseline: Dict[str, dict] = {}
    for t in tasks:
        recs = [r for r in valid if r["arm"] == "baseline" and r["task"] == t["id"]]
        if recs:
            passes = sum(r["passed"] for r in recs)
            baseline[t["id"]] = {"n": len(recs), "passes": passes, "rate": _rate(recs),
                                 "ci": wilson(passes, len(recs)),
                                 "cost": _med(r.get("cost_usd") for r in recs),
                                 "cost_per_pass": _cost_per_pass(recs)}

    pairs = []
    for s in skills:
        for t in tasks:
            recs = [r for r in valid if r["arm"] in ("skill", "pack")
                    and r["skill"] == s["id"] and r["task"] == t["id"]]
            if not recs:
                continue
            base = baseline.get(t["id"])
            with_rate = _rate(recs)
            # A skill only a person can start has no trigger rate: the run starts it.
            trig = None if s.get("user_invoked") else sum(r.get("skill_triggered", False) for r in recs) / len(recs)
            passes = sum(r["passed"] for r in recs)
            notes = []
            p_value = None
            if not base or base["n"] < MIN_VALID or len(recs) < MIN_VALID:
                verdict, delta = FLAGGED, None
                notes.append("too few valid runs")
            else:
                delta = with_rate - base["rate"]
                p_value = fisher_p(passes, len(recs), base["passes"], base["n"])
                significant = p_value <= alpha
                if significant and delta >= threshold:
                    verdict = HELPS
                elif significant and delta <= -threshold:
                    verdict = HURTS
                else:
                    verdict = NO_LIFT
                    if abs(delta) >= threshold:
                        notes.append(f"difference not significant (p={p_value:.2f})")
                    if min(len(recs), base["n"]) < SMALL_SAMPLE:
                        notes.append("small sample: only large effects detectable")
                if base["rate"] == 1.0 and with_rate == 1.0:
                    notes.append("ceiling: passes without the skill too")
                if trig is None:
                    notes.append(f"started by the user (/{s['name']}): lift only")
                if trig == 0:
                    notes.append("pack's skills never used" if s.get("pack") else "skill never triggered")
                    if verdict != NO_LIFT:
                        # A change without the skill ever loading is noise, not lift.
                        notes.append("difference is noise")
                        verdict = FLAGGED
            pairs.append({
                "skill": s["id"], "task": t["id"], "n": len(recs),
                "with_rate": with_rate, "base_rate": base["rate"] if base else None,
                "delta": delta, "trigger_rate": trig, "p_value": p_value,
                "ci": wilson(passes, len(recs)), "base_ci": base["ci"] if base else None,
                "cost": _med(r.get("cost_usd") for r in recs),
                "base_cost": base["cost"] if base else None,
                "cost_per_pass": _cost_per_pass(recs),
                "base_cost_per_pass": base["cost_per_pass"] if base else None,
                "turns": _med(r.get("turns") for r in recs),
                "verdict": verdict, "notes": notes,
                "match": (matches.get(f"{s['id']}|{t['id']}") or {}).get("reason"),
            })

    per_skill = []
    for s in skills:
        sp = [p for p in pairs if p["skill"] == s["id"]]
        if not sp:
            continue
        vs = {p["verdict"] for p in sp}
        if HELPS in vs and HURTS in vs:
            verdict = MIXED
        elif HELPS in vs:
            verdict = HELPS
        elif HURTS in vs:
            verdict = HURTS
        elif vs == {FLAGGED}:
            verdict = FLAGGED
        else:
            verdict = NO_LIFT
        trigs = [p["trigger_rate"] for p in sp if p["trigger_rate"] is not None]
        per_skill.append({**s, "verdict": verdict, "tasks": [p["task"] for p in sp],
                          "trigger_rate": sum(trigs) / len(trigs) if trigs else None})

    return {
        "runs": len(records), "errors": errors,
        "cost_usd": round(sum(r.get("cost_usd") or 0 for r in records), 4),
        "threshold": threshold, "alpha": alpha,
        "baseline": baseline, "pairs": pairs, "skills": per_skill,
        "gaps": find_gaps(per_skill, pairs, baseline, skills, tasks, untested),
    }


def _words(text: str) -> set:
    return {w for w in re.findall(r"[a-z]{4,}", text.lower())}


def find_gaps(per_skill, pairs, baseline, skills, tasks, untested) -> Dict[str, list]:
    gaps: Dict[str, list] = {}

    gaps["costly_no_lift"] = sorted(
        [s for s in per_skill if s["verdict"] == NO_LIFT
         and (s["upfront_tokens"] >= COSTLY_UPFRONT or s["onuse_tokens"] >= COSTLY_ONUSE)],
        key=lambda s: -(s["upfront_tokens"] * 20 + s["onuse_tokens"]))
    gaps["never_triggered"] = [s for s in per_skill if s["trigger_rate"] == 0]
    gaps["hurts"] = [s for s in per_skill if s["verdict"] in (HURTS, MIXED)]
    gaps["ceiling_tasks"] = [t for t, b in baseline.items() if b["rate"] == 1.0]
    helped = {p["task"] for p in pairs if p["verdict"] == HELPS}
    gaps["unsolved_tasks"] = [
        t for t, b in baseline.items()
        if b["rate"] == 0.0 and t not in helped
        and not any(p["task"] == t and p["with_rate"] > 0 for p in pairs)]
    by_id = {s["id"]: s for s in skills}
    untested_skills = [by_id[i] for i in untested if i in by_id]
    gaps["needs_person"] = [s for s in untested_skills if needs_person(s)]
    gaps["untested_claims"] = [s for s in untested_skills if not needs_person(s)]

    lookalikes = []
    for i, a in enumerate(skills):
        wa = _words(a["description"])
        for b in skills[i + 1:]:
            if a["source"] == b["source"]:
                continue
            wb = _words(b["description"])
            if len(wa) >= 5 and len(wb) >= 5:
                sim = len(wa & wb) / len(wa | wb)
                if sim >= 0.5:
                    lookalikes.append({"a": a["id"], "b": b["id"], "similarity": round(sim, 2)})
    gaps["lookalikes"] = lookalikes
    return gaps
