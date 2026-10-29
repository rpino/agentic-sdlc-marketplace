# Agentic SDLC dashboard (read-only)

A local web page for following Agentic SDLC projects: where each feature is in its lane, what is waiting for approval, open decisions, the AC to task to test traceability matrix, artifacts and recent activity. It covers roadmap step 6a. Approving gates and answering decisions from the page is a later step (6b), so for now **approvals still happen in Claude Code** with `/sdlc-core:approve <phase>`.

Stack: Next.js (App Router) with TypeScript and Tailwind CSS.

## Run it

You need Node 22.18 or newer and Python 3.9 or newer.

```
cd ui
npm install
npm run dev          # http://127.0.0.1:4310
```

Open the page, paste the folder of a project that has a `.sdlc/` directory (made by `/sdlc-core:init` or `/sdlc-core:adopt`) and press Add. To try it without a real project, make a demo one:

```
python dev/make_demo_project.py ../../demo-project
```

## How it works

- **The state script stays the source of truth.** The page runs `sdlc_state.py status|next|trace|verify --json` in the project folder, so the logic for phases, lanes, stale approvals and traceability lives in one place. The UI keeps no copy of project state.
- **It never changes a project.** The only fixed commands it runs are the four read-only ones above. Its own list of registered folders is stored in `~/.agentic-sdlc-ui/projects.json`.
- **The artifact viewer is restricted.** It shows only Markdown files that are inside a registered project after following symlinks, and never anything under `.sdlc`, `.git` or `node_modules`.
- **It listens on `127.0.0.1` only**, port 4310. Don't expose it to a network: it has no login, and it can read every registered project.

## Settings

| Variable | Default | Meaning |
|---|---|---|
| `SDLC_STATE_SCRIPT` | `../plugins/sdlc-core/scripts/sdlc_state.py` | Path to the state script |
| `SDLC_PYTHON` | `python` (Windows) or `python3` | Python executable |
| `SDLC_UI_DATA` | `~/.agentic-sdlc-ui/projects.json` | Where the list of projects is stored |

## Checks

```
npm run typecheck
npm test
npm run build
```
