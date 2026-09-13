# Agent Memory (Data Foundation)

TIDE's future AI Crawler / Trend Analyst has **persistent memory in the database**
— never inside the LLM. This phase creates the tables; the reasoning loop that
fills them is a later phase.

Memory is **structured, not a single transcript**. Each concern is its own table
so it can be queried, evaluated, and traced back to evidence.

## Tables

| Table | Meaning | Key fields |
| --- | --- | --- |
| `agent_runs` | One execution/session of the analyst | `status` (checked), `trigger`, `started_at`, `finished_at`, `config`, `stats` |
| `agent_observations` | Something determined from inspecting graph/data | `run_id`, `observation_type`, `subject_type`/`subject_id`, `summary`, `confidence`, `data` |
| `agent_hypotheses` | An explicit belief explaining a pattern | `run_id`, `statement`, `status`, `confidence`, `supporting_evidence`, `contradicting_evidence` |
| `agent_predictions` | A future claim that can be evaluated later | `run_id`, `hypothesis_id?`, `statement`, `confidence`, `evaluation_at`, `status` (checked), `actual_outcome`, `resolved_at`, `evaluation_metadata` |
| `agent_reports` | A persisted intelligence output | `run_id`, `title`, `summary`, `body`, `concept_ids`, `prediction_ids`, `generated_at` |

Everything hangs off `agent_runs` via `run_id` (FK, `ON DELETE CASCADE`), so a run
and its memory form one traceable unit.

## Prediction evaluation

Predictions are built to eventually measure **whether TIDE's analyst is actually
correct**. Each carries the full evaluation lifecycle:

```
created_at ──▶ evaluation_at ──▶ resolved_at
statement                          status:  pending → correct | incorrect | partial | unresolved
confidence                         actual_outcome + evaluation_metadata
```

`status` is CHECK-constrained to the closed outcome set; `evaluation_at` and
`status` are indexed so a future evaluator can efficiently find predictions that
are due.

## How this maps to the five conceptual memory classes

The [Phase 0 AI-Crawler lifecycle](agent-lifecycle.md) named five memory classes.
They map onto these tables plus the knowledge graph:

| Conceptual class | Backed by |
| --- | --- |
| episodic | `agent_runs` + `agent_observations` |
| semantic | `concepts`, `entities`, `graph_edges`, `embeddings` |
| hypothesis | `agent_hypotheses` |
| predictive | `agent_predictions` |
| report | `agent_reports` |

The LLM remains a stateless reasoning engine (`contracts.LLMProvider`); durable
state always lives here.
