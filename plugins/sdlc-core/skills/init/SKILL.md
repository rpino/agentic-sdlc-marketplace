---
name: init
description: Start a new Agentic SDLC project — creates the .sdlc/state.json state file, the docs/ phase folders and a project CLAUDE.md, then kicks off the first phase. Also adds a new feature to an existing project.
argument-hint: "\"<Project Name>\" [approver name] [--type feature|bugfix|hotfix|spike|chore]"
disable-model-invocation: true
---

# Initialize an Agentic SDLC project

Arguments: `$ARGUMENTS`

`SDLC` means `sh "${CLAUDE_PLUGIN_ROOT}/scripts/run_py.sh" "${CLAUDE_PLUGIN_ROOT}/scripts/sdlc_state.py"`.

1. Work out:
   - the **name** (first quoted argument);
   - the **approver**, meaning the human Product Owner. Use the second argument if given, otherwise ask the user for their name. Ask once, if needed, whether a different person is Tech Lead or QA Lead. If unknown, use the same approver.
   - the **work type**, which decides the phases (show `SDLC lanes` if the user is unsure). The default is `feature`, which runs all 10 phases. A production emergency is `hotfix`, a defect is `bugfix`, an investigation is `spike`, and maintenance is `chore`.

2. Decide the **project directory**: the current working directory, unless the user named another folder.
   - If it already contains `.sdlc/state.json`, this is **new work in an existing project**. Run `SDLC feature new "<Name>" --type <type>` instead. That feature gets its own docs under `docs/features/<slug>/` and becomes the active one.

3. Otherwise run:
   ```
   SDLC init "<Project Name>" --approver "<Name>" [--tech-lead "<Name>"] [--qa-lead "<Name>"] [--type <type>] [--dir "<path>"]
   ```

4. If the project keeps code outside the standard folders (`src/ app/ lib/ services/ packages/ api/ web/ tests/ test/`), gate it with `SDLC settings add-code-path <folder>/`.

5. Show the user what was created (state file, phase folders, `CLAUDE.md`) in two or three lines.

6. **Kick off the first phase immediately:** follow the `sdlc-core:conductor` skill.
