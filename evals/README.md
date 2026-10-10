# evals — Review quality harness

> Per the M5 correction: noise (not cost) is the risk. This harness measures it.

## How to run (no key needed for baseline)

```bash
python evals/run.py                # deterministic baseline only
python evals/run.py --backend llm  # needs BYOK key, see core/llm README
```

## Scores that matter

- **hit rate**: fraction of cases where the review mentions every `must_mention` keyword.
- **false-positive rate**: fraction of noise-trap cases where the review mentions something from `must_not_mention`.
- A bot that scores high hits but also high false-positives gets muted. Both numbers are reported.

## Adding cases (target: 20-30 from real PRs)

One JSON file per case in `evals/cases/`. Shape:

```json
{
  "id": "sql-injection-fstring",
  "title": "SQL built with f-string",
  "category": "bug",
  "diff": "--- a/db.py\n+++ b/db.py\n...",
  "must_mention": ["inject", "param"],
  "must_not_mention": [],
  "notes": "Why this matters..."
}
```

Categories: `bug` | `security` | `perf` | `noise-trap` (must_not_mention required).
Keywords are matched case-insensitively as substrings — keep them short and
distinctive, not full sentences.
