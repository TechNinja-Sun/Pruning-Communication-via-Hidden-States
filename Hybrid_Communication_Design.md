# Hybrid Communication Design (Dynamic + Core-Edge)

This document describes the newly added hybrid communication strategy in [PruneComm/system/exp.py](PruneComm/system/exp.py), including how dynamic switching and core-edge mixing are implemented.

## 1. Goal

The design combines two ideas:

1. Dynamic switching by disagreement level.
2. Core-edge structured mixing to keep exploration while controlling noise.

It preserves existing console output style and chart style.

## 2. Communication Modes

The workflow now supports these modes:

- `similar`
- `dissimilar`
- `random`
- `hybrid` (new)

Set via `COMM_MODE` in [model.env](model.env).

## 3. Dynamic Switching Rule (Hybrid)

Implemented by `decide_hybrid_strategy(...)`.

Inputs:

- First-round options from all agents.
- Ground-truth option (available in experiment mode).

Computed values:

- `consensus_option`: most frequent first-round option.
- `consensus_ratio`: frequency of `consensus_option` / number of agents.
- `correct_tendency`: whether consensus points to GT and exceeds `CORRECT_TENDENCY_TH`.

Decision rule:

- High-consensus sample -> `similar`
  - `consensus_ratio >= HIGH_CONSENSUS_TH`
- Medium-disagreement sample -> `mixed`
  - `MID_CONSENSUS_TH <= consensus_ratio < HIGH_CONSENSUS_TH`
- High-disagreement sample -> `dissimilar_then_similar`
  - `consensus_ratio < MID_CONSENSUS_TH`
- If there is clear correct tendency, prioritize `similar`.

Thresholds are configurable with env vars:

- `HIGH_CONSENSUS_TH` (default `0.75`)
- `MID_CONSENSUS_TH` (default `0.50`)
- `CORRECT_TENDENCY_TH` (default `0.50`)

## 4. Core-Edge Mixing

Implemented by:

- `update_agent_stability(...)`
- `split_core_edge_agents(...)`
- `build_ref_maps(..., strategy="mixed")`

How it works:

1. Each round updates first-round stability per agent (correct count / total count).
2. Agents are sorted by stability score.
3. Top portion (`CORE_RATIO`, default `0.60`) becomes core agents; others are edge agents.
4. In `mixed` strategy:
   - Core agents use `similar` links within the core.
   - Edge agents use `dissimilar` links toward the core.

This keeps robust correction in core while edge agents inject diverse hypotheses.

## 5. High-Disagreement Two-Step Reference

For `dissimilar_then_similar` strategy:

- `primary_ref_map`: dissimilar reference.
- `secondary_ref_map`: similar reference.

Second-round prompt contains both references:

- Primary reference for exploration.
- Secondary reference for convergence.

This approximates "explore first, then converge" without changing current two-round pipeline shape.

## 6. Runtime Trace and Logs

Per-round trace now includes:

- `graph` (primary references)
- `secondary_graph` (optional second references)
- `hybrid_strategy`:
  - `active_strategy`
  - `consensus_option`
  - `consensus_ratio`
  - `correct_tendency`
  - `vote`
  - `core_agents`
  - `edge_agents`

Console output keeps existing style and adds strategy lines in second-round info:

- `STRATEGY`
- `CONSENSUS`
- `CORE AGENTS` / `EDGE AGENTS` (when mixed)

## 7. What Was Intentionally Preserved

- Existing first-round / second-round output layout.
- Existing four metrics calculation and files.
- Existing ACC / Token / four-metric chart style.

So current plotting and reporting remain compatible with prior experiments.

## 8. Key Code Entry Points

Main implementation is in [PruneComm/system/exp.py](PruneComm/system/exp.py):

- `decide_hybrid_strategy(...)`
- `update_agent_stability(...)`
- `split_core_edge_agents(...)`
- `build_ref_maps(...)`
- `run(...)` integration section after first-round answers and similarity matrix.

## 9. Suggested Usage

Example `model.env` additions:

```dotenv
COMM_MODE="hybrid"
HIGH_CONSENSUS_TH=0.75
MID_CONSENSUS_TH=0.50
CORRECT_TENDENCY_TH=0.50
CORE_RATIO=0.60
```

Then run the same experiment entrypoint as before.
