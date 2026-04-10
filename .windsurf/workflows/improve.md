---
description: Improve the codebase
---

Analyze and improve the codebase quality.

1. Run all quality checks:

```fish
task test
task type-check
task lint
task markdownlint
```

2. Review failing features:

```fish
task jq:next-features
```
3. Pick one improvement to make
4. Follow TDD: write failing test first
5. Implement the fix
6. Verify all tests pass
7. Update feature JSON if applicable
8. Commit with conventional commit message
