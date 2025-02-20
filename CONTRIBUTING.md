# Contributing

Thanks for contributing to SomaOS Governance Gateway.

## Development setup

```bash
cd /path/to/soma-governance-gateway
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running checks

```bash
pytest -q
make check
```

## Pull request expectations

- Keep changes scoped and reviewable.
- Add or update tests for behavior changes.
- Update docs (`README.md`, `docs/api.md`) if API behavior changes.
- Use clear commit messages focused on intent.

## API contract guidance

The core endpoints under `/v1/*` are public-facing. Avoid breaking response fields without documenting migration notes.

## Code style

- Prefer clear, deterministic policy logic.
- Keep side effects explicit in approval/audit flows.
- Maintain meaningful event payloads (`event_type`, `ts`, reason/context).
