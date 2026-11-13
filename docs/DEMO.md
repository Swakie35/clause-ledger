# Reproducible local walkthrough

This walkthrough does not require production data or cloud deployment. Run the commands at this repository root.

## Prerequisites

Python 3.11+; make a virtual environment and install the project test extra.

## Setup and test

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[test]"
python -m pytest -q
```

## Demonstrate the main path

```bash
python -m clauseledger.evaluation
```

## What to look for

- Observe the console or generated report; **do not substitute copied/synthetic screenshots for actual runtime output**.
- For algorithms, inspect tests around boundary conditions and compare behavior with the README.
- For Java demos, the test runner exercises the HTTP service or core worker behavior; the README includes manual server commands.
- Open `docs/ARCHITECTURE.md` to explain design trade-offs and limits.

## Interpretation

No access control or tenant isolation. Index construction is performed per query. Clause signals are pattern flags, not legal determinations; do not upload private agreements.

If a command fails, capture the exact error and runtime version rather than claiming the repository is verified.
