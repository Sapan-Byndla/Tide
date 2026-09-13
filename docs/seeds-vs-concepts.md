# Curated Seeds vs. Discovered Concepts

This is a **fundamental TIDE architectural rule**. The curated seed list is a
*beachhead*, not TIDE's permanent vocabulary and not a hard allow-list.

## Three distinct layers

| Layer | Where it lives | Who writes it | Mutable by discovery? |
| --- | --- | --- | --- |
| **Curated configuration** | `seed_list.yaml` (version-controlled) | Humans | ❌ Never auto-edited |
| **Runtime seed representation** | `sources`, `seeds` tables | The seed importer | ❌ Only from the file |
| **Expanding knowledge** | `concepts`, `entities`, `graph_edges`, … | Future processing / the AI Crawler | ✅ Grows freely |

* `seed_list.yaml` is **curated configuration**.
* The database `seeds`/`sources` tables are the **runtime representation** of that
  configuration.
* The `concepts`/`entities` graph is an **expanding knowledge representation**.

## Why two separate tables (`seeds` vs `concepts`)

The schema deliberately does **not** collapse curated seeds and discovered
concepts into one table:

* A seed `"AI Agents"` may lead to discovered concepts like `"agentic memory"`,
  `"computer use"`, `"agent interoperability"` — none of which are in the seed
  list. These are rows in `concepts` with `origin='discovered'` and
  `seed_id = NULL`.
* When a concept *did* originate from a curated seed, `concepts.seed_id` records
  that provenance — a link, not a merge.

```
seed_list.yaml ──import──▶ seeds ──(provenance, optional)──▶ concepts ◀── discovered
   (curated)              (runtime)         concepts.seed_id            (origin='discovered',
                                                                          seed_id=NULL)
```

## Rules the code enforces

1. **The importer writes only `sources`/`seeds`.** It never creates or edits
   `concepts`/`entities`. (See `backend/seeds/importer.py`.)
2. **Discovery never rewrites `seed_list.yaml`.** Discovered concepts live in the
   database only. There is no code path from the graph back to the file.
3. **Removing a seed is non-destructive.** A seed dropped from the file is
   *deactivated* (`enabled=False`, `config.removed_from_seed_list=true`), never
   deleted — and `concepts.seed_id` uses `ON DELETE SET NULL`, so graph knowledge
   is never cascaded away.
4. **Stable identity.** Seeds are keyed by a deterministic `key`/`uuid5`
   (`backend/seeds/identity.py`), so re-import updates the same rows.

## Out of scope for Phase 1

A **controlled concept-to-seed promotion** workflow (TIDE recommending discovered
concepts for direct monitoring) is intentionally **not** implemented. The schema
anticipates it: `SeedOrigin.PROMOTED` exists as a future origin value, but nothing
performs promotion yet.
