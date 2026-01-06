---
description: Create GitHub PR
---

Create a pull request for the current branch.

1. Ensure all changes are committed
2. Push the current branch: `git push -u origin HEAD`
3. Create PR using GitHub MCP tools:
   - Use `mcp5_create_pull_request`
   - Set base branch to `main`
   - Generate title from branch name or commits
   - Generate description from commit messages

PR title should follow conventional commits format when applicable.
