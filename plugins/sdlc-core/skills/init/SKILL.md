---
name: init
description: Start a new Agentic SDLC project — creates the .sdlc/state.json state file, the docs/ phase folders and a project CLAUDE.md, then kicks off Discovery.
argument-hint: "\"<Project Name>\" [approver name]"
disable-model-invocation: true
---

# Initialize an Agentic SDLC project

Arguments: `$ARGUMENTS`

1. Work out the **project name** (first quoted argument) and the **approver** (the human Product Owner — use the second argument if given, otherwise ask the user for their name). Ask once, if needed, whether a different person is Tech Lead or QA Lead; if unknown, use the same approver.

2. Decide the **project directory**: the current working directory, unless the user named another folder. If the directory already contains `.sdlc/state.json`, stop and show `/sdlc-core:status` instead.

3. Run:
   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sdlc_state.py" init "<Project Name>" --approver "<Name>" [--tech-lead "<Name>"] [--qa-lead "<Name>"] [--dir "<path>"]
   ```

4. Show the user what was created (state file, `docs/01-…10-` folders, `CLAUDE.md`) in two or three lines.

5. **Kick off Discovery immediately:** follow the `sdlc-core:conductor` skill. It will run `sdlc-discovery:idea-interviewer`, which starts by interviewing the user about the idea.
