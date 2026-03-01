# MEMORY.md - Long-Term Memory

> Load this only in main sessions (direct chat with Hal). Not for group chats or shared contexts.

---

## Who I Am

I'm Hal's AI assistant running via OpenClaw on a Linux workstation. My job is to be genuinely useful — proactive, capable, and trustworthy. I communicate primarily through Slack (#all-usmlabs) and direct webchat sessions.

---

## Hal

- **Name:** Hal
- **Email:** hal@usmlabs.com
- **GitHub:** hal-urbana
- **Org:** USM Labs (usmlabs.com)
- **Role:** Software developer
- **Style:** Prefers getting things done over lengthy back-and-forth. Concise is better.
- **Primary channel:** Slack (#all-usmlabs)
- **Key contact:** David Trepp — david.trepp@usmlabs.com (colleague at USM Labs)

---

## My Setup

### Models
- **Primary:** GLM 4.7 Flash (local) — `ollama/glm-4.7-flash:latest` via `http://192.168.20.105:11434`
- **Reasoning/Vision:** Kimi K2.5 (cloud-routed) — `ollama-remote/kimi-k2.5:cloud` via `http://192.168.10.242:11434` — supports thinking, tools, vision
- **Fallback:** anthropic/claude-haiku-4-5 (configured but secondary)

### Channels
- **Slack:** Connected via Socket Mode. Bot active in #C0AF85E3ARK. `requireMention: false` — responds without needing to be @mentioned.

### Tools Available
- **Web search:** BraveSearch (enabled)
- **Web fetch:** Enabled
- **Gmail:** `gog` CLI v0.11.0 — authenticated as hal@usmlabs.com (OAuth, `~/.config/gogcli/`)
- **Skills:** 54 skills available under `/home/linuxbrew/.linuxbrew/lib/node_modules/openclaw/skills/`

---

## Gmail Integration

Set up 2026-02-27 using `gog` (Google Workspace CLI).

- **Account:** hal@usmlabs.com
- **Auth type:** OAuth2 (Desktop app)
- **Credentials stored:** `~/.config/gogcli/credentials.json`
- **Services authorized:** gmail
- **Google project:** gen-lang-client-0750923599

### Key commands
```bash
# Search inbox
gog gmail search 'in:inbox newer_than:3d' --max 10 --account hal@usmlabs.com

# Send email
gog gmail send --to recipient@example.com --subject "Subject" --body "Body" --account hal@usmlabs.com

# Search individual messages (not threads)
gog gmail messages search "in:inbox from:someone@example.com" --max 10 --account hal@usmlabs.com

# Read a specific message
gog gmail get <messageId> --account hal@usmlabs.com --json

# Reply
gog gmail send --to addr --subject "Re: X" --body "Reply" --reply-to-message-id <msgId> --account hal@usmlabs.com
```

Set `GOG_ACCOUNT=hal@usmlabs.com` to skip `--account` flag.

**Important:** Always confirm before sending email (per AGENTS.md).

---

## GitLab (Internal — Primary Git Host)

Switched from GitHub to internal GitLab on 2026-02-27.

- **Server:** http://192.168.10.42 (HTTP only, no TLS) — also responds as `gitlab.sightweaver.com`
- **User:** hal (user ID 2, hal@usmlabs.com) — separate from `root` admin account
- **CLI:** `glab` (installed via brew, default host set to 192.168.10.42)
- **Git credentials:** stored via `git credential store` for `http://192.168.10.42`
- **PAT:** stored in `~/.config/glab-cli/config.yml`, expires 2027-02-27
- **Key difference:** GitLab uses Merge Requests (MRs), not Pull Requests

---

## Projects

### Snake Game
- **Repo:** https://github.com/hal-urbana/snake
- **Location:** `workspace/snake/snake.py`
- **Stack:** Python, pygame
- **Status:** Complete and pushed to GitHub

### ArcGIS Knowledge Integration
- **Repo:** https://github.com/hal-urbana/arcgis-knowledge-integration
- **Location:** `workspace/arcgis-knowledge-integration/`
- **Stack:** Python (ArcGIS Knowledge API client, OAuth)
- **Status:** Code complete, awaiting ArcGIS Knowledge Server for testing
- **Notes:** Production-ready client with error handling. Needs ArcGIS Enterprise env vars to test.

---

## System Notes

- OpenClaw config: `~/.openclaw/openclaw.json`
- Gateway runs on port 18789 (loopback only)
- Slack credentials (botToken, appToken, userToken) are in `openclaw.json`
- `trash` preferred over `rm` for deletions

---

## Lessons Learned

- When reading email bodies via `gog gmail get --json`, body content is in `payload.parts[].body.data` (base64 encoded). An empty reply shows as `DQo=` (just `\r\n`).
- `gog gmail messages search` returns individual messages; `gog gmail search` returns one row per thread. Use `messages search` when you need to see each email separately.
- `gog gmail get <id>` needs the message ID, not the thread ID.

---

_Last updated: 2026-02-27_
