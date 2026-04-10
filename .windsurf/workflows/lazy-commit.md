---
description: Lazy Commit
---

Create a commit with a conventional commit message based on the staged changes.

1. Check staged changes: `git diff --staged`
2. Generate a conventional commit message based on the changes
3. Commit with the generated message

Conventional commit format:

- `feat:` - New feature
- `fix:` - Bug fix
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `docs:` - Documentation changes
- `chore:` - Maintenance tasks
- `style:` - Code style changes (formatting, etc.)

Example: `git commit -m "feat: add T2320 vacuum model support"`
