---
description: Review PR
---

Review a pull request for code quality and correctness.

1. Get PR details using `mcp5_pull_request_read` with method `get`
2. Get the diff using `mcp5_pull_request_read` with method `get_diff`
3. Review for:
   - Code correctness
   - Test coverage
   - Type hints
   - Following existing patterns
   - Conventional commit messages
4. Add review comments if needed using `mcp5_add_comment_to_pending_review`
5. Submit review using `mcp5_pull_request_review_write`
