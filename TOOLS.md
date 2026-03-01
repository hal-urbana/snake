# TOOLS.md - Local Notes

## Git & GitLab (Primary)

- **GitLab server:** http://192.168.10.42 (internal network — `gitlab.sightweaver.com`)
- **GitLab user:** hal (hal@usmlabs.com, user ID 2)
- **Auth:** `glab` CLI authenticated with PAT (`~/.config/glab-cli/config.yml`)
- **Git protocol:** HTTP (internal server, no TLS)
- **PAT scopes:** api, read_user, read_repository, write_repository
- **PAT expires:** 2027-02-27
- **Default branch naming:** main (check per-repo)

### Common workflows

```bash
# Clone a repo
git clone http://192.168.10.42/hal/REPO.git

# Check auth
glab auth status

# List repos
glab repo list

# Create a MR (merge request)
glab mr create --title "Title" --description "Description" --target-branch main

# Check CI on a MR
glab ci status

# Create an issue
glab issue create --title "Title" --description "Description"

# View issues
glab issue list

# Direct API calls
glab api /user
glab api /projects
```

### Notes

- GitLab uses **Merge Requests** (MRs), not Pull Requests
- Always check existing issues/MRs before starting work (`glab issue list`, `glab mr list`)
- Use feature branches, not direct commits to main unless trivial
- MR descriptions should include: what changed, why, how to test
- Reference issue numbers in MR bodies with `Closes #N` when applicable
- Server is HTTP only (no HTTPS) — git remotes must use `http://` not `https://`

## Git & GitHub (Legacy — repos still exist)

- **GitHub user:** hal-urbana
- **Auth:** `gh` CLI authenticated
- **Existing repos:** snake (https://github.com/hal-urbana/snake), arcgis-knowledge-integration
- **Status:** Superseded by internal GitLab for new work

## Development Environment

- **OS:** Linux (Ubuntu 24.x)
- **Shell:** bash/zsh
- **Node:** available via linuxbrew
- **Package manager:** linuxbrew (`brew`)

---

_Update this as you learn more about Hal's specific projects and tools._
