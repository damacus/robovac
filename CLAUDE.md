# CLAUDE.md — AI Assistant Guide for robovac

This file provides context for AI assistants (Claude, Copilot, etc.) working in this codebase.

## Project Overview

**robovac** is a Home Assistant custom component that integrates Eufy RoboVac vacuum cleaners via the Tuya Local API. It supports 40+ models with encrypted local communication (protocol v3.3 and v3.4/v3.5) and optional cloud API fallback.

- **Language**: Python 3.13+
- **Framework**: Home Assistant custom component
- **License**: Apache-2.0
- **Current version**: 2.3.0-beta.1
- **Repo**: `damacus/robovac`

---

## Repository Structure

```
custom_components/robovac/   # Main integration source
├── vacuums/                 # Per-model command definitions (40+ models)
│   ├── base.py              # Shared enums, types, Protocol definition
│   └── T2251.py, T2080.py… # One file per model
├── __init__.py              # Integration setup and discovery
├── robovac.py               # RoboVac class — device interface and command dispatch
├── vacuum.py                # StateVacuumEntity (Home Assistant entity)
├── sensor.py                # Battery/status sensor entities
├── config_flow.py           # Config UI and options flow
├── tuyalocalapi.py          # Tuya v3.3/v3.5 protocol: encryption, sockets, DPS
├── tuyawebapi.py            # Tuya cloud REST API client
├── tuyalocaldiscovery.py    # UDP broadcast device discovery
├── const.py                 # DOMAIN, CONF_VACS, REFRESH_RATE, PING_RATE, TIMEOUT
└── manifest.json            # Component metadata

tests/
└── test_vacuum/             # 50+ test files (~4600 lines)
    ├── test_t2251_command_mappings.py  # Per-model command tests
    ├── test_vacuum_entity.py
    ├── test_config_flow.py
    ├── test_options_flow.py
    ├── test_protocol_version.py
    └── …

docs/                        # Internal contributor documentation
site_docs/                   # User-facing documentation (published to GitHub Pages)
.github/workflows/           # CI/CD pipelines
Taskfile.yaml                # Task automation (uses `task` CLI)
pyproject.toml               # Build system, mypy, black, isort, pytest config
```

---

## Development Workflow

### Setup

```bash
task install-dev   # Create venv with uv and install dev dependencies
```

All Python tasks use [`uv`](https://github.com/astral-sh/uv) instead of pip.

### Running Checks

```bash
task test          # Run pytest with coverage
task type-check    # mypy type checking
task lint          # flake8 linting
task markdownlint  # Markdown lint (with auto-fix)
task all           # Run all of the above in sequence
```

Run tests for a specific file:

```bash
uv run pytest tests/test_vacuum/test_t2251_command_mappings.py -v
```

### Pre-commit Hooks

Hooks are managed by **lefthook** (configured in `lefthook.yml`). They run lint, test, and type-check in parallel on commit. Install with:

```bash
lefthook install
```

---

## Key Conventions

### Naming

| Item | Convention | Example |
|------|-----------|---------|
| Files | `snake_case.py` | `tuyalocalapi.py` |
| Classes | `PascalCase` | `RoboVac`, `T2251` |
| Functions/methods | `snake_case` | `async_setup_entry` |
| Constants | `UPPER_CASE` | `DOMAIN`, `REFRESH_RATE` |
| Private | `_leading_underscore` | `_LOGGER`, `_dps` |
| Logger | `logging.getLogger(__name__)` as `_LOGGER` | |

### Command Mapping Pattern

Each model file defines a `commands` dict mapping `RobovacCommand` enum values to DPS codes and value mappings:

```python
commands = {
    RobovacCommand.MODE: {
        "code": 5,
        "values": {
            "auto": "Auto",          # input (snake_case) → output (PascalCase)
            "small_room": "SmallRoom",
            "spot": "Spot",
        },
    },
}
```

- **Keys** are always lowercase/snake_case (what HA sends to the device)
- **Values** are PascalCase strings (what the Tuya protocol expects)
- Matching is **case-insensitive** — device responses are normalized before lookup
- Commands that are absent from a model's `commands` dict are not supported by that model

### Type Hints

Full type hints are required. mypy runs in strict mode with `disallow_untyped_defs = true`. Use `cast()` when narrowing types that mypy can't infer. Some legacy modules have per-module overrides in `pyproject.toml`.

### Async

Home Assistant integration methods are async. Use `async def` and `await` consistently. Do not call blocking I/O from coroutines — use `asyncio.get_event_loop().run_in_executor` if needed.

### Docstrings

Use Google-style docstrings for public methods:

```python
def my_method(self, arg: str) -> bool:
    """Short one-line summary.

    Args:
        arg: Description of arg.

    Returns:
        Description of return value.
    """
```

---

## Adding a New Vacuum Model

1. Create `custom_components/robovac/vacuums/T<model>.py`
2. Implement `RobovacModelDetails` Protocol (see `base.py`):
   - `ha_features`: `VacuumEntityFeature` flags
   - `robovac_features`: `RoboVacEntityFeature` flags
   - `commands`: dict of `RobovacCommand` → `{code, values}`
3. Register the model in `robovac.py` model lookup dict
4. Add tests in `tests/test_vacuum/test_t<model>_command_mappings.py`
5. Update supported models list in `README.md` / documentation

Reference `custom_components/robovac/vacuums/T2251.py` as the canonical example for a fully-featured model.

---

## Testing Conventions

- **100% coverage target** — all new code must be tested
- Tests use `pytest-asyncio` (asyncio_mode=auto — no need for `@pytest.mark.asyncio`)
- Mock hardware using `unittest.mock.patch` / `AsyncMock`
- Use `pytest-homeassistant-custom-component` for HA fixtures
- Command mapping tests verify both forward (HA → device) and reverse mappings
- Test file names mirror source: `vacuum.py` → `test_vacuum_entity.py`

---

## CI/CD Pipelines

| Workflow | Trigger | Jobs |
|----------|---------|------|
| `ci.yml` | Push / PR | HACS validation, hassfest, markdown lint, link check, flake8 lint, pytest |
| `release.yaml` | Merge to main | Semantic release, version bump in `manifest.json` + `pyproject.toml` |
| `docs.yml` | Push to main | Build and deploy documentation site |

**Commit messages must follow [Conventional Commits](https://www.conventionalcommits.org/)** — the release pipeline uses them to determine version bumps:

```
feat: add support for T9000 model
fix: handle missing DPS code gracefully
docs: update troubleshooting guide
chore: bump cryptography to 46.0.5
```

---

## Protocol Notes (Tuya Local API)

- **v3.3**: Symmetric AES encryption, UDP discovery, DPS-based commands
- **v3.4/v3.5**: HMAC-based session negotiation, device session key exchange
- `tuyalocalapi.py` handles all encryption, framing, and socket communication
- DPS codes are model-specific integer keys that map to device functions
- Device responses use PascalCase values that must be matched case-insensitively

Avoid modifying `tuyalocalapi.py` without understanding the full Tuya protocol spec — bugs here affect all models.

---

## Configuration & Tooling

| Tool | Config file | Purpose |
|------|------------|---------|
| black | `pyproject.toml` | Code formatting (88 char line length) |
| isort | `pyproject.toml` | Import sorting |
| flake8 | `.flake8` | Linting (max-line-length=180) |
| mypy | `pyproject.toml` | Static type checking |
| pytest | `pytest.ini` + `pyproject.toml` | Test runner + coverage |
| lefthook | `lefthook.yml` | Git hooks |
| pre-commit | `.pre-commit-config.yaml` | Additional pre-commit checks |
| renovate | `renovate.json` | Automated dependency updates |
| semantic-release | `.releaserc` | Automated versioning |
| task | `Taskfile.yaml` | Task automation runner |

---

## Security Considerations

- The integration uses encrypted local communication; never log encryption keys
- `tuyalocalapi.py` previously used `random` (weak RNG) — now uses `secrets`; maintain this
- `literal_eval` replaced `eval` for safe config parsing — do not revert
- Do not expose device local keys or tokens in logs, errors, or exceptions

---

## Useful Commands

```bash
# List all supported models
python -m custom_components.robovac.model_validator_cli --list

# Analyze DPS codes for a device
python analyze_model_dps.py

# Start Home Assistant (dev container)
task ha-start

# View Home Assistant logs
task ha-logs
```

---

## Getting Help

- Contributor docs: `DEVELOPMENT.md`
- Troubleshooting guide: `TROUBLESHOOTING.md`
- GitHub Issues: `damacus/robovac`
