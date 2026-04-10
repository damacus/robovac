---
description: Address PR comments
auto_execution_mode: 0
---

1. Check out the PR branch: `gh pr checkout [id]` if not checked out already

2. 
   a) If I have given ypu screenshots ingest those and use them to inform your changes

    b) If i have not given you screenshots, get comments on pull request using the following command

    ```bash
    gh api --paginate repos/[owner]/[repo]/pulls/[id]/comments | jq '.[] | {user: .user.login, body, path, line, original_line, created_at, in_reply_to_id, pull_request_review_id, commit_id}'
    ```

3. For EACH comment, do the following. Remember to address one comment at a time.
 a. Print out the following: "(index). From [user] on [file]:[lines] — [body]"
 b. Analyze the file and the line range.
 c. If you don't understand the comment, do not make a change. Just ask me for clarification, or to implement it myself.
 d. If you think you can make the change, make the change BEFORE moving onto the next comment.

4. After all comments are processed, summarize what you did, and which comments need the USER's attention.
