# Persistent team bootstrap RED evidence

- Command: focused Python 3.11 bootstrap contract suite.
- Result: 10 deterministic failures.
- Bounded cause: the required bootstrap executable was absent before implementation.
- Redaction: no prompts, responses, repository secrets, or temporary paths are retained here.

## Unsafe baseline checks

- Model switch without a complete safe handoff: refused by the planned transition contract.
- Forced collision overwrite: refused; no force option exists.
- Parallel writer owners: refused by the fixed one-writer policy.
- Pulse manufacturing work: refused; pulse is read-only and optional.

## GREEN result

- Focused contract after implementation: 12 tests passed.

## Pre-apply dry run

- Mode: `new`; apply: false; conflicts: 0; errors: 0; planned managed paths: 23.
- The JSON output contained repository-relative paths only and was inspected before apply.

## Applied verification

- First apply: 23 managed paths created; conflicts: 0; errors: 0.
- Validator: conforming with 23 unchanged managed paths.
- Repeated apply: 0 created; 23 unchanged; conflicts: 0; errors: 0.
- Read-only routing pilot: no work created. Optional pulse returned exactly its five empty fields.

## Adversarial RED follow-up

- Focused contracts exposed missing parsed sandbox fields, adoption marker insertion, and
  transactional publication behaviour.
- A regular-file ancestor produced a traceback before implementation hardening; this record keeps
  only the failure category and no temporary paths or raw process output.

## Adversarial GREEN follow-up

- Hardened focused contracts now cover parsed TOML sandbox modes, marker adoption, injected
  publication rollback, regular-file ancestors, reversed markers, invalid UTF-8, and the
  active-to-zero-to-acknowledged-active handoff boundary.
- Final focused contract result: 17 tests passed.

## Second adversarial follow-up

- RED contracts exposed overly broad transition overwrites, invalid Bucky ownership repair, and
  the backup-to-install rollback gap.
- GREEN contracts now pass with a transition-artifact whitelist, strict persisted policy checks,
  and registered backups before replacement. Final focused contract result: 20 tests passed.
- The existing generated state migrated through the required zero-writer boundary before the
  acknowledged Nightingale state was restored.

## Catalog and publication hardening

- RED: catalog provenance, exact boolean routing, optional recognition, safe scalar rendering,
  legacy-state migration, and generated-pulse transition contracts exposed the missing boundaries.
- GREEN: 29 focused Python 3.11 contracts pass in both the source and installed packages.
- The installed state moved active one writer to zero, then back to acknowledged active one;
  the selected and requested pair is the advertised `gpt-5.6-terra` at `xhigh`.
- The catalog is a closed `active-runtime:model/list` snapshot using the advertised
  `gpt-5.6-sol` and `gpt-5.6-terra` families and their advertised efforts. Luna is recorded
  only as not advertised in this runtime, never as globally unavailable.
- Validation, a repeated apply, the read-only routing dry run, and the optional pulse dry run
  completed without manufacturing work. This report retains no raw output, prompts, responses,
  secrets, or temporary paths.

## Descriptor-relative publication hardening

- RED: four final contracts reproduced an intermediate-ancestor symlink swap, failed rollback
  restoration, boolean and incomplete legacy state, and DEL or malformed rendered persona input.
- GREEN: 33 focused Python 3.11 contracts pass in both packages. Publication now holds one
  no-follow repository descriptor, walks each destination one component at a time, and uses
  basename-only renames for installation and rollback.
- A rollback restoration failure is reported and retains the byte-identical recovery copy inside
  the isolated repository. The control-character and persona checks run before dry-run success.

## Repository-root descriptor hardening

- RED: a run-level fixture swapped an intermediate absolute repository-path ancestor immediately
  before root descriptor acquisition. The original pathname-based reopen could then redirect work.
- GREEN: the runner now opens filesystem root and every absolute repository component with
  no-follow directory descriptors before validation. Inspection, state reads, and publication use
  that one retained repository descriptor; no later repository-path reopen occurs.
- The new adversarial fixture preserves the original tree, produces exit 1 JSON, and makes no
  outside write. The full focused suite now has 34 passing contracts.

## Post-publication review follow-up

- RED: malformed catalog values, dot and traversal config paths, wrapper cwd drift, descriptor
  cleanup, managed-block overwrite, incomplete zero state, and ungated fault switches exposed
  contract gaps.
- GREEN: malformed input now returns JSON exit 1 without a traceback; the validator resolves a
  relative config within its repo; and target-open failures close the already-open source fd.
- Managed AGENTS content remains no-overwrite even at a safe handoff. Strict state validation is
  the only adoption authority. Fault switches require explicit test mode. The focused suite now
  has 41 passing contracts, with no raw outputs or temporary paths retained.
