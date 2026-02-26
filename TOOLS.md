# TOOLS.md - Local Notes

## Git & GitHub

- **GitHub user:** hal-urbana
- **Auth:** `gh` CLI authenticated via PAT (full repo + workflow scopes)
- **Git protocol:** HTTPS (configured by gh)
- **Default branch naming:** main (check per-repo)

### Common workflows

```bash
# Clone a repo
git clone https://github.com/hal-urbana/REPO.git

# Check auth
gh auth status

# List repos
gh repo list hal-urbana

# Create a PR
gh pr create --title "Title" --body "Description" --base main

# Check CI on a PR
gh pr checks PR_NUMBER

# Create an issue
gh issue create --title "Title" --body "Description"
```

### Notes

- Always check existing issues/PRs before starting work (`gh issue list`, `gh pr list`)
- Use feature branches, not direct commits to main unless trivial
- PR descriptions should include: what changed, why, how to test
- Reference issue numbers in PR bodies with `Closes #N` when applicable

## Development Environment

- **OS:** Linux (Ubuntu 24.x)
- **Shell:** bash/zsh
- **Node:** available via linuxbrew
- **Package manager:** linuxbrew (`brew`)

---

_Update this as you learn more about Hal's specific projects and tools._
