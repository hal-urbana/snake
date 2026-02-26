# HEARTBEAT.md - Periodic Checks

On each heartbeat, rotate through these checks (don't repeat the same one back-to-back):

## GitHub (check 1-2x per day)

```bash
# Open PRs needing attention
gh pr list --author hal-urbana --state open

# Open issues assigned to Hal
gh issue list --assignee hal-urbana --state open
```

Notify in Slack if:
- A PR has failing checks
- A PR has new review comments
- An issue has been open >7 days without activity

## Active work

- Check if any in-progress branches have uncommitted changes
- If a task was started last session, check its current status

## When to stay quiet (HEARTBEAT_OK)

- Nothing new since last check
- Late night (23:00-08:00) unless urgent
- CI passing, no open review requests, no new issues

---

_Keep this concise. Token cost adds up._
