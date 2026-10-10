"""Eval runner: scores a reviewer backend against evals/cases/*.json.

Backends:
  deterministic  current summarize path (no key, always runs)
  llm            core.llm reviewer with BYOK key (skips cleanly without key)
"""
import json
import sys
from pathlib import Path

CASES_DIR = Path(__file__).parent / "cases"


def load_cases() -> list[dict]:
    cases = []
    for path in sorted(CASES_DIR.glob("*.json")):
        cases.append((path.name, json.loads(path.read_text())))
    return cases


def score_output(case: dict, text: str) -> dict:
    lowered = text.lower()
    must = [k for k in case.get("must_mention", []) if k.lower() in lowered]
    missed = [k for k in case.get("must_mention", []) if k.lower() not in lowered]
    fps = [k for k in case.get("must_not_mention", []) if k.lower() in lowered]
    return {"hits": must, "missed": missed, "false_positives": fps}


def deterministic_reviewer(diff: str) -> str:
    """Adapter: current product behavior summarized as text for scoring."""
    lines = diff.splitlines()
    added = [line for line in lines if line.startswith("+") and not line.startswith("+++")]
    return (
        f"firstpass deterministic summary: {len(added)} added line(s). "
        "No semantic findings (no LLM configured)."
    )


def run(backend: str = "deterministic") -> int:
    if backend == "llm":
        from core.llm.review import review_diff

        def reviewer(diff: str) -> str:
            try:
                return review_diff(diff)
            except RuntimeError as exc:  # e.g. no key configured
                print(f"LLM backend skipped: {exc}")
                return ""
    else:
        reviewer = deterministic_reviewer

    cases = load_cases()
    if not cases:
        print("no cases found")
        return 1
    total_hits = total_missed = total_fp = trap_fps = traps = 0
    for name, case in cases:
        text = reviewer(case["diff"])
        if backend == "llm" and not text:
            return 0  # skipped cleanly, don't score
        s = score_output(case, text)
        total_hits += len(s["hits"])
        total_missed += len(s["missed"])
        total_fp += len(s["false_positives"])
        if case.get("category") == "noise-trap":
            traps += 1
            trap_fps += 1 if s["false_positives"] else 0
        flag = "FP!" if s["false_positives"] else ("MISS" if s["missed"] else "ok")
        print(f"[{flag}] {name}: hits={s['hits']} missed={s['missed']} fp={s['false_positives']}")
    must_total = total_hits + total_missed
    print(f"\ncases={len(cases)} hit_rate={total_hits}/{must_total} false_positives={total_fp}")
    if traps:
        print(f"noise-traps flagged: {trap_fps}/{traps} (lower is better)")
    return 0


if __name__ == "__main__":
    backend = sys.argv[sys.argv.index("--backend") + 1] if "--backend" in sys.argv else "deterministic"
    raise SystemExit(run(backend))
