## Agent skills

### Issue tracker

Issues are tracked in GitHub Issues for davitrek/Oracle-of-Music, using the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Uses the five default triage labels: needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.

## Spotify Web API

Spotify's batch endpoints ("Get Several Artists", "Get Several Tracks", etc.) are deprecated. Fetch one item per request.
