# Commit Code Command

Commit all staged and unstaged changes to git and push to the remote repository.

## Instructions

1. Run `git status` to see all modified, deleted, and untracked files
2. Run `git diff --stat` to understand the scope of changes
3. Run `git log --oneline -3` to see recent commit message style
4. Analyze the changes and draft a concise commit message that:
   - Starts with a verb (Fix, Add, Update, Remove, Refactor, etc.)
   - Summarizes the main change in the first line (50 chars max)
   - Includes bullet points for multiple changes in the body
   - Does NOT include "Generated with Claude Code" or "Co-Authored-By" footers
5. Stage all changes with `git add -A`
6. Commit with the drafted message using a HEREDOC format
7. Push to remote (use `--set-upstream origin <branch>` if needed)
8. Report the commit hash and confirmation of push

## Commit Message Format

```
<type>: <short summary>

- Detail 1
- Detail 2
```

Types: Fix, Add, Update, Remove, Refactor, Docs, Test, Chore